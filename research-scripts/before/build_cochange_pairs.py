import json
from pathlib import Path
from itertools import combinations

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
COMMIT_DIR = BASE_DIR / "outputs" / "commit_logs"
OUT_DIR = BASE_DIR / "outputs" / "cochange_pairs"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== 設定 =====
ALLOWED_TYPES = {"A", "M"}
MAX_FILES_PER_COMMIT = 50   # 爆発防止
TARGET_EXT = ".java"

def extract_am_files(commit):
    files = []
    for ch in commit["changes"]:
        if ch["type"] in ALLOWED_TYPES and ch["file"].endswith(TARGET_EXT):
            files.append(ch["file"])
    return files

def build_pairs(repo_name, commits):
    pairs = []

    for c in commits:
        files = extract_am_files(c)

        if len(files) < 2:
            continue

        # 巨大コミット除外
        if len(files) > MAX_FILES_PER_COMMIT:
            continue

        for f1, f2 in combinations(sorted(files), 2):
            pairs.append({
                "repo": repo_name,
                "commit": c["commit"],
                "file1": f1,
                "file2": f2,
                "label": 1
            })

    return pairs

# ===== main =====
if __name__ == "__main__":

    json_files = list(COMMIT_DIR.glob("*_commits.json"))
    print(f"[DEBUG] files = {json_files}")

    for jf in json_files:
        repo = jf.stem.replace("_commits", "")
        print(f"[PROCESS] {repo}")

        with open(jf, encoding="utf-8") as f:
            commits = json.load(f)

        pairs = build_pairs(repo, commits)

        out_path = OUT_DIR / f"{repo}_cochange_pairs_am.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(pairs, f, indent=2, ensure_ascii=False)

        print(f"[DONE] {repo}: {len(pairs)} positive pairs")
