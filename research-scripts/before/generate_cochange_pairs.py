# generate_cochange_pairs_small.py

import pandas as pd
import random
from itertools import combinations
import os

INPUT_CSV = "commit_history.csv"
OUTPUT_CSV = "cochange_pairs.csv"

MAX_POS = 1000   # 正例の最大数
MAX_NEG = 1000   # 負例の最大数

def main():
    df = pd.read_csv(INPUT_CSV)

    if len(df) == 0:
        print("Error: commit_history.csv が空です")
        return

    projects = df["project"].unique()

    positive_pairs = []
    negative_pairs = []

    for proj in projects:
        if len(positive_pairs) >= MAX_POS:
            break   # 既に十分集まった

        df_proj = df[df["project"] == proj]

        # コミットごとにファイルをまとめる
        commit_groups = df_proj.groupby("commit_id")["file_path"].apply(list)

        # --- 正例生成 ---
        for commit_id, files in commit_groups.items():
            if len(files) < 2:
                continue

            for f1, f2 in combinations(files, 2):
                positive_pairs.append([proj, f1, f2, 1])

                if len(positive_pairs) >= MAX_POS:
                    break

            if len(positive_pairs) >= MAX_POS:
                break

        # --- 負例生成 ---
        if len(positive_pairs) > 0:
            all_files = df_proj["file_path"].unique().tolist()

            pos_set = {(p[1], p[2]) for p in positive_pairs if p[0] == proj}
            pos_rev = {(p[2], p[1]) for p in positive_pairs if p[0] == proj}

            neg_candidates = []
            for f1, f2 in combinations(all_files, 2):
                if (f1, f2) not in pos_set and (f1, f2) not in pos_rev:
                    neg_candidates.append([proj, f1, f2, 0])

            random.shuffle(neg_candidates)

            needed = MAX_NEG - len(negative_pairs)
            negative_pairs.extend(neg_candidates[:needed])

        print(f"📌 {proj}: 正例={len(positive_pairs)}, 負例={len(negative_pairs)}")

    # 最終スライス（念のため）
    positive_pairs = positive_pairs[:MAX_POS]
    negative_pairs = negative_pairs[:MAX_NEG]

    pairs = positive_pairs + negative_pairs

    df_out = pd.DataFrame(pairs, columns=["project", "file1", "file2", "label"])
    df_out.to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Final: 正例={len(positive_pairs)}, 負例={len(negative_pairs)} → 合計 {len(df_out)} 行 Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

