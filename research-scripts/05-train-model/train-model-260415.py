import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "outputs" / "dataset"

# ===== CSV読み込み =====
def load_csv(csv_path):
  print(f"[LOAD] {csv_path.name}")
  try:
    return pd.read_csv(csv_path)
  except Exception as e:
    print(f"[ERROR] 読み込み失敗: {e}")
    return pd.DataFrame()

# ===== main =====
if __name__ == "__main__":

  files = list(DATASET_DIR.glob("*_dataset.csv"))

  if not files:
    print("[ERROR] *_dataset.csv が見つかりません")
    exit(1)

  for csv_file in files:

    df = load_csv(csv_file)

    print(df.columns)

    print(f"  rows = {len(df)}")

    if df.empty:
      print("[SKIP] empty dataset")
      continue

    # ===== 必要カラムチェック =====
    required_columns = [
      "package_similarity",
      "class_name_similarity",
      "co_changed"
    ]

    if not all(col in df.columns for col in required_columns):
      print("[SKIP] 必要カラム不足")
      continue

    # ===== 特徴量とラベル =====
    X = df[
      [
        "package_similarity",
        "class_name_similarity"
      ]
    ]

    y = df["co_changed"]

    # ===== train / test 分割 =====
    try:
      X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        stratify=y,
        random_state=42  # 再現性確保
      )
    except ValueError as e:
      print(f"[SKIP] 分割エラー: {e}")
      continue

    # ===== RandomForest =====
    model = RandomForestClassifier(
      n_estimators=100,
      random_state=42, 
      class_weight="balanced"  # クラス不均衡に対応
    )

    model.fit(X_train, y_train)

    # ===== 評価 =====
    y_pred = model.predict(X_test)

    print(f"\n[RESULT] {csv_file.stem}")
    print(classification_report(y_test, y_pred, digits=4))

    # ===== 特徴量重要度 =====
    print("[FEATURE IMPORTANCE]")
    for name, score in zip(X.columns, model.feature_importances_):
      print(f"  {name:25s} = {score:.4f}")

    print("-" * 50)