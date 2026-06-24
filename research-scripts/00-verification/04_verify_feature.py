import json
from pathlib import Path
from collections import defaultdict

# ===== パス設定 =====
BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE_DIR / "outputs" / "datasets_with_features"
OUTPUT_DIR = BASE_DIR / "outputs" / "verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 検証対象の特徴量
JACCARD_FEATURES = [
    "package_similarity",
    "class_name_similarity",
    "import_similarity",
    "method_similarity",
    "field_similarity",
    "interface_similarity",
    "param_type_similarity",
]

BINARY_FEATURES = [
    "superclass_match",
    "class_name_suffix_match",
    "direct_import",
    "uses_dependency",
    "inheritance_dependency",
    "method_call_dependency",
]

ALL_FEATURES = JACCARD_FEATURES + BINARY_FEATURES

THRESHOLD = 0.25  # positive_rate の閾値


# ===== データ読み込み =====
def load_all_datasets(input_dir: Path) -> list:
    all_pairs = []
    for json_file in input_dir.glob("*_dataset_with_features.json"):
        with open(json_file, encoding="utf-8") as f:
            pairs = json.load(f)
        for pair in pairs:
            pair["_project"] = json_file.stem.replace("_dataset_with_features", "")
        all_pairs.extend(pairs)
        print(f"  [LOAD] {json_file.name}: {len(pairs)} pairs")
    return all_pairs


# ===== 統計計算 =====
def calc_stats(values: list) -> dict:
    if not values:
        return {"count": 0, "mean": 0.0, "positive_rate": 0.0}
    n = len(values)
    mean = sum(values) / n
    positive = sum(1 for v in values if float(v) > THRESHOLD)
    return {
        "count": n,
        "mean": round(mean, 4),
        "positive_rate": round(positive / n * 100, 2),
    }


# ===== 差の計算 =====
def calc_diff(s1: dict, s0: dict) -> float:
    return round(s1["positive_rate"] - s0["positive_rate"], 2)


# ===== 特徴量ごとに co_changed=1 vs 0 を比較（全体） =====
def verify_features(pairs: list) -> dict:
    group = defaultdict(list)
    for pair in pairs:
        label = str(pair.get("co_changed", "0"))
        group[label].append(pair)

    changed     = group["1"]
    not_changed = group["0"]

    print(f"\n総ペア数       : {len(pairs)}")
    print(f"co_changed=1   : {len(changed)}")
    print(f"co_changed=0   : {len(not_changed)}")

    results = {}
    for feat in ALL_FEATURES:
        vals_1 = [float(p[feat]) for p in changed     if feat in p]
        vals_0 = [float(p[feat]) for p in not_changed if feat in p]

        s1 = calc_stats(vals_1)
        s0 = calc_stats(vals_0)

        results[feat] = {
            "co_changed_1":       s1,
            "co_changed_0":       s0,
            "diff_positive_rate": calc_diff(s1, s0),
        }

    return results


# ===== プロジェクト別の集計 =====
def verify_by_project(pairs: list) -> dict:
    by_project = defaultdict(list)
    for pair in pairs:
        by_project[pair["_project"]].append(pair)

    project_results = {}
    for proj, proj_pairs in by_project.items():
        changed     = [p for p in proj_pairs if str(p.get("co_changed")) == "1"]
        not_changed = [p for p in proj_pairs if str(p.get("co_changed")) == "0"]

        # 特徴量ごとの差をこのプロジェクトのペアだけで計算する
        feat_diff = {}
        for feat in ALL_FEATURES:
            vals_1 = [float(p[feat]) for p in changed     if feat in p]
            vals_0 = [float(p[feat]) for p in not_changed if feat in p]
            s1 = calc_stats(vals_1)
            s0 = calc_stats(vals_0)
            feat_diff[feat] = {
                "rate_1": s1["positive_rate"],
                "rate_0": s0["positive_rate"],
                "diff":   calc_diff(s1, s0),
            }

        project_results[proj] = {
            "total":               len(proj_pairs),
            "co_changed_1":        len(changed),
            "co_changed_0":        len(not_changed),
            "positive_rate_label": round(len(changed) / len(proj_pairs) * 100, 2) if proj_pairs else 0,
            "feat_diff":           feat_diff,
        }

    return project_results


# ===== レポート出力 =====
def print_and_save_report(results: dict, project_results: dict, output_path: Path):
    lines = []

    lines.append("=" * 70)
    lines.append("検証結果（差ベース）")
    lines.append("=" * 70)

    # ===== プロジェクト別サマリー（ペア数） =====
    lines.append("\n[プロジェクト別ペア数]")
    lines.append(f"{'プロジェクト':<30} {'総数':>6} {'co_change=1':>10} {'co_change=0':>10} {'正例率(%)':>9}")
    lines.append("-" * 70)
    for proj, s in sorted(project_results.items()):
        lines.append(
            f"{proj:<30} {s['total']:>6} {s['co_changed_1']:>10} "
            f"{s['co_changed_0']:>10} {s['positive_rate_label']:>9}"
        )

    # ===== プロジェクト別・特徴量別の差テーブル =====
    lines.append("\n\n[プロジェクト別 特徴量の差（差 = 正例rate - 負例rate）]")
    lines.append(f"  positive_rate = 特徴量が{THRESHOLD}より大きいペアの割合(%)")
    lines.append("  ◎=有効(>=10)  ○=やや有効(>=3)  △=効果小(>=0)  ✗=逆効果(<0)")
    lines.append("")

    proj_list = sorted(project_results.keys())

    # ヘッダー行
    header = f"{'特徴量':<28}"
    for proj in proj_list:
        header += f"  {proj[:10]:>10}"
    lines.append(header)
    lines.append("-" * (28 + 12 * len(proj_list)))

    def diff_cell(diff):
        if diff >= 10:
            return f"◎{diff:>+6.1f}"
        elif diff >= 3:
            return f"○{diff:>+6.1f}"
        elif diff >= 0:
            return f"△{diff:>+6.1f}"
        else:
            return f"✗{diff:>+6.1f}"

    for feat in ALL_FEATURES:
        row = f"{feat:<28}"
        for proj in proj_list:
            diff = project_results[proj]["feat_diff"][feat]["diff"]
            row += f"  {diff_cell(diff):>10}"
        lines.append(row)

    # ===== 全体の特徴量別サマリー =====
    lines.append("\n\n[正例と負例の特徴量比較（全プロジェクト合算）]")
    lines.append(f"  positive_rate = 特徴量が{THRESHOLD}より大きいペアの割合(%)")
    lines.append("")
    lines.append(f"{'特徴量':<28} {'1のrate(%)':>10} {'0のrate(%)':>10} {'差(1-0)':>8}  判定")
    lines.append("-" * 70)

    # 差の大きい順にソート
    sorted_results = sorted(results.items(), key=lambda x: -x[1]["diff_positive_rate"])

    for feat, r in sorted_results:
        r1   = r["co_changed_1"]["positive_rate"]
        r0   = r["co_changed_0"]["positive_rate"]
        diff = r["diff_positive_rate"]

        if diff >= 10:
            judge = "◎ 有効"
        elif diff >= 3:
            judge = "○ やや有効"
        elif diff >= 0:
            judge = "△ 効果小"
        else:
            judge = "✗ 逆効果"

        lines.append(f"{feat:<28} {r1:>10} {r0:>10} {diff:>8}  {judge}")

    lines.append("\n")
    lines.append("【判定基準（差）】")
    lines.append("  ◎ 有効      : 差 >= 10%  共変更ペアに圧倒的に多く出現")
    lines.append("  ○ やや有効  : 差 >= 3%   共変更ペアに多く出現する傾向あり")
    lines.append("  △ 効果小    : 差 >= 0%   差はあるが弱い")
    lines.append("  ✗ 逆効果    : 差 <  0%   共変更しないペアに多く出現（要考察）")

    report = "\n".join(lines)
    print(report)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[SAVED] {output_path}")


# ===== main =====
if __name__ == "__main__":
    print("[LOAD] datasets_with_features を読み込み中...")
    pairs = load_all_datasets(INPUT_DIR)

    if not pairs:
        print("[ERROR] データが見つかりません。put_feature_ast.py を先に実行してください。")
        exit(1)

    print("\n[VERIFY] 特徴量検証中...")
    results         = verify_features(pairs)
    project_results = verify_by_project(pairs)

    report_path = OUTPUT_DIR / "verification_report_diff.txt"
    print_and_save_report(results, project_results, report_path)