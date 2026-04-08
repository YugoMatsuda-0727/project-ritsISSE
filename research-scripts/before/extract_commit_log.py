import subprocess
import csv
from pathlib import Path

# ===== 設定 =====
REPO_DIR = Path(r"C:\Users\07yug\OneDrive\Desktop\project\java-data\awaitility")   # ← 各プロジェクトごとに変更
if not REPO_DIR.exists():
    raise RuntimeError(f"REPO_DIR does not exist: {REPO_DIR}")

if not (REPO_DIR / ".git").exists():
    raise RuntimeError(f"Not a git repository: {REPO_DIR}")

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "commits"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / f"{REPO_DIR.name}_commits.csv"

# ===== git log 実行 =====
def get_git_log(repo_dir):
    cmd = [
        "git",
        "log",
        "--name-status",
        "--pretty=format:%H,%cI"
    ]
    result = subprocess.run(
        cmd,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout.splitlines()

# ===== パース =====
def parse_git_log(lines):
    rows = []
    current_commit = None
    current_time = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "," in line and len(line.split(",")[0]) == 40:
            current_commit, current_time = line.split(",", 1)
            continue

        if line[0] in {"A", "M", "D"}:
            change_type, path = line.split(maxsplit=1)

            if not path.endswith(".java"):
                continue

            rows.append([
                current_commit,
                current_time,
                path,
                change_type
            ])

    return rows

# ===== main =====
if __name__ == "__main__":
    print(f"[REPO] {REPO_DIR.name}")

    lines = get_git_log(REPO_DIR)
    rows = parse_git_log(lines)

    if not rows:
        print("[WARN] no java changes found")
        exit()

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "commit_hash",
            "commit_time",
            "file_path",
            "change_type"
        ])
        writer.writerows(rows)

    print(f"[DONE] {OUT_CSV} ({len(rows)} rows)")
