import json
import random
from pathlib import Path
from itertools import combinations

# ===== パス =====
BASE_DIR = Path(__file__).resolve().parents[1]
COMMIT_DIR = BASE_DIR / "outputs" / "commit_logs"
POS_DIR = BASE_DIR / "outputs" / "cochange_pairs"
OUT_DIR = BASE_DIR / "outputs" / "cochange_pairs"

# ===== 設定 =====
TARGET_EXT = ".java"
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

def collect_all_java_files(commits):
    files = set()
    for c in commits:
        for ch in c["changes"]:
            if ch["file"].endswith(TARGET_EXT):
                files.add(ch["file"])
    return sorted(files)

def load_positive_pairs(pos_path):
    with open(pos_path, encoding="utf-8") as f:
        data = json.load(f)

    pairs = set()
    for p in data:
        pairs.add(tuple(sorted((p["file1"], p["file2"]))))
    return pairs, len(data)

def build_negative_pairs(repo, all_files, positive_pairs, target_size):
    candidates = []

    for f1, f2 in combinations(all_files, 2):
        key = tuple(sorted((f1, f2)))
        if key not in positive_pairs:
            candidates.append(key)

    if not candidates:
        return []

    sample_size = min(target_size, len(candidates))
    sampled = random.sample(candidates, sample_size)

    negatives = []
    for f1, f2 in sampled:
        negatives.append({
            "repo": repo,
            "file1": f1,
            "file2": f2,
            "label": 0
        })

    return negatives

# ===== main =====
if __name__ == "__main__":

    for commit_json in COMMIT_DIR.glob("*_commits.json"):
        repo = commit_json.stem.replace("_commits", "")
        print(f"[PROCESS] {repo}")

        pos_path = POS_DIR / f"{repo}_cochange_pairs_am.json"
        if not pos_path.exists():
            print("  [SKIP] no positive pairs")
            continue

        # load commits
        with open(commit_json, encoding="utf-8") as f:
            commits = json.load(f)

        all_files = collect_all_java_files(commits)
        print(f"  java files = {len(all_files)}")

        positive_pairs, pos_size = load_positive_pairs(pos_path)
        print(f"  positive pairs = {pos_size}")

        negatives = build_negative_pairs(
            repo,
            all_files,
            positive_pairs,
            pos_size
        )

        out_path = OUT_DIR / f"{repo}_negative_pairs_am.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(negatives, f, indent=2, ensure_ascii=False)

        print(f"  negative pairs = {len(negatives)}")
        print("-" * 40)
