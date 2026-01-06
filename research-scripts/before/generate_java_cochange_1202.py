import pandas as pd
import random
from itertools import combinations

INPUT_CSV = "commit_history.csv"
OUTPUT_CSV = "cochange_pairs_java.csv"

# .java に限定
VALID_EXT = (".java",)

# 目標行数（正例＋負例）
TARGET_TOTAL = 2000
TARGET_POSITIVE = TARGET_TOTAL // 2
TARGET_NEGATIVE = TARGET_TOTAL // 2


def is_valid_file(path):
    """対象ファイルかどうか（.javaのみ）"""
    return path.endswith(VALID_EXT)


def main():
    df = pd.read_csv(INPUT_CSV)

    if len(df) == 0:
        print("Error: commit_history.csv が空です")
        return

    projects = df["project"].unique()

    all_positive_pairs = []
    all_negative_pairs = []

    for proj in projects:
        df_proj = df[df["project"] == proj]

        # .java 以外は除外
        df_proj = df_proj[df_proj["file_path"].apply(is_valid_file)]

        if len(df_proj) == 0:
            continue  # Java ファイルがないプロジェクトはスキップ

        # commit_id 単位でファイル群を取り出す
        commit_groups = df_proj.groupby("commit_id")["file_path"].apply(list)

        positive_pairs = []

        # ---- 1) 正例（共変更ペア） ----
        for commit_id, files in commit_groups.items():
            java_files = [f for f in files if is_valid_file(f)]
            if len(java_files) < 2:
                continue
            for f1, f2 in combinations(java_files, 2):
                positive_pairs.append([proj, f1, f2, 1])

        # ---- 2) 負例（非共変更ペア） ----
        all_files = df_proj["file_path"].unique().tolist()

        # 正例セット（重複防止用）
        positive_set = {(p[1], p[2]) for p in positive_pairs}
        positive_reverse = {(p[2], p[1]) for p in positive_pairs}

        negative_candidates = []
        for f1, f2 in combinations(all_files, 2):
            if (f1, f2) not in positive_set and (f1, f2) not in positive_reverse:
                negative_candidates.append([proj, f1, f2, 0])

        # 正例と負例をシャッフルして均等に
        random.shuffle(positive_pairs)
        random.shuffle(negative_candidates)

        # このプロジェクト分だけ追加
        all_positive_pairs.extend(positive_pairs)
        all_negative_pairs.extend(negative_candidates)

    # ---- 3) 全体で 2000 行に制限 ----
    random.shuffle(all_positive_pairs)
    random.shuffle(all_negative_pairs)

    selected_positive = all_positive_pairs[:TARGET_POSITIVE]
    selected_negative = all_negative_pairs[:TARGET_NEGATIVE]

    pairs = selected_positive + selected_negative
    random.shuffle(pairs)

    df_out = pd.DataFrame(pairs, columns=["project", "file1", "file2", "label"])
    df_out.to_csv(OUTPUT_CSV, index=False)

    print(f"✔ Positive: {len(selected_positive)}  Negative: {len(selected_negative)}")
    print(f"✔ Total: {len(df_out)} saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
