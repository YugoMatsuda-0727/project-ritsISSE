import json
from pathlib import Path

# ===== パス =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "outputs" / "dataset_pairs"
META_DIR = BASE_DIR / "outputs" / "metadata"
OUT_DIR = BASE_DIR / "outputs" / "dataset_W14"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== util =====
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def normalize(path):
    return path.replace("\\", "/")

def build_metadata_index(meta, repo_dir):
    index = {}
    for c in meta:
        p = Path(c["file_path"])
        try:
            rel = p.relative_to(repo_dir)
        except ValueError:
            continue
        index[normalize(str(rel))] = c
    return index

# ===== main =====
if __name__ == "__main__":

    for dataset_path in DATASET_DIR.glob("*_pairs_mini_dataset.json"):

        repo = dataset_path.stem.replace("_pairs_mini_dataset", "")
        print(f"[PROCESS] {repo}")

        meta_path = META_DIR / f"{repo}.json"
        if not meta_path.exists():
            print("  [SKIP] metadata not found")
            continue

        dataset = load_json(dataset_path)
        metadata = load_json(meta_path)
        repo_dir = BASE_DIR / repo
        meta_index = build_metadata_index(metadata, repo_dir)

        enriched = []
        skipped = 0

        for pair in dataset:
            f1 = pair["file1"]
            f2 = pair["file2"]

            if f1 not in meta_index or f2 not in meta_index:
                skipped += 1
                continue

            c1 = meta_index[f1]
            c2 = meta_index[f2]

            row = {
                "repo": repo,
                "file1": f1,
                "file2": f2,
                "label": pair["label"],

                # ===== 特徴量 =====
                "package_similarity": jaccard(
                    c1["package_tokens"],
                    c2["package_tokens"]
                ),
                "class_name_similarity": jaccard(
                    c1["class_name_tokens"],
                    c2["class_name_tokens"]
                )
            }

            enriched.append(row)

        out_path = OUT_DIR / dataset_path.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2, ensure_ascii=False)

        print(f"  total = {len(dataset)}")
        print(f"  enriched = {len(enriched)}")
        print(f"  skipped = {skipped}")
        print("-" * 40)
