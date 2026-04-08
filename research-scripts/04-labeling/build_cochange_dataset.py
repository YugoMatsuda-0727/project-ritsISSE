# build_cochange_dataset.py
import json
import csv
import itertools
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[2]          # java-data/
COMMIT_DIR = BASE_DIR / "research-scripts" / "outputs" / "commit_logs"
CSV_DIR    = BASE_DIR / "research-scripts" / "outputs" / "csv"
OUTPUT_DIR = BASE_DIR / "research-scripts" / "outputs" / "dataset"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# testパスを除外するキーワード
TEST_KEYWORDS = ["test", "Test"]


# ===== 共変更ペアセットの構築 =====
def build_cochange_set(commit_log_path: Path) -> set:
    """
    commit_log の changes から .java かつ非testファイルのみ抽出し、
    同一コミット内の全ペアを co_changed_pairs に登録する
    """
    with open(commit_log_path, encoding="utf-8") as f:
        commits = json.load(f)

    co_changed_pairs = set()

    for commit in commits:
        # testファイルを除外 & .javaのみ
        files = [
            c["file"] for c in commit["changes"]
            if not any(kw in c["file"] for kw in TEST_KEYWORDS)
            and c["file"].endswith(".java")
        ]

        # 2ファイル以上変更されたコミットのみペアを生成
        if len(files) < 2:
            continue

        for a, b in itertools.combinations(sorted(files), 2):
            co_changed_pairs.add((a, b))

    return co_changed_pairs


# ===== CSVにラベルを付与 =====
def label_pairs(csv_path: Path, co_changed_pairs: set) -> list:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = tuple(sorted([row["file_a"], row["file_b"]]))
            row["co_changed"] = 1 if key in co_changed_pairs else 0
            rows.append(row)
    return rows


# ===== CSV出力 =====
def save_dataset(rows: list, out_path: Path):
    if not rows:
        print("[WARN] rows is empty")
        return

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ===== ラベル分布のサマリ表示 =====
def print_summary(project_name: str, rows: list):
    total = len(rows)
    positive = sum(1 for r in rows if int(r["co_changed"]) == 1)
    negative = total - positive
    ratio = positive / total * 100 if total > 0 else 0
    print(f"  total   : {total}")
    print(f"  positive: {positive} ({ratio:.2f}%)")
    print(f"  negative: {negative}")


# ===== main =====
if __name__ == "__main__":

    for commit_file in COMMIT_DIR.glob("*_commits.json"):
        project_name = commit_file.stem.replace("_commits", "")
        csv_file = CSV_DIR / f"{project_name}_pairs.csv"

        if not csv_file.exists():
            print(f"[SKIP] CSVが見つかりません: {csv_file.name}")
            continue

        print(f"[PROCESS] {project_name}")

        co_changed_pairs = build_cochange_set(commit_file)
        rows = label_pairs(csv_file, co_changed_pairs)

        out_path = OUTPUT_DIR / f"{project_name}_dataset.csv"
        save_dataset(rows, out_path)
        print_summary(project_name, rows)

        print(f"[DONE] {out_path.name}")