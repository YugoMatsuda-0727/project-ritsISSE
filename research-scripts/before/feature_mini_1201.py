# feature_mini_1201.py
import pandas as pd
import os
import javalang

def build_dataset(pairs_csv, output_csv, project_root):
    # CSV読み込み
    df_pairs = pd.read_csv(pairs_csv)
    
    # 列名を正規化
    df_pairs.columns = df_pairs.columns.str.strip().str.lower()
    for col in ["project", "file1", "file2", "label"]:
        if col not in df_pairs.columns:
            raise ValueError(f"CSVに必要な列がありません: {df_pairs.columns.tolist()}")

    dataset = []

    # 各ペアに対して特徴量を計算
    for _, row in df_pairs.iterrows():
        project = row["project"]
        file1_rel = row["file1"]
        file2_rel = row["file2"]
        label = row["label"]

        # 絶対パスを作成
        file1_abs = os.path.join(project_root, project, file1_rel)
        file2_abs = os.path.join(project_root, project, file2_rel)

        # ファイル存在確認
        if not os.path.exists(file1_abs) or not os.path.exists(file2_abs):
            continue

        # import 類似度
        def get_imports(f):
            imports = set()
            try:
                with open(f, 'r', encoding='utf-8') as fin:
                    for line in fin:
                        if line.strip().startswith("import"):
                            imports.add(line.strip())
            except:
                pass
            return imports

        i1, i2 = get_imports(file1_abs), get_imports(file2_abs)
        import_sim = len(i1 & i2) / max(len(i1), len(i2)) if i1 and i2 else 0.0

        # メソッド名共通度
        def get_methods(f):
            methods = set()
            try:
                with open(f, 'r', encoding='utf-8') as fin:
                    tree = javalang.parse.parse(fin.read())
                    for _, node in tree.filter(javalang.tree.MethodDeclaration):
                        methods.add(node.name)
            except:
                pass
            return methods

        m1, m2 = get_methods(file1_abs), get_methods(file2_abs)
        method_sim = len(m1 & m2) / max(len(m1), len(m2)) if m1 and m2 else 0.0

        dataset.append({
            "file1": file1_rel,
            "file2": file2_rel,
            "import_similarity": import_sim,
            "method_similarity": method_sim,
            "label": label
        })

    # データフレームに変換して出力
    df_dataset = pd.DataFrame(dataset)
    df_dataset.to_csv(output_csv, index=False)
    print(f"✅ Saved dataset with {len(df_dataset)} rows to {output_csv}")


if __name__ == "__main__":
    build_dataset(
        pairs_csv="cochange_pairs.csv",
        output_csv="dataset_minimal_fixed.csv",
        project_root="C:/Users/07yug/OneDrive/Desktop/project/java-data"
    )

