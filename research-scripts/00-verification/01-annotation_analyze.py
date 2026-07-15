import os
import json
from collections import Counter
from matplotlib import Path
import pandas as pd  # 結果を綺麗に出力・保存するために使用します

def analyze_project_annotations(metadata_dir, save_dir):
    """
    metadata_dir 配下にあるすべての .json ファイルを読み込み、
    プロジェクトごとにアノテーションの出現回数を集計し、save_dir に保存します。
    """
    if not os.path.exists(metadata_dir):
        print(f"[Error] ディレクトリが見つかりません: {metadata_dir}")
        return

    # 対象となるJSONファイルを取得
    json_files = [f for f in os.listdir(metadata_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"No JSON files found in {metadata_dir}")
        return

    print(f"=== アノテーション集計開始 (対象ファイル数: {len(json_files)}) ===")

    all_results = {}

    for file_name in json_files:
        project_name = os.path.splitext(file_name)[0]
        
        # 1. 隠しファイルやシステム用フォルダ (.git, .vscode など) は集計からスキップする
        if project_name.startswith('.'):
            continue
            
        file_path = os.path.join(metadata_dir, file_name)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
        except Exception as e:
            print(f"  [Error] {file_name} の読み込みに失敗しました: {e}")
            continue

        # 2. JSONの中身がリスト形式でない、または空の場合は安全にスキップする
        if not isinstance(data_list, list):
            print(f"  [Warning] {file_name} のデータ形式がリストではないためスキップします。")
            continue

        annotation_counter = Counter()

        for file_entry in data_list:
            # 3. リストの中身が辞書型（dict）ではない場合を安全に回避
            if not isinstance(file_entry, dict):
                continue

            annos_keys = [
                "class_annotations",
                "method_annotations",
                "field_annotations",
                "param_annotations"
            ]
            
            for key in annos_keys:
                annos_list = file_entry.get(key, [])
                # もしキーが存在して、かつリストの場合のみ処理する
                if isinstance(annos_list, list):
                    for anno in annos_list:
                        annotation_counter[anno] += 1

        all_results[project_name] = annotation_counter

        print(f"\n📁 プロジェクト: {project_name}")
        if not annotation_counter:
            print("  (アノテーションは検出されませんでした)")
        else:
            for anno, count in annotation_counter.most_common(10):
                print(f"  - @{anno}: {count} 回")
            if len(annotation_counter) > 10:
                print(f"  ...他 {len(annotation_counter) - 10} 種類のアノテーション")

    # --- 保存先を save_dir に変更して呼び出し ---
    save_results(all_results, save_dir)


def save_results(all_results, output_dir):
    """
    集計結果をCSVおよびJSON形式で保存します。
    """
    # 保存先ディレクトリが存在しない場合は自動で作成する
    os.makedirs(output_dir, exist_ok=True)

    # 1. 扱いやすいように辞書形式でJSON保存
    json_output_path = os.path.join(output_dir, "annotation_summary.json")
    serializable_results = {proj: dict(counter) for proj, counter in all_results.items()}
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=4, ensure_ascii=False)
    
    # 2. 横並びの表（DataFrame）にしてCSV保存
    # 行：アノテーション名、列：プロジェクト名、値：出現回数
    df = pd.DataFrame(serializable_results).fillna(0).astype(int)
    csv_output_path = os.path.join(output_dir, "annotation_summary.csv")
    df.to_csv(csv_output_path, encoding='utf-8-sig')

    print("\n=========================================")
    print(f"[保存完了] 詳細な集計結果を保存しました：")
    print(f"  - JSON形式: {json_output_path}")
    print(f"  - CSV形式 (マトリックス): {csv_output_path}")
    print("=========================================")


if __name__ == "__main__":
    # 各種パスを指定
    BASE_DIR = Path(__file__).resolve().parents[1]
    
    # 読み込み元は outputs/metadata のまま
    METADATA_DIR = BASE_DIR / "outputs" / "metadata"
    
    # 保存先を outputs/annotation_sample に変更
    SAVE_DIR = BASE_DIR / "outputs" / "annotation_sample"
    
    # 読み込み元（METADATA_DIR）から集計し、保存先（SAVE_DIR）を指定して実行
    analyze_project_annotations(METADATA_DIR, SAVE_DIR)