import json
import random
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

# ===== 振り分けモード =====
# "sort" : ソート→交互振り分け（再現性あり）
# "random"     : ランダム振り分け（毎回変わる）
SPLIT_MODE = "random"


# ===== クラス数を取得 =====
def get_class_count(project_name: str) -> int:
    meta_path = METADATA_DIR / f"{project_name}.json"
    if not meta_path.exists():
        return 0
    with open(meta_path, encoding="utf-8") as f:
        return len(json.load(f))


# ===== OSSリストを作成 =====
def build_project_list(files: list) -> list:
    projects = []
    for f in files:
        name = f.stem.replace("_dataset_with_features", "")
        if name in SKIP:
            continue
        class_count = get_class_count(name)
        projects.append((name, class_count, f))
    return projects


# ===== パターンA：ソート→交互振り分け =====
def split_sort(projects: list, train_ratio: float = 0.7):
    projects_sorted = sorted(projects, key=lambda x: x[1], reverse=True)

    train_projects = []
    test_projects = []
    train_total = 0
    total_classes = sum(p[1] for p in projects_sorted)
    target_train = total_classes * train_ratio

    for i, (name, count, f) in enumerate(projects_sorted):
        # 交互に振り分け、かつ学習用が70%に近くなるように調整
        if train_total < target_train and i % 2 == 0:
            train_projects.append((name, count, f))
            train_total += count
        else:
            test_projects.append((name, count, f))

    return train_projects, test_projects


# ===== パターンB：ランダム振り分け =====
def split_random(projects: list, train_ratio: float = 0.7, seed: int = None):

    if seed is not None:
        random.seed(seed)

    shuffled = projects[:]
    random.shuffle(shuffled)

    total_classes = sum(p[1] for p in shuffled)
    target_train = total_classes * train_ratio

    train_projects = []
    test_projects = []
    train_total = 0

    for name, count, f in shuffled:
        if train_total < target_train:
            train_projects.append((name, count, f))
            train_total += count
        else:
            test_projects.append((name, count, f))

    return train_projects, test_projects


# ===== 振り分け結果を表示 =====
def print_split_result(train_projects, test_projects):
    train_total = sum(p[1] for p in train_projects)
    test_total = sum(p[1] for p in test_projects)
    total = train_total + test_total

    print(f"学習用 ({train_total/total*100:.1f}% of classes):")
    for name, count, _ in train_projects:
        print(f"  {name} (classes={count})")
    print(f"テスト用 ({test_total/total*100:.1f}% of classes):")
    for name, count, _ in test_projects:
        print(f"  {name} (classes={count})")
    print()


# ===== 学習・評価 =====
def train_and_evaluate(train_projects, test_projects):
    print("[LOAD] 学習用データを読み込み中...")
    train_dfs = []
    for name, count, f in train_projects:
        df = pd.read_json(f)
        df["oss"] = name
        train_dfs.append(df)
        print(f"  {name}: {len(df)} rows")
    train_df = pd.concat(train_dfs, ignore_index=True)
    print(f"  学習データ合計: {len(train_df)} rows\n")

    print("[LOAD] テスト用データを読み込み中...")
    test_dfs = []
    for name, count, f in test_projects:
        df = pd.read_json(f)
        df["oss"] = name
        test_dfs.append(df)
        print(f"  {name}: {len(df)} rows")
    test_df = pd.concat(test_dfs, ignore_index=True)
    print(f"  テストデータ合計: {len(test_df)} rows\n")

    X_train = train_df[FEATURE_COLS]
    y_train = train_df["co_changed"].astype(int)
    X_test = test_df[FEATURE_COLS]
    y_test = test_df["co_changed"].astype(int)

    print("[TRAIN] RandomForest 学習中...")
    model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    print("  完了\n")

    y_pred = model.predict(X_test)

    print("===== 全体評価 =====")
    print(classification_report(y_test, y_pred, digits=4))

    print("===== OSS別評価 =====")
    for name, count, _ in test_projects:
        mask = test_df["oss"] == name
        y_t = y_test[mask]
        y_p = model.predict(X_test[mask])
        print(f"[{name}]")
        print(classification_report(y_t, y_p, digits=4))

    print("[FEATURE IMPORTANCE]")
    for name, score in zip(FEATURE_COLS, model.feature_importances_):
        print(f"  {name:25s} = {score:.4f}")


# ===== main =====
if __name__ == "__main__":

    files = list(JSON_DIR.glob("*_dataset_with_features.json"))
    if not files:
        print("[ERROR] dataset_with_features.json が見つかりません")
        exit(1)

    projects = build_project_list(files)

    if SPLIT_MODE == "sort":
        print("===== OSS振り分け結果（ソート→交互） =====")
        train_projects, test_projects = split_sort(projects)
    elif SPLIT_MODE == "random":
        print("===== OSS振り分け結果（ランダム） =====")
        train_projects, test_projects = split_random(projects)
    else:
        print(f"[ERROR] 不明なSPLIT_MODE: {SPLIT_MODE}")
        exit(1)

    print_split_result(train_projects, test_projects)
    train_and_evaluate(train_projects, test_projects)