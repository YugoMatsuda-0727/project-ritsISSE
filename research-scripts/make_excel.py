import json
import csv
from pathlib import Path
import xlsxwriter

BASE_DIR = Path(__file__).parent
METADATA_DIR = BASE_DIR / "outputs" / "metadata"
DATASET_DIR = BASE_DIR / "outputs" / "dataset"
OUTPUT_PATH = str(BASE_DIR / "outputs" / "distribution_analysis.xlsx")

SKIP = {".git", "dummy_sample", "Log", "research-scripts"}

def count_classes(metadata_path):
    with open(metadata_path, encoding="utf-8") as f:
        data = json.load(f)
    return len(data)

def get_label_stats(dataset_path):
    total = 0
    positive = 0
    with open(dataset_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if int(row["co_changed"]) == 1:
                positive += 1
    return total, positive

def collect_data():
    rows = []
    for meta_file in sorted(METADATA_DIR.glob("*.json")):
        project = meta_file.stem
        if project in SKIP:
            continue
        dataset_file = DATASET_DIR / f"{project}_dataset.csv"
        if not dataset_file.exists():
            continue
        class_count = count_classes(meta_file)
        total, positive = get_label_stats(dataset_file)
        ratio = round(positive / total * 100, 2) if total > 0 else 0.0
        rows.append({
            "project": project,
            "class_count": class_count,
            "total_pairs": total,
            "positive_pairs": positive,
            "cochange_ratio": ratio,
        })
        print(f"  {project}: classes={class_count}, ratio={ratio}%")
    return rows

def build_excel(rows):
    wb = xlsxwriter.Workbook(OUTPUT_PATH)
    ws = wb.add_worksheet("Distribution")

    header_fmt = wb.add_format({
        "bold": True, "font_color": "white", "bg_color": "2F4F8F",
        "align": "center", "valign": "vcenter", "border": 1,
        "font_name": "Arial", "font_size": 11
    })
    even_fmt = wb.add_format({
        "bg_color": "EEF2FF", "align": "center", "valign": "vcenter",
        "border": 1, "font_name": "Arial", "font_size": 10
    })
    odd_fmt = wb.add_format({
        "align": "center", "valign": "vcenter",
        "border": 1, "font_name": "Arial", "font_size": 10
    })
    corr_label_fmt = wb.add_format({"bold": True, "font_name": "Arial"})
    corr_val_fmt = wb.add_format({
        "font_color": "0000FF", "font_name": "Arial", "num_format": "0.0000"
    })

    headers = ["Project", "Class Count", "Total Pairs", "Positive Pairs", "Co-change Rate (%)"]
    col_widths = [40, 15, 15, 15, 20]
    for col, (h, w) in enumerate(zip(headers, col_widths)):
        ws.write(0, col, h, header_fmt)
        ws.set_column(col, col, w)
    ws.set_row(0, 22)

    for i, row in enumerate(rows):
        fmt = even_fmt if i % 2 == 0 else odd_fmt
        ws.write(i + 1, 0, row["project"], fmt)
        ws.write(i + 1, 1, row["class_count"], fmt)
        ws.write(i + 1, 2, row["total_pairs"], fmt)
        ws.write(i + 1, 3, row["positive_pairs"], fmt)
        ws.write(i + 1, 4, row["cochange_ratio"], fmt)

    last_row = len(rows) + 1
    ws.write(last_row + 1, 0, "相関係数（クラス数 vs 共変更率）", corr_label_fmt)
    ws.write_formula(last_row + 1, 1,
                     f"=CORREL(B2:B{last_row},E2:E{last_row})", corr_val_fmt)

    chart = wb.add_chart({"type": "scatter"})

    chart.add_series({
        "name": "Projects",
        "categories": ["Distribution", 1, 1, len(rows), 1],
        "values":     ["Distribution", 1, 4, len(rows), 4],
        "marker": {
            "type": "circle",
            "size": 8,
            "fill": {"color": "#4472C4"},
            "border": {"color": "#4472C4"},
        },
        "line": {"none": True},
        "data_labels": {
            "value": True,
            "num_format": "0.00",
        },
    })

    chart.set_title({"name": "Class Count vs Co-change Rate"})

    chart.set_x_axis({
        "name": "Class Count",
        "min": 0,
        "max": 1200,
        "major_unit": 200,
        "num_format": "0",
        "major_gridlines": {"visible": True},
    })

    chart.set_y_axis({
        "name": "Co-change Rate (%)",
        "min": 0,
        "max": 100,
        "major_unit": 10,
        "num_format": "0",
        "major_gridlines": {"visible": True},
    })

    chart.set_legend({"none": True})
    chart.set_size({"width": 600, "height": 400})

    ws.insert_chart("G2", chart)

    wb.close()
    print(f"\n[DONE] {OUTPUT_PATH}")

if __name__ == "__main__":
    print("[COLLECT] データ集計中...")
    rows = collect_data()
    print("\n[BUILD] Excel作成中...")
    build_excel(rows)