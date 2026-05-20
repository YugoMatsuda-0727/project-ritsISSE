# put_feature.py

import json
import csv
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "outputs" / "dataset"
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


# ===== 継承関係の一致 =====
def superclass_match(m1, m2) -> float:
    """
    親クラスが同じなら 1.0、片方でも None なら 0.0
    """
    s1 = m1.get("superclass")
    s2 = m2.get("superclass")
    if s1 and s2 and s1 == s2:
        return 1.0
    return 0.0

# ===== クラス名の末尾一致 =====
def class_name_suffix_match(m1, m2) -> float:
    t1 = m1.get("class_name_tokens", [])
    t2 = m2.get("class_name_tokens", [])
    if not t1 or not t2:
        return 0.0
    return 1.0 if t1[-1] == t2[-1] else 0.0

# ===== w6-仮説1 直接import依存 =====
def direct_import(m1, m2) -> float:
    imports1 = set(m1.get("imports", []))
    imports2 = set(m2.get("imports", []))
    class1 = m1.get("class_name", "")
    class2 = m2.get("class_name", "")

    # importのフルパス末尾がクラス名と一致するかで判定
    def imported(imports, class_name):
        return any(imp.split(".")[-1] == class_name for imp in imports)

    if imported(imports1, class2) or imported(imports2, class1):
        return 1.0
    return 0.0


# ===== w6-仮説2 引数型依存 =====
def param_type_dependency(m1, m2) -> float:
    params1 = set(m1.get("param_types", []))
    params2 = set(m2.get("param_types", []))
    class1 = m1.get("class_name", "")
    class2 = m2.get("class_name", "")

    if class2 in params1 or class1 in params2:
        return 1.0
    return 0.0


# ===== w6-仮説3 継承依存（直接の親子関係） =====
def inheritance_dependency(m1, m2) -> float:
    super1 = m1.get("superclass")
    super2 = m2.get("superclass")
    class1 = m1.get("class_name", "")
    class2 = m2.get("class_name", "")

    if super1 == class2 or super2 == class1:
        return 1.0
    return 0.0


# ===== w6-仮説4 クラスロールペア =====
ROLE_PAIRS = [
    ("controller", "service"),
    ("service", "repository"),
    ("service", "dao"),
]

def class_role_pair(m1, m2) -> float:
    role1 = m1.get("class_role", {})
    role2 = m2.get("class_role", {})

    for r_a, r_b in ROLE_PAIRS:
        if (role1.get(r_a) and role2.get(r_b)) or \
           (role1.get(r_b) and role2.get(r_a)):
            return 1.0
    return 0.0


# ===== test 除外 =====
def is_valid_pair(pair):
    return (
        "src/test" not in pair["file_a"]
        and "src/test" not in pair["file_b"]
    )


# ===== feature 付与 =====
def enrich_pairs(dataset, meta_index):
    enriched = []
    skipped = 0

    for pair in dataset:
        if not is_valid_pair(pair):
            skipped += 1
            continue

        f1 = pair["file_a"]
        f2 = pair["file_b"]

        if f1 not in meta_index or f2 not in meta_index:
            skipped += 1
            continue

        m1 = meta_index[f1]
        m2 = meta_index[f2]

        enriched.append({
            **pair,

            # ===== 既存の4特徴量（正規表現ベース）=====
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

            # ===== 追加の3特徴量（ASTベース）=====
            "field_similarity": jaccard(
                m1.get("fields", []),
                m2.get("fields", [])
            ),
            "interface_similarity": jaccard(
                m1.get("interfaces", []),
                m2.get("interfaces", [])
            ),
            "param_type_similarity": jaccard(
                m1.get("param_types", []),
                m2.get("param_types", [])
            ),
            "superclass_match": superclass_match(m1, m2),
            "class_name_suffix_match": class_name_suffix_match(m1, m2),
        })

    return enriched, skipped


# ===== main =====
if __name__ == "__main__":

    for dataset_file in DATASET_DIR.glob("*_dataset.csv"):
        project = dataset_file.stem.replace("_dataset", "")
        print(f"[PROCESS] {project}")

        metadata_file = METADATA_DIR / f"{project}.json"
        if not metadata_file.exists():
            print("  [SKIP] metadata not found")
            continue

        with open(dataset_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            dataset = list(reader)

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