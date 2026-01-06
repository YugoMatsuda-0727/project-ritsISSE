# feature_extractor_mini.py

import pandas as pd   # pandas読み込み
import os    # OS依存のパス操作用　-> ファイル名やディレクトリ名の取得に
from difflib import SequenceMatcher    # 文字列の類似度を測るライブラリ  -> ファイル名の類似度計算に使用
import javalang    # JavaソースコードをパースしてAST作成するライブラリ

PAIRS_PATH = "file_pairs_labeled_mini.csv"   
OUTPUT_PATH = "structured_features_final_mini.csv"          # 入力・出力先の定義

def name_similarity(file1, file2):     # ファイル名類似度  (0~1)
    return SequenceMatcher(None, os.path.basename(file1), os.path.basename(file2)).ratio()

def package_similarity(file1, file2):    # パッケージ類似度　（0|1）
    return int(os.path.dirname(file1) == os.path.dirname(file2))

def ast_similarity(file1, file2):  # ASTに基づく型の類似度 (0~1)
    try:
        with open(file1, 'r', encoding='utf-8') as f:     # with open() -> file1を開く。with分は閉じる処理も自動で
            tree1 = list(javalang.parse.parse(f.read()).types)    # tree1にソースコードをパースして作成したASTを.typesでAST内のトップレベル型を取得しリスト化
        with open(file2, 'r', encoding='utf-8') as f:
            tree2 = list(javalang.parse.parse(f.read()).types)
        if not tree1 or not tree2:
            return 0.0
        return len(set(type(t).__name__ for t in tree1) & set(type(t).__name__ for t in tree2)) / max(len(tree1), len(tree2))     # 共通要素数の計算
    except:
        return 0.0    # エラーの際は0を返す

def import_similarity(file1, file2):    # importの類似度 (0~1)
    def get_imports(f):
        imports = set()
        try:
            with open(f, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith("import"):
                        imports.add(line.strip())
        except:
            pass
        return imports
    i1, i2 = get_imports(file1), get_imports(file2)
    return len(i1 & i2) / max(len(i1), len(i2)) if i1 and i2 else 0.0

def method_call_overlap(file1, file2):  # メソッド呼び出しの共通度
    def get_methods(f):
        methods = set()
        try:
            with open(f, 'r', encoding='utf-8') as f:
                tree = javalang.parse.parse(f.read())
                for path, node in tree.filter(javalang.tree.MethodInvocation):
                    methods.add(node.member)
        except:
            pass
        return methods
    m1, m2 = get_methods(file1), get_methods(file2)
    return len(m1 & m2) / max(len(m1), len(m2)) if m1 and m2 else 0.0

def class_dependency_overlap(file1, file2):    # クラス依存関係の重複度　-> 共通クラスの割合
    def get_classes(f):
        classes = set()
        try:
            with open(f, 'r', encoding='utf-8') as f:
                tree = javalang.parse.parse(f.read())
                for path, node in tree.filter(javalang.tree.ClassDeclaration):
                    classes.add(node.name)
        except:
            pass
        return classes
    c1, c2 = get_classes(file1), get_classes(file2)
    return len(c1 & c2) / max(len(c1), len(c2)) if c1 and c2 else 0.0

def main():
    df = pd.read_csv(PAIRS_PATH)    # 入力csvをデータフレームに読み込み
         # df.apply -> データフレームの各行に関数を適用  axis=処理単位
         # 無名関数を定義(lambda x) １行ごとに計算結果をdf=に渡し、列追加
    df["name_similarity"] = df.apply(lambda x: name_similarity(x["file1"], x["file2"]), axis=1)
    df["package_similarity"] = df.apply(lambda x: package_similarity(x["file1"], x["file2"]), axis=1)
    df["AST_similarity"] = df.apply(lambda x: ast_similarity(x["file1"], x["file2"]), axis=1)
    df["import_similarity"] = df.apply(lambda x: import_similarity(x["file1"], x["file2"]), axis=1)
    df["method_call_overlap"] = df.apply(lambda x: method_call_overlap(x["file1"], x["file2"]), axis=1)
    df["class_dependency_overlap"] = df.apply(lambda x: class_dependency_overlap(x["file1"], x["file2"]), axis=1)
    
    features = df[[
        "file1","file2","label",
        "name_similarity","package_similarity","AST_similarity","import_similarity",
        "method_call_overlap","class_dependency_overlap"
    ]]    # 出力用の列を整理
    
    features.to_csv(OUTPUT_PATH, index=False)    # 保存
    print(f"✅ Saved structured dataset: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
