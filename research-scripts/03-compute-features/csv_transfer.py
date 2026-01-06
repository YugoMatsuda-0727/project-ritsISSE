# csv_transfer.py
import json
import csv
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
PAIR_DIR = BASE_DIR / "outputs" / "pairs"
CSV_DIR = BASE_DIR / "outputs" / "csv"
CSV_DIR.mkdir(parents=True, exist_ok=True)

# ===== JSON読み込み =====
def load_pairs(json_path):
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

# ===== 特徴量抽出 =====
def extract_features(pair):
    return {
        "package_similarity": pair["package_similarity"],
        "class_name_similarity": pair["class_name_similarity"],
    }

# ===== JSON → 行データ =====
def convert_pairs(pairs):
    rows = []
    for pair in pairs:
        rows.append(extract_features(pair))
    return rows

# ===== CSV出力 =====
def save_csv(rows, out_path):
    if not rows:
        print("[WARN] rows is empty")
        return

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

# ===== main =====
if __name__ == "__main__":

    for json_file in PAIR_DIR.glob("*_pairs_mini.json"):
        print(f"[LOAD] {json_file.name}")

        pairs = load_pairs(json_file)
        rows = convert_pairs(pairs)

        out_csv = CSV_DIR / f"{json_file.stem}.csv"
        save_csv(rows, out_csv)

        print(f"[DONE] {out_csv} ({len(rows)} rows)")
