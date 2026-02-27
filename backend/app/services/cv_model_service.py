from __future__ import annotations

import importlib.util
import math
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable

import cv2
import numpy as np

try:
    import onnxruntime as ort
except Exception:  # noqa: BLE001
    ort = None


PredictFn = Callable[[np.ndarray], float]


@dataclass
class CVInferenceResult:
    malicious_probability: float | None
    prediction: str | None
    model_source: str | None
    error: str | None = None


class QRCVModelService:
    """
    Loads a QR image CV model if available.

    Priority:
    1) Python adapter file at models/cv_adapter.py with function:
       predict_malicious_probability(image_bgr: np.ndarray) -> float
    2) ONNX model at models/qr_cv_model.onnx (requires onnxruntime)
    3) Disabled (returns None probabilities)
    """

    def __init__(
        self,
        adapter_path: str | Path = "models/cv_adapter.py",
        onnx_path: str | Path = "models/qr_cv_model.onnx",
    ) -> None:
        self.adapter_path = Path(adapter_path)
        self.onnx_path = Path(onnx_path)
        self._adapter_fn: PredictFn | None = None
        self._onnx_session = None
        self._onnx_input_name: str | None = None

        self._load_adapter()
        if self._adapter_fn is None:
            self._load_onnx()

    @property
    def active_model_source(self) -> str | None:
        if self._adapter_fn is not None:
            return "python_adapter"
        if self._onnx_session is not None:
            return "onnx"
        return None

    def predict_from_bytes(self, image_bytes: bytes) -> CVInferenceResult:
        raw = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if image is None:
            return CVInferenceResult(
                malicious_probability=None,
                prediction=None,
                model_source=self.active_model_source,
                error="Invalid image bytes.",
            )
        return self.predict_from_image(image)

    def predict_from_image(self, image_bgr: np.ndarray) -> CVInferenceResult:
        if self._adapter_fn is None and self._onnx_session is None:
            return CVInferenceResult(
                malicious_probability=None,
                prediction=None,
                model_source=None,
                error=None,
            )

        try:
            if self._adapter_fn is not None:
                prob = float(self._adapter_fn(image_bgr))
                prob = self._clamp_probability(prob)
                return CVInferenceResult(
                    malicious_probability=prob,
                    prediction="MALICIOUS" if prob >= 0.5 else "BENIGN",
                    model_source="python_adapter",
                )

            prob = self._predict_onnx(image_bgr)
            return CVInferenceResult(
                malicious_probability=prob,
                prediction="MALICIOUS" if prob >= 0.5 else "BENIGN",
                model_source="onnx",
            )
        except Exception as exc:  # noqa: BLE001
            return CVInferenceResult(
                malicious_probability=None,
                prediction=None,
                model_source=self.active_model_source,
                error=f"CV inference failed: {exc}",
            )

    def _load_adapter(self) -> None:
        if not self.adapter_path.exists():
            return
        spec = importlib.util.spec_from_file_location("cv_adapter", self.adapter_path)
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._adapter_fn = self._extract_adapter_fn(module)

    def _extract_adapter_fn(self, module: ModuleType) -> PredictFn | None:
        fn = getattr(module, "predict_malicious_probability", None)
        if fn is None or not callable(fn):
            return None
        return fn

    def _load_onnx(self) -> None:
        if ort is None or not self.onnx_path.exists():
            return
        self._onnx_session = ort.InferenceSession(str(self.onnx_path), providers=["CPUExecutionProvider"])
        self._onnx_input_name = self._onnx_session.get_inputs()[0].name

    def _predict_onnx(self, image_bgr: np.ndarray) -> float:
        input_meta = self._onnx_session.get_inputs()[0]
        input_tensor = self._prepare_onnx_input(image_bgr, input_meta.shape)
        outputs = self._onnx_session.run(None, {self._onnx_input_name: input_tensor})
        return self._parse_model_output(outputs[0])

    def _prepare_onnx_input(self, image_bgr: np.ndarray, input_shape: list[int | str | None]) -> np.ndarray:
        # Default size for dynamic models.
        target_h = 224
        target_w = 224

        if len(input_shape) == 4:
            # NCHW -> [N, C, H, W]
            if isinstance(input_shape[2], int):
                target_h = input_shape[2]
            if isinstance(input_shape[3], int):
                target_w = input_shape[3]
        elif len(input_shape) == 3:
            # CHW / HWC with unknown batch.
            if isinstance(input_shape[1], int):
                target_h = input_shape[1]
            if isinstance(input_shape[2], int):
                target_w = input_shape[2]

        resized = cv2.resize(image_bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)
        normalized = resized.astype(np.float32) / 255.0

        if len(input_shape) == 4 and input_shape[1] in (1, 3):
            # NCHW
            if input_shape[1] == 1:
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                tensor = gray[np.newaxis, np.newaxis, :, :]
            else:
                rgb = cv2.cvtColor(normalized, cv2.COLOR_BGR2RGB)
                tensor = np.transpose(rgb, (2, 0, 1))[np.newaxis, :, :, :]
        else:
            # Assume NHWC
            rgb = cv2.cvtColor(normalized, cv2.COLOR_BGR2RGB)
            tensor = rgb[np.newaxis, :, :, :]

        return tensor.astype(np.float32)

    def _parse_model_output(self, output: np.ndarray) -> float:
        flat = np.asarray(output, dtype=np.float32).reshape(-1)
        if flat.size == 0:
            raise ValueError("Empty model output.")

        if flat.size == 1:
            value = float(flat[0])
            if 0.0 <= value <= 1.0:
                return self._clamp_probability(value)
            return self._clamp_probability(1.0 / (1.0 + math.exp(-value)))

        # Multi-class output: treat index 1 as malicious.
        if np.all(flat >= 0) and 0.9 <= float(flat.sum()) <= 1.1:
            return self._clamp_probability(float(flat[1] if flat.size > 1 else flat[0]))

        shifted = flat - float(flat.max())
        exps = np.exp(shifted)
        probs = exps / float(exps.sum())
        return self._clamp_probability(float(probs[1] if probs.size > 1 else probs[0]))

    @staticmethod
    def _clamp_probability(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
