import subprocess
import json
from pathlib import Path

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[2]        # java-data/
OUTPUT_DIR = BASE_DIR / "research-scripts" / "outputs" / "commit_logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_git_log(repo_dir: Path):
    """
    git log から
    commit hash / 変更種別(A,M,D) / ファイルパス
    を取得する（v1: 同一コミット内共変更用）
    """

    cmd = [
        "git", "log",
        "--name-status",
        "--pretty=format:commit %H"
    ]

    result = subprocess.run(
        cmd,
        cwd=repo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"
    )

    if result.returncode != 0:
        print(f"[SKIP] git log failed: {repo_dir.name}")
        return []

    return result.stdout.splitlines()


def parse_git_log(lines):
    """
    git log の出力を
    [
      {
        commit: "...",
        changes: [
          {type: "M", file: "src/..."}, ...
        ]
      }
    ]
    に変換
    """

    commits = []
    current = None

    for line in lines:
        if line.startswith("commit "):
            if current:
                commits.append(current)
            current = {
                "commit": line.split()[1],
                "changes": []
            }

        elif line and current:
            parts = line.split("\t")
            if len(parts) == 2:
                change_type, file_path = parts
                if file_path.endswith(".java"):
                    current["changes"].append({
                        "type": change_type,   # A / M / D
                        "file": file_path
                    })

    if current:
        commits.append(current)

    return commits


def process_repository(repo_dir: Path):
    print(f"[REPO] {repo_dir.name}")

    lines = get_git_log(repo_dir)
    if not lines:
        return

    commits = parse_git_log(lines)

    out_path = OUTPUT_DIR / f"{repo_dir.name}_commits.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(commits, f, indent=2)

    print(f"[DONE] {repo_dir.name}: {len(commits)} commits")


# ===== main =====
if __name__ == "__main__":

    for repo_dir in BASE_DIR.iterdir():
        if not repo_dir.is_dir():
            continue

        if not (repo_dir / ".git").exists():
            continue

        process_repository(repo_dir)
