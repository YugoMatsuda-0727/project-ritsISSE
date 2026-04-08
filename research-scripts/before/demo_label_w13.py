# demo_label_w13.py

import json
import csv
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
PAIR_DIR = BASE_DIR / "outputs" / "pairs"
DATASET_DIR = BASE_DIR / "outputs" / "dataset"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# ===== JSON読み込み =====
def load_pairs(json_path):
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

# ===== ラベル付与（一時的な対応策） =====
def assign_label(pair):
    """
    方法A:
    パッケージ類似度が 1.0 の場合 → 共変更あり (1)
    それ以外 → 共変更なし (0)
    """
    return 1 if pair["package_similarity"] == 1.0 else 0

# ===== 特徴量 + ラベル =====
def extract_row(pair):
    return {
        "package_similarity": pair["package_similarity"],
        "class_name_similarity": pair["class_name_similarity"],
        "label": assign_label(pair)
    }

# ===== JSON → CSV行 =====
def convert_pairs(pairs):
    rows = []
    for pair in pairs:
        rows.append(extract_row(pair))
    return rows

# ===== CSV保存 =====
def save_csv(rows, out_path):
    if not rows:
        print("[WARN] empty dataset")
        return

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

# ===== main =====
if __name__ == "__main__":

    for json_file in PAIR_DIR.glob("*_pairs_mini.json"):
        print(f"[PROCESS] {json_file.name}")

        pairs = load_pairs(json_file)
        rows = convert_pairs(pairs)

        out_csv = DATASET_DIR / f"{json_file.stem}_dataset.csv"
        save_csv(rows, out_csv)

        print(f"[DONE] {out_csv} ({len(rows)} rows)")
