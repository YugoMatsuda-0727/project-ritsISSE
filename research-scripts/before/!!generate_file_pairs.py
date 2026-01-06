# generate_file_pairs.py
import pandas as pd
from itertools import combinations          # 組み合わせ出力
import os
import random

INPUT_CSV = "all_java_files.csv"
OUTPUT_CSV = "file_pairs_labeled_mini.csv"


MAX_PAIRS_PER_PROJECT = 1000  # プロジェクト内で作るペアの上限
NEGATIVE_RATIO = 1.0  # ラベル0と1の比率

def main():
    df_files = pd.read_csv(INPUT_CSV)
    files = df_files["file_path"].tolist()

    # ファイル → プロジェクト名の対応
    project_dict = {}
    for f in files:
        project_name = os.path.normpath(f).split(os.sep)[-2]  # プロジェクト名は parent directory
        project_dict[f] = project_name

    # プロジェクトごとのファイルリスト
    project_files = {}
    for f, proj in project_dict.items():
        project_files.setdefault(proj, []).append(f)

    pairs = []

    # ==============================
    # 同プロジェクトペア作成
    # ==============================
    for proj, flist in project_files.items():
        combos = list(combinations(flist, 2))
        random.shuffle(combos)
        combos = combos[:MAX_PAIRS_PER_PROJECT]  # 上限
        for f1, f2 in combos:
            pairs.append([f1, f2, 1])  # ラベル1

    # ==============================
    # 異プロジェクトペア作成
    # ==============================
    proj_names = list(project_files.keys())
    negative_pairs = []
    for i in range(len(proj_names)):
        for j in range(i + 1, len(proj_names)):
            f1_list = project_files[proj_names[i]]
            f2_list = project_files[proj_names[j]]
            combos = list(combinations(f1_list + f2_list, 2))
            # 同プロジェクトの組み合わせを除外
            combos = [c for c in combos if project_dict[c[0]] != project_dict[c[1]]]
            random.shuffle(combos)
            max_neg = min(len(combos), int(MAX_PAIRS_PER_PROJECT * NEGATIVE_RATIO))
            negative_pairs.extend(combos[:max_neg])

    random.shuffle(negative_pairs)
    pairs.extend(negative_pairs)

    # ==============================
    # CSV出力
    # ==============================
    df_pairs = pd.DataFrame(pairs, columns=["file1", "file2", "label"])
    df_pairs.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved {len(pairs)} file pairs to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

    