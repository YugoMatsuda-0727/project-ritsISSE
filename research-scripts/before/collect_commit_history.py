# collect_commit_history.py
import subprocess
import pandas as pd
import os

PROJECTS = [
    "awaitility", "ByteLegend", "immutables", "java-design-patterns", "leet-code"
]

OUTPUT_CSV = "commit_history.csv"
MAX_COMMITS = 100

all_commits = []

base_dir = os.path.abspath("..")  # java-data ディレクトリ

print(f" Base dir: {base_dir}")

for proj in PROJECTS:
    repo_path = os.path.join(base_dir, proj)

    print(f" Reading repo: {repo_path}")

    cmd = [
        "git", "-C", repo_path,
        "log", f"-n{MAX_COMMITS}",
        "--name-only", "--pretty=format:COMMIT:%H"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        print(f" Error in {proj}:", result.stderr)
        continue

    lines = result.stdout.splitlines()
    current_commit = None

    for line in lines:
        line = line.strip()

        if line.startswith("COMMIT:"):
            current_commit = line.replace("COMMIT:", "")
        elif line and current_commit:
            all_commits.append([proj, current_commit, line])

df = pd.DataFrame(all_commits, columns=["project", "commit_id", "file_path"])
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f" Saved commit history: {OUTPUT_CSV}")
print(f" Total rows: {len(df)}")
