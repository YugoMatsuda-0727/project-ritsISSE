# csv_transfer.py
import json
import csv
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
PAIR_DIR = BASE_DIR / "outputs" / "pairs"
CSV_DIR = BASE_DIR / "outputs" / "csv"
CSV_DIR.mkdir(parents=True, exist_ok=True)


# ===== Step2が出力するキー一覧 =====
FEATURE_KEYS = [
    "file_a",
    "file_b",
    "same_package",
    "package_prefix_ratio",
    "class_name_jaccard",
    "same_role",
]

# ===== JSON読み込み =====
def load_pairs(json_path):
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

# ===== 特徴量抽出 =====
def extract_features(pair):
    return {
        key: pair[key] for key in FEATURE_KEYS
    }

# ===== JSON → 行データ =====
def convert_pairs(pairs):
    rows = []
    for pair in pairs:
        try:
            rows.append(extract_features(pair))
        except KeyError as e:
            print(f"[WARN] キーが見つかりません: {e} — このペアをスキップします")
    return rows

# ===== CSV出力 =====
def save_csv(rows, out_path):
    if not rows:
        print("[WARN] rows is empty — CSVを出力しません")
        return
 
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEATURE_KEYS)
        writer.writeheader()
        writer.writerows(rows)

# ===== main =====
if __name__ == "__main__":
 
    json_files = list(PAIR_DIR.glob("*_pairs.json"))  # "_mini"を削除
 
    if not json_files:
        print(f"[WARN] {PAIR_DIR} に *_pairs.json が見つかりません")
    
    for json_file in json_files:
        print(f"[LOAD] {json_file.name}")
 
        pairs = load_pairs(json_file)
        rows = convert_pairs(pairs)
 
        out_csv = CSV_DIR / f"{json_file.stem}.csv"
        save_csv(rows, out_csv)
 
        print(f"[DONE] {out_csv} ({len(rows)} rows)")
