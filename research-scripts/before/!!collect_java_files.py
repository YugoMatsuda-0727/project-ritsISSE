# collect_java_files.py
import os             # ->パス使う
import pandas as pd   # ->csv読み込み

# 複数プロジェクトのルートディレクトリ
projects = [
    r"C:\Users\07yug\OneDrive\Desktop\project\java-data\awaitility",
    r"C:\Users\07yug\OneDrive\Desktop\project\java-data\ByteLegend",
    r"C:\Users\07yug\OneDrive\Desktop\project\java-data\immutables",
    r"C:\Users\07yug\OneDrive\Desktop\project\java-data\java-design-patterns",
    r"C:\Users\07yug\OneDrive\Desktop\project\java-data\leet-code"
]  

java_files = []                                         # ->保存先ファイル定義

for proj_dir in projects:
    for root, dirs, files in os.walk(proj_dir):            # ->.javaを抽出しリスト化
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))  # 末尾にpath書き込み

# 結果をデータフレームにして保存
df = pd.DataFrame(java_files, columns=["file_path"])
df.to_csv("all_java_files.csv", index=False)                # index(行番号)を省略
print(f"Collected {len(java_files)} java files across {len(projects)} projects")
print("✅ Saved all_java_files.csv")

