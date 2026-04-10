import json
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
PAIR_DIR = BASE_DIR / "outputs" / "cochange_pairs"
OUT_DIR = BASE_DIR / "outputs" / "dataset"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def normalize_positive(data):
    rows = []
    for p in data:
        rows.append({
            "repo": p["repo"],
            "file1": p["file1"],
            "file2": p["file2"],
            "label": 1
        })
    return rows

def normalize_negative(data):
    rows = []
    for p in data:
        rows.append({
            "repo": p["repo"],
            "file1": p["file1"],
            "file2": p["file2"],
            "label": 0
        })
    return rows

# ===== main =====
if __name__ == "__main__":

    repos = set()

    for pos_file in PAIR_DIR.glob("*_cochange_pairs_am.json"):
        repo = pos_file.stem.replace("_cochange_pairs_am", "")
        repos.add(repo)

    for repo in sorted(repos):
        print(f"[PROCESS] {repo}")

        pos_path = PAIR_DIR / f"{repo}_cochange_pairs_am.json"
        neg_path = PAIR_DIR / f"{repo}_negative_pairs_am.json"

        if not pos_path.exists() or not neg_path.exists():
            print("  [SKIP] missing files")
            continue

        positives = normalize_positive(load_json(pos_path))
        negatives = normalize_negative(load_json(neg_path))

        dataset = positives + negatives

        out_path = OUT_DIR / f"{repo}_pairs_mini_dataset.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"  positives = {len(positives)}")
        print(f"  negatives = {len(negatives)}")
        print(f"  total = {len(dataset)}")
        print("-" * 40)
