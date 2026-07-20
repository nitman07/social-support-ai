"""Training pipeline — extracts features, trains RF, evaluates, saves."""

import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.ml.features import FEATURE_NAMES, FeatureVector, extract_all_feature_vectors

logger = get_logger(__name__)

MODEL_DIR = Path("data/models")
MODEL_PATH = MODEL_DIR / "eligibility_rf.pkl"


async def run_training() -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting feature vectors from database...")
    vectors = await extract_all_feature_vectors()

    if not vectors:
        logger.error("No feature vectors extracted — is the database seeded?")
        return {"status": "failed", "reason": "no_data"}

    valid = [v for v in vectors if v.label is not None]
    if not valid:
        logger.error("No labeled data found — run seed_runner first")
        return {"status": "failed", "reason": "no_labels"}

    logger.info(f"Found {len(valid)} labeled samples out of {len(vectors)} total")

    X = np.array([v.array for v in valid])
    y = np.array([int(v.label) for v in valid])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
    )

    logger.info(f"Training Random Forest on {len(X_train)} samples...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.0

    logger.info(f"Accuracy:  {accuracy:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")
    logger.info(f"ROC AUC:   {auc:.4f}")

    importance = dict(zip(FEATURE_NAMES, model.feature_importances_))
    logger.info("Feature importances:")
    for name, imp in sorted(importance.items(), key=lambda x: -x[1]):
        logger.info(f"  {name}: {imp:.4f}")

    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"Confusion matrix:\n{cm}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {MODEL_PATH}")

    return {
        "status": "success",
        "samples": len(valid),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "feature_importance": importance,
        "model_path": str(MODEL_PATH),
    }


async def main() -> None:
    result = await run_training()
    if result["status"] == "success":
        logger.info("=" * 50)
        logger.info("TRAINING COMPLETE")
        logger.info(f"  Accuracy:  {result['accuracy']}")
        logger.info(f"  Precision: {result['precision']}")
        logger.info(f"  Recall:    {result['recall']}")
        logger.info(f"  F1 Score:  {result['f1_score']}")
        logger.info(f"  ROC AUC:   {result['roc_auc']}")
        logger.info("=" * 50)
    else:
        logger.error(f"Training failed: {result.get('reason', 'unknown')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
