# extract_java_metadata.py

import re                     # 正規表現
import json                   # 抽出結果をJSONで保存
from pathlib import Path      # ファイル・ディレクトリ操作用

def split_camel_case(name):
    tokens = re.findall(
        r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)',
        name
    )
    return [t.lower() for t in tokens]                                    # 大文字単位でトークン分割し出力


def detect_class_role(class_name):                                        # 設計レイヤ：Controller, Service, Repositoryクラス名を抽出
    lname = class_name.lower()
    return {
        "controller": "controller" in lname,
        "service": "service" in lname,
        "repository": "repository" in lname or "dao" in lname,
        "dto": "dto" in lname
    }

def parse_java_file(file_path):                                          # ファイル解析

    with open(file_path, encoding="utf-8", errors="ignore") as f:        # エラーを無視してエンコード
        content = f.read()

    package_match = re.search(r'package\s+([\w\.]+);', content)          # パッケージ抽出
    if not package_match:
        return None
    package = package_match.group(1)

    class_match = re.search(                                             # public class/interface抽出
        r'(public\s+)?(abstract\s+)?(class|interface)\s+(\w+)',
        content
    )
    if not class_match:
        return None

    class_name = class_match.group(4)                                   # クラス名属性

    imports = re.findall(r'import\s+([\w\.]+);', content)               # import抽出
    imports = [i for i in imports if not i.startswith("java.lang")]     

    method_names = re.findall(                                          # メソッド名
        r'public\s+[^\s]+\s+(\w+)\s*\(',
        content
    )

    return {                                                           # ファイルの構造情報
        "file_path": str(file_path),
        "package": package,
        "package_tokens": package.split("."),

        "class_name": class_name,
        "class_name_tokens": split_camel_case(class_name),

        "class_role": detect_class_role(class_name),

        "imports": imports,
        "import_packages": list(set(".".join(i.split(".")[:-1]) for i in imports)),

        "methods": [{"name": m} for m in method_names]
    }

def extract_project_metadata(project_root, output_path):

    project_root = Path(project_root)                                # パス

    java_files = list(project_root.rglob("*.java"))                  # .java探索

    results = []                                                     # 結果格納用リスト

    for java_file in java_files:
        # test除外（あとでon/off可能）
        if "test" in java_file.parts:
            continue

        data = parse_java_file(java_file)                           # 解析(package, class, import, method, )
        if data:
            results.append(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)                            # JSONとして保存

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parents[2]
    PROJECTS_DIR = BASE_DIR 
    OUTPUT_DIR = BASE_DIR / "research-scripts" / "outputs" / "metadata"

    for project in PROJECTS_DIR.iterdir():
        if project.is_dir():
            out_file = OUTPUT_DIR / f"{project.name}.json"
            extract_project_metadata(project, out_file)
            print(f"[DONE] {project.name}")

            