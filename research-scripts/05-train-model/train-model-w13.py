import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
CSV_DIR = BASE_DIR / "outputs" / "dataset"

# ===== CSV読み込み =====
def load_csv(csv_path):
    print(f"[LOAD] {csv_path.name}")
    return pd.read_csv(csv_path)

# ===== main =====
if __name__ == "__main__":

    for csv_file in CSV_DIR.glob("*_pairs_mini_dataset.csv"):

        df = load_csv(csv_file)

        if df.empty:
            print("[SKIP] empty csv")
            continue

        # ===== 特徴量とラベル =====
        X = df[[
            "package_similarity",
            "class_name_similarity"
        ]]

        # label を仮ラベルにする
        y = df["label"]

        # ===== train / test 分割 =====
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.3,
            random_state=42
        )

        # ===== RandomForest =====
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )

        model.fit(X_train, y_train)

        # ===== 評価 =====
        y_pred = model.predict(X_test)

        print(f"\n[RESULT] {csv_file.stem}")
        print(classification_report(y_test, y_pred))

        # ===== 特徴量重要度 =====
        importances = model.feature_importances_
        for name, score in zip(X.columns, importances):
            print(f"  importance({name}) = {score:.4f}")

        print("-" * 40)
