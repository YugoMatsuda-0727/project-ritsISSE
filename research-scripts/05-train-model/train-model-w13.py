import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
JSON_DIR = BASE_DIR / "outputs" / "datasets_with_features"

# ===== JSON読み込み =====
def load_json(json_path):
    print(f"[LOAD] {json_path.name}")
    return pd.read_json(json_path)

# ===== main =====
if __name__ == "__main__":

    files = list(JSON_DIR.glob("*_dataset_with_features.json"))

    if not files:
        print("[ERROR] dataset_with_features.json が見つかりません")
        exit(1)

    for json_file in files:

        df = load_json(json_file)

        print(f"  rows = {len(df)}")

        if df.empty:
            print("[SKIP] empty dataset")
            continue

        # ===== 特徴量とラベル =====
        X = df[
            [
                "package_similarity",
                "class_name_similarity"
            ]
        ]

        y = df["label"]

        # ===== train / test 分割 =====
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.3,
            random_state=42,
            stratify=y
        )

        # ===== RandomForest =====
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )

        model.fit(X_train, y_train)

        # ===== 評価 =====
        y_pred = model.predict(X_test)

        print(f"\n[RESULT] {json_file.stem}")
        print(classification_report(y_test, y_pred, digits=4))

        # ===== 特徴量重要度 =====
        print("[FEATURE IMPORTANCE]")
        for name, score in zip(X.columns, model.feature_importances_):
            print(f"  {name:25s} = {score:.4f}")

        print("-" * 50)
