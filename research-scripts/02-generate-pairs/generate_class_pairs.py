import json
from pathlib import Path
import itertools
import random

# === 入出力ディレクトリ ===
BASE_DIR = Path(__file__).resolve().parents[2]                              # =java-data/
METADATA_DIR = BASE_DIR / "research-scripts" / "outputs" / "metadata"       # .jsonの場所
OUTPUT_DIR = BASE_DIR / "research-scripts" / "outputs" / "pairs"            # 出力先
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_PAIRS=2000

def load_metadata(json_path):                      # .json -> データ構造に変換して返す
    """
    1プロジェクト分の metadata.json を読み込む
    """
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def generate_class_pairs(class_list):
    """
    クラスのリストから、順序なしペアをすべて作る
    """
    return list(itertools.combinations(class_list, 2))


def compute_pair_features(a, b):
    """
    クラスAとBから、構造的特徴量を計算
    """

    # 同一パッケージか
    same_package = int(a["package"] == b["package"])

    # パッケージ共通prefix長
    pa = set(a["package_tokens"])
    pb = set(b["package_tokens"])
    common = 0

    if pa or pb:
        package_token_similarity = len(pa & pb) / len(pa | pb)
    else:
        package_token_similarity = 0.0

    package_prefix_ratio = common / max(len(pa), len(pb))  # 率=共通/長いほうの個数

    # クラス名トークンのJaccard類似度
    set_a = set(a["class_name_tokens"])
    set_b = set(b["class_name_tokens"])
    name_jaccard = len(set_a & set_b) / len(set_a | set_b) if set_a | set_b else 0.0

    # 役割一致（Controller / Service など）
    same_role = int(any(
        a["class_role"][k] and b["class_role"][k]
        for k in a["class_role"]
    ))

    return {
        "file_a": a["file_path"],
        "file_b": b["file_path"],
        "same_package": same_package,
        "package_prefix_ratio": package_prefix_ratio,
        "class_name_jaccard": name_jaccard,
        "same_role": same_role
    }


def process_project(json_path):
    classes = load_metadata(json_path)
    pairs = generate_class_pairs(classes)

    # 制限してランダム生成
    random.shuffle(pairs)
    pairs = pairs[:MAX_PAIRS]

    results = []
    for a, b in pairs:
        features = compute_pair_features(a, b)
        results.append(features)

    return results


if __name__ == "__main__":

    for json_file in METADATA_DIR.glob("*.json"):
        project_name = json_file.stem
        print(f"[PROCESS] {project_name}")

        pair_data = process_project(json_file)

        out_path = OUTPUT_DIR / f"{project_name}_pairs.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(pair_data, f, indent=2)

        print(f"[DONE] {project_name}: {len(pair_data)} pairs")
