from dataclasses import fields
import re
import json
from pathlib import Path

try:
    import javalang
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False
    print("[WARN] javalang が見つかりません。AST特徴量はスキップされます。")

# クラス名をキャメルケースで分割して小文字化する
def split_camel_case(name):
    tokens = re.findall(
        r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)',
        name
    )
    return [t.lower() for t in tokens]


# ===== AST解析 =====
def parse_ast_features(content: str) -> dict:

    empty = {
        "fields": [],
        "superclass": None,
        "interfaces": [],
        "param_types": [],
        "instantiated_classes": [], # インスタンス化されているクラス
        "field_types": [],  # フィールドの型
        "called_methods": [],  # [{"method": "...", "viatype": "..."}, ...] 呼び出されているメソッドと呼び出し方法（直接呼び出し、インスタンス経由、static経由など）
        "class_annotations": [],      # クラス直上のアノテーション
        "method_annotations": [],     # メソッド直上のアノテーション
        "field_annotations": [],      # フィールド直上のアノテーション
        "param_annotations": [],      # 引数直上のアノテーション
        "all_annotations": [],        # ファイル内の全アノテーションのユニークリスト
    }

    if not AST_AVAILABLE:
        return empty

    try:
        tree = javalang.parse.parse(content)
    except Exception:
        # 構文エラー等でパースできない場合はスキップ
        return empty

    fields = []
    field_types = []
    superclass = None
    interfaces = []
    param_types = []
    instantiated_classes = []
    called_methods = []
    class_annotations = []
    method_annotations = []
    field_annotations = []
    param_annotations = []
    all_annotations_set = set()

    for _, node in tree:
        # 1. クラス定義、またはインターフェース定義（及びその直上のアノテーション）
        if isinstance(node, javalang.tree.ClassDeclaration):
            # クラスの場合
            if node.extends:
                superclass = node.extends.name
            if node.implements:
                interfaces = [i.name for i in node.implements]
            
            # クラス直上のアノテーション
            if node.annotations:
                for anno in node.annotations:
                    class_annotations.append(anno.name)
                    all_annotations_set.add(anno.name)

        elif isinstance(node, javalang.tree.InterfaceDeclaration):
            # インターフェースの場合（extendsで他のインターフェースを複数継承できる）
            if node.extends:
                # node.extends は通常 list (ReferenceTypeのリスト) になります
                if isinstance(node.extends, list):
                    interfaces.extend([ext.name for ext in node.extends])
                else:
                    interfaces.append(node.extends.name)
            
            # インターフェース直上のアノテーション
            if node.annotations:
                for anno in node.annotations:
                    class_annotations.append(anno.name)
                    all_annotations_set.add(anno.name)

        # 2. フィールド変数名（及びその直上のアノテーション）
        elif isinstance(node, javalang.tree.FieldDeclaration):
            for declarator in node.declarators:
                fields.append(declarator.name)
                field_types.append(node.type.name)
            
            # フィールド直上のアノテーションを抽出
            if node.annotations:
                for anno in node.annotations:
                    field_annotations.append(anno.name)
                    all_annotations_set.add(anno.name)

        # 3. メソッド定義（及びその直上のアノテーション、引数アノテーション）
        elif isinstance(node, javalang.tree.MethodDeclaration):
            for param in node.parameters:
                param_types.append(param.type.name)
                # 引数直上のアノテーションを抽出 (例: @RequestParam, @PathVariable)
                if param.annotations:
                    for anno in param.annotations:
                        param_annotations.append(anno.name)
                        all_annotations_set.add(anno.name)
            
            # メソッド直上のアノテーションを抽出
            if node.annotations:
                for anno in node.annotations:
                    method_annotations.append(anno.name)
                    all_annotations_set.add(anno.name)

        # 4. コンストラクタ定義（引数アノテーション等のため）
        elif isinstance(node, javalang.tree.ConstructorDeclaration):
            for param in node.parameters:
                param_types.append(param.type.name)
                if param.annotations:
                    for anno in param.annotations:
                        param_annotations.append(anno.name)
                        all_annotations_set.add(anno.name)
            if node.annotations:
                for anno in node.annotations:
                    method_annotations.append(anno.name)
                    all_annotations_set.add(anno.name)

        # 5. インスタンス化されているクラス
        elif isinstance(node, javalang.tree.ClassCreator):
            instantiated_classes.append(node.type.name)
    
    # フィールドの「変数名：型名」の対応を作る
    field_type_map = {}
    for _, node in tree:
        if isinstance(node, javalang.tree.FieldDeclaration):
            for declarator in node.declarators:
                field_type_map[declarator.name] = node.type.name

    for _, method_node in tree:
        if not isinstance(method_node, javalang.tree.MethodDeclaration):
            continue

        for param in method_node.parameters:
            param_types.append(param.type.name)

        scope_map = dict(field_type_map)  # フィールドの型情報をスコープに追加

        for param in method_node.parameters:
            scope_map[param.name] = param.type.name

        for _, local_node in method_node:
            if isinstance(local_node, javalang.tree.LocalVariableDeclaration):
                for declarator in local_node.declarators:
                    scope_map[declarator.name] = local_node.type.name

        for _, call_node in method_node:
            if isinstance(call_node, javalang.tree.MethodInvocation):
                qualifier = call_node.qualifier
                if qualifier and qualifier in scope_map:
                    called_methods.append({
                        "method": call_node.member,
                        "viatype": scope_map[qualifier]  # 変数の型を呼び出し方法として記録
                    })

    return {
        "fields": fields,
        "superclass": superclass,
        "interfaces": interfaces,
        "param_types": param_types,
        "instantiated_classes": instantiated_classes,
        "field_types": field_types,
        "field_type_map": field_type_map,
        "called_methods": called_methods,
        "class_annotations": class_annotations,
        "method_annotations": method_annotations,
        "field_annotations": field_annotations,
        "param_annotations": param_annotations,
        "all_annotations": list(set(class_annotations + method_annotations + field_annotations + param_annotations))
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

    rel_path = file_path.relative_to(project_root)
    rel_path = str(rel_path).replace("\\", "/")

    # ===== AST特徴量を追加 =====
    ast_features = parse_ast_features(content)

    return {
        "file_path": rel_path,
        "package": package,
        "package_tokens": package.split("."),

        "class_name": class_name,
        "class_name_tokens": split_camel_case(class_name),

        "imports": imports,
        "import_packages": list(
            set(".".join(i.split(".")[:-1]) for i in imports)
        ),

        "methods": [{"name": m} for m in method_names],

        # ===== 以下がASTで追加した特徴量 =====
        "fields": ast_features["fields"],
        "superclass": ast_features["superclass"],
        "interfaces": ast_features["interfaces"],
        "param_types": ast_features["param_types"],
        "instantiated_classes": ast_features["instantiated_classes"],
        "field_types": ast_features["field_types"],
        "called_methods": ast_features["called_methods"],
        "class_annotations": ast_features["class_annotations"],
        "method_annotations": ast_features["method_annotations"],
        "field_annotations": ast_features["field_annotations"],
        "param_annotations": ast_features["param_annotations"],
        "all_annotations": list(set(
            ast_features["class_annotations"] +
            ast_features["method_annotations"] +
            ast_features["field_annotations"] +
            ast_features["param_annotations"]
        ))
    }


def extract_project_metadata(project_root: Path, output_path: Path):
    project_root = Path(project_root)

    java_files = list(project_root.rglob("*.java"))
    results = []
    skipped_ast = 0

    for java_file in java_files:
        if "test" in java_file.parts:
            continue

        data = parse_java_file(java_file, project_root)
        if data:
            if not data["fields"] and not data["superclass"] and not data["interfaces"]:
                skipped_ast += 1
            results.append(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[DONE] {project_root.name}: {len(results)} files (AST空白: {skipped_ast})")


if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parents[2]
    PROJECTS_DIR = BASE_DIR
    OUTPUT_DIR = BASE_DIR / "research-scripts" / "outputs" / "metadata"

    for project in PROJECTS_DIR.iterdir():
        if project.is_dir():
            out_file = OUTPUT_DIR / f"{project.name}.json"
            extract_project_metadata(project, out_file)