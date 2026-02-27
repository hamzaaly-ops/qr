import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.ml_features import FEATURE_NAMES, extract_url_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train phishing URL classifier.")
    parser.add_argument("--input", required=True, help="CSV file with columns: url,label")
    parser.add_argument(
        "--output",
        default="models/phishing_model.joblib",
        help="Path to save trained model",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data reserved for test set",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = pd.read_csv(args.input)

    if "url" not in frame.columns or "label" not in frame.columns:
        raise ValueError("Input CSV must include columns named 'url' and 'label'.")

    labels = frame["label"].astype(int)
    if set(labels.unique()) - {0, 1}:
        raise ValueError("Labels must be binary (0 for benign, 1 for phishing).")

    feature_rows = [extract_url_features(url) for url in frame["url"].astype(str)]
    features = pd.DataFrame(feature_rows)[FEATURE_NAMES]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=args.test_size,
        random_state=42,
        stratify=labels,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1200, class_weight="balanced")),
        ]
    )
    model.fit(x_train, y_train)

    probs = model.predict_proba(x_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    accuracy = accuracy_score(y_test, preds)
    roc_auc = roc_auc_score(y_test, probs)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC-AUC : {roc_auc:.4f}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    print(f"Saved model: {output_path}")


if __name__ == "__main__":
    main()
