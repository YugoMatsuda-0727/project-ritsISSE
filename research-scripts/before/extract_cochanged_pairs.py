# extract_cochanged_pairs.py
import pandas as pd
from itertools import combinations
import random

COMMIT_CSV = "commit_history.csv"
OUTPUT_CSV = "file_pairs_labeled.csv"
MAX_PAIRS_PER_PROJECT = 1000
LABEL_RATIO = 0.5

df = pd.read_csv(COMMIT_CSV)
pairs = []

for proj, g in df.groupby("project"):
    # コミットごとに同時変更ファイルの組み合わせ
    co_changed = set()
    for commit_id, commit_group in g.groupby("commit_id"):
        files = commit_group["file_path"].tolist()
        combos = list(combinations(files, 2))
        co_changed.update(combos)

    co_changed = list(co_changed)
    random.shuffle(co_changed)
    co_changed = co_changed[:MAX_PAIRS_PER_PROJECT]

    # ラベル付け（共変更=1, 非共変更=0）
    n = len(co_changed)
    label_1_pairs = [[f1, f2, 1] for f1, f2 in co_changed]
    label_0_pairs = [[f1, f2, 0] for f1, f2 in random.sample(co_changed, n)]

    pairs.extend(label_1_pairs + label_0_pairs)

df_pairs = pd.DataFrame(pairs, columns=["file1", "file2", "label"])
df_pairs.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Saved {len(pairs)} file pairs to {OUTPUT_CSV}")

