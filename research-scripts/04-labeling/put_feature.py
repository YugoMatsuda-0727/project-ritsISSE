# put_feature.py

import json
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "outputs" / "dataset_pairs"
METADATA_DIR = BASE_DIR / "outputs" / "metadata"
OUTPUT_DIR = BASE_DIR / "outputs" / "datasets_with_features"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ===== metadata index 作成 =====
def build_metadata_index(metadata):
    return {item["file_path"]: item for item in metadata}


# ===== 類似度 =====
def jaccard(a, b):
    if not a or not b:
        return 0.0
    a, b = set(a), set(b)
    return len(a & b) / len(a | b)


# ===== test 除外 =====
def is_valid_pair(pair):
    return (
        "src/test" not in pair["file1"]
        and "src/test" not in pair["file2"]
    )


# ===== feature 付与 =====
def enrich_pairs(dataset, meta_index):
    enriched = []
    skipped = 0

    for pair in dataset:
        # ---- v1: test 除外
        if not is_valid_pair(pair):
            skipped += 1
            continue

        f1 = pair["file1"]
        f2 = pair["file2"]

        if f1 not in meta_index or f2 not in meta_index:
            skipped += 1
            continue

        m1 = meta_index[f1]
        m2 = meta_index[f2]

        enriched.append({
            **pair,

            "package_similarity": jaccard(
                m1.get("package_tokens", []),
                m2.get("package_tokens", [])
            ),

            "class_name_similarity": jaccard(
                m1.get("class_name_tokens", []),
                m2.get("class_name_tokens", [])
            ),

            "import_similarity": jaccard(
                m1.get("import_packages", []),
                m2.get("import_packages", [])
            ),

            "method_similarity": jaccard(
                [m["name"] for m in m1.get("methods", [])],
                [m["name"] for m in m2.get("methods", [])]
            ),
        })

    return enriched, skipped


# ===== main =====
if __name__ == "__main__":

    for dataset_file in DATASET_DIR.glob("*_dataset.json"):
        project = dataset_file.stem.replace("_pairs_mini_dataset", "")
        print(f"[PROCESS] {project}")

        metadata_file = METADATA_DIR / f"{project}.json"
        if not metadata_file.exists():
            print("  [SKIP] metadata not found")
            continue

        with open(dataset_file, encoding="utf-8") as f:
            dataset = json.load(f)

        with open(metadata_file, encoding="utf-8") as f:
            metadata = json.load(f)

        meta_index = build_metadata_index(metadata)

        enriched, skipped = enrich_pairs(dataset, meta_index)

        out_file = OUTPUT_DIR / f"{project}_dataset_with_features.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2)

        print(f"  total    = {len(dataset)}")
        print(f"  enriched = {len(enriched)}")
        print(f"  skipped  = {skipped}")
        print("-" * 40)
