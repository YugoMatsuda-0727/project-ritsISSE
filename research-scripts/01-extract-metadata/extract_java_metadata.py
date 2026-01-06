import re
import json
from pathlib import Path


def split_camel_case(name):
    tokens = re.findall(
        r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)',
        name
    )
    return [t.lower() for t in tokens]


def detect_class_role(class_name):
    lname = class_name.lower()
    return {
        "controller": "controller" in lname,
        "service": "service" in lname,
        "repository": "repository" in lname or "dao" in lname,
        "dto": "dto" in lname
    }


def parse_java_file(file_path: Path, project_root: Path):
    """
    1 Javaファイルから構造メタデータを抽出
    file_path は project_root からの相対パスで保存する
    """

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return None

    package_match = re.search(r'package\s+([\w\.]+);', content)
    if not package_match:
        return None
    package = package_match.group(1)

    class_match = re.search(
        r'(public\s+)?(abstract\s+)?(class|interface)\s+(\w+)',
        content
    )
    if not class_match:
        return None

    class_name = class_match.group(4)

    imports = re.findall(r'import\s+([\w\.]+);', content)
    imports = [i for i in imports if not i.startswith("java.lang")]

    method_names = re.findall(
        r'public\s+[^\s]+\s+(\w+)\s*\(',
        content
    )

    # ★★ ここが最重要修正点 ★★
    rel_path = file_path.relative_to(project_root)
    rel_path = str(rel_path).replace("\\", "/")

    return {
        "file_path": rel_path,   # ← 相対パスのみ
        "package": package,
        "package_tokens": package.split("."),

        "class_name": class_name,
        "class_name_tokens": split_camel_case(class_name),

        "class_role": detect_class_role(class_name),

        "imports": imports,
        "import_packages": list(
            set(".".join(i.split(".")[:-1]) for i in imports)
        ),

        "methods": [{"name": m} for m in method_names]
    }


def extract_project_metadata(project_root: Path, output_path: Path):
    project_root = Path(project_root)

    java_files = list(project_root.rglob("*.java"))
    results = []

    for java_file in java_files:
        # test ディレクトリ除外
        if "test" in java_file.parts:
            continue

        data = parse_java_file(java_file, project_root)
        if data:
            results.append(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[DONE] {project_root.name}: {len(results)} files")


if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parents[2]
    PROJECTS_DIR = BASE_DIR
    OUTPUT_DIR = BASE_DIR / "research-scripts" / "outputs" / "metadata"

    for project in PROJECTS_DIR.iterdir():
        if project.is_dir():
            out_file = OUTPUT_DIR / f"{project.name}.json"
            extract_project_metadata(project, out_file)
