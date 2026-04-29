import json
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
JSON_DIR = BASE_DIR / "outputs" / "datasets_with_features"
METADATA_DIR = BASE_DIR / "outputs" / "metadata"

FEATURE_COLS = [
    "package_similarity",
    "class_name_similarity",
    "import_similarity",
    "method_similarity",
    "field_similarity",
    "interface_similarity",
    "param_type_similarity",
    "superclass_match",
    "class_name_suffix_match",
]

SKIP = {".git", "dummy_sample", "Log", "research-scripts"}


# ===== クラス数を取得 =====
def get_class_count(project_name: str) -> int:
    meta_path = METADATA_DIR / f"{project_name}.json"
    if not meta_path.exists():
        return 0
    with open(meta_path, encoding="utf-8") as f:
        return len(json.load(f))


# ===== OSSをクラス数ベースで7:3に振り分け =====
def split_oss_by_class_count(files: list, train_ratio: float = 0.7):
    """
    クラス数の合計が train_ratio に近くなるように
    OSSを学習用とテスト用に振り分ける（greedy法）
    """
    # プロジェクト名とクラス数のリストを作成
    projects = []
    for f in files:
        name = f.stem.replace("_dataset_with_features", "")
        if name in SKIP:
            continue
        class_count = get_class_count(name)
        projects.append((name, class_count, f))

    # クラス数の多い順に並べる
    projects.sort(key=lambda x: x[1], reverse=True)

    total_classes = sum(p[1] for p in projects)
    target_train = total_classes * train_ratio

    train_projects = []
    test_projects = []
    train_total = 0

    for name, count, f in projects:
        if train_total < target_train:
            train_projects.append((name, count, f))
            train_total += count
        else:
            test_projects.append((name, count, f))

    return train_projects, test_projects


# ===== main =====
if __name__ == "__main__":

    files = list(JSON_DIR.glob("*_dataset_with_features.json"))

    if not files:
        print("[ERROR] dataset_with_features.json が見つかりません")
        exit(1)

    # ===== OSS振り分け =====
    train_projects, test_projects = split_oss_by_class_count(files)

    train_class_total = sum(p[1] for p in train_projects)
    test_class_total = sum(p[1] for p in test_projects)
    total = train_class_total + test_class_total

    print("===== OSS振り分け結果 =====")
    print(f"学習用 ({train_class_total/total*100:.1f}% of classes):")
    for name, count, _ in train_projects:
        print(f"  {name} (classes={count})")
    print(f"テスト用 ({test_class_total/total*100:.1f}% of classes):")
    for name, count, _ in test_projects:
        print(f"  {name} (classes={count})")
    print()

    # ===== 学習データの読み込み =====
    print("[LOAD] 学習用データを読み込み中...")
    train_dfs = []
    for name, count, f in train_projects:
        df = pd.read_json(f)
        df["oss"] = name
        train_dfs.append(df)
        print(f"  {name}: {len(df)} rows")

    train_df = pd.concat(train_dfs, ignore_index=True)
    print(f"  学習データ合計: {len(train_df)} rows\n")

    # ===== テストデータの読み込み =====
    print("[LOAD] テスト用データを読み込み中...")
    test_dfs = []
    for name, count, f in test_projects:
        df = pd.read_json(f)
        df["oss"] = name
        test_dfs.append(df)
        print(f"  {name}: {len(df)} rows")

    test_df = pd.concat(test_dfs, ignore_index=True)
    print(f"  テストデータ合計: {len(test_df)} rows\n")

    # ===== 特徴量とラベル =====
    X_train = train_df[FEATURE_COLS]
    y_train = train_df["co_changed"].astype(int)

    X_test = test_df[FEATURE_COLS]
    y_test = test_df["co_changed"].astype(int)

    # ===== RandomForest 学習 =====
    print("[TRAIN] RandomForest 学習中...")
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    print("  完了\n")

    # ===== 評価（全体）=====
    y_pred = model.predict(X_test)

    print("===== 全体評価 =====")
    print(classification_report(y_test, y_pred, digits=4))

    # ===== 評価（OSSごと）=====
    print("===== OSS別評価 =====")
    for name, count, _ in test_projects:
        mask = test_df["oss"] == name
        y_t = y_test[mask]
        y_p = model.predict(X_test[mask])
        print(f"[{name}]")
        print(classification_report(y_t, y_p, digits=4))

    # ===== 特徴量重要度 =====
    print("[FEATURE IMPORTANCE]")
    for name, score in zip(FEATURE_COLS, model.feature_importances_):
        print(f"  {name:25s} = {score:.4f}")