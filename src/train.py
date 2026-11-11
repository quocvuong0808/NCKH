from __future__ import annotations
import hashlib
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from core import FEATURES, validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/student-por.csv"
SEED = 42

def metrics(y, pred, score=None):
    result = dict(precision=float(precision_score(y, pred, zero_division=0)), recall=float(recall_score(y, pred, zero_division=0)), f1=float(f1_score(y, pred, zero_division=0)), accuracy=float(accuracy_score(y, pred)), confusion_matrix=confusion_matrix(y, pred, labels=[0, 1]).tolist())
    if score is not None:
        result["average_precision"] = float(average_precision_score(y, score))
    return result

def main():
    if not DATA.exists():
        raise SystemExit("Thiếu data/raw/student-por.csv. Xem docs/06_nguon_du_lieu.md.")
    raw = pd.read_csv(DATA, sep=";")
    data = validate(raw, "G2", target=True)
    y = (data.G3 < 10).astype(int)
    if y.value_counts().min() < 10 or y.nunique() != 2:
        raise SystemExit("Cần ít nhất 10 bản ghi mỗi lớp để chia tập và chạy CV.")
    train, test = train_test_split(data.index, test_size=0.2, random_state=SEED, stratify=y)
    report = {"dataset": "UCI Student Performance / student-por.csv", "sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(), "target": "G3 < 10/20", "n_rows": len(data), "n_risk": int(y.sum()), "split": "Stratified 80/20 seed 42; same rows for both stages", "limitations": ["Portuguese secondary school students, not Vietnamese university students", "No person IDs: cannot verify person overlap", "Grade-only features; no claim about activity collection time", "Uncalibrated model scores; fixed threshold 0.5", "G1/G2 may differ in assessment difficulty"], "stages": {}}
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    for stage, columns in FEATURES.items():
        X = data[columns]
        candidates = {
            "majority": DummyClassifier(strategy="most_frequent"),
            "logistic": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000, random_state=SEED)),
            "tree": DecisionTreeClassifier(max_depth=3, min_samples_leaf=10, class_weight="balanced", random_state=SEED),
        }
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        scores = {name: float(cross_val_score(model, X.loc[train], y.loc[train], cv=cv, scoring="f1").mean()) for name, model in candidates.items()}
        selected = max(scores, key=scores.get)
        results = {"rule_grade_below_10": metrics(y.loc[test], (X.loc[test, stage] < 10).astype(int))}
        for name, model in candidates.items():
            model.fit(X.loc[train], y.loc[train])
            p = model.predict_proba(X.loc[test])[:, list(model.classes_).index(1)]
            results[name] = metrics(y.loc[test], (p >= 0.5).astype(int), p)
        joblib.dump(candidates[selected], ROOT / f"models/pipeline_{stage}.pkl")
        report["stages"][stage] = {"features": columns, "selected_by_training_cv": selected, "training_cv_f1": scores, "test_results": results}
    (ROOT / "reports/metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
