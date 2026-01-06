# feature_extractor_1201.py

import pandas as pd
import re
import os

INPUT_CSV = "cochange_pairs.csv"     # file1, file2, label
OUTPUT_CSV = "feature_dataset.csv"


# --------------------------
# Utility: Safe file read
# --------------------------
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except:
        return ""


# --------------------------
# Feature 1: file length
# --------------------------
def file_length(path):
    content = read_file(path)
    return len(content.splitlines())


# --------------------------
# Feature 2: import similarity
# --------------------------
def import_similarity(f1, f2):
    def get_imports(text):
        imports = set()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("import "):
                imports.add(line)
        return imports

    t1 = read_file(f1)
    t2 = read_file(f2)

    i1, i2 = get_imports(t1), get_imports(t2)

    if len(i1) == 0 and len(i2) == 0:
        return 0.0
    return len(i1 & i2) / max(len(i1), len(i2))


# --------------------------
# Feature 3: token jaccard
# --------------------------
def token_jaccard(f1, f2):
    def tokenize(text):
        return set(re.findall(r"[A-Za-z_]+", text))

    t1 = tokenize(read_file(f1))
    t2 = tokenize(read_file(f2))

    if len(t1) == 0 and len(t2) == 0:
        return 0.0

    return len(t1 & t2) / len(t1 | t2)


# --------------------------
# Feature 4: method name overlap
# --------------------------
def method_name_overlap(f1, f2):
    def extract_methods(text):
        # かなり簡易な Java メソッド抽出 (public int func(...){ のような行)
        return set(re.findall(r"[A-Za-z0-9_]+(?=\()", text))

    m1 = extract_methods(read_file(f1))
    m2 = extract_methods(read_file(f2))

    if len(m1) == 0 and len(m2) == 0:
        return 0.0

    return len(m1 & m2) / max(len(m1), len(m2))


# --------------------------
# Main
# --------------------------
def main():
    df = pd.read_csv(INPUT_CSV)
    
    rows = []

    for idx, row in df.iterrows():
        f1, f2, label = row["file1"], row["file2"], row["label"]

        fl1 = file_length(f1)
        fl2 = file_length(f2)
        imp_sim = import_similarity(f1, f2)
        tok_jac = token_jaccard(f1, f2)
        meth_ov = method_name_overlap(f1, f2)

        rows.append([
            f1, f2, label,
            fl1, fl2,
            imp_sim, tok_jac, meth_ov
        ])

        if idx % 500 == 0:
            print(f"Processed {idx} pairs...")

    columns = [
        "file1", "file2", "label",
        "len1", "len2",
        "import_sim",
        "token_jaccard",
        "method_overlap"
    ]

    out = pd.DataFrame(rows, columns=columns)
    out.to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Saved feature dataset → {OUTPUT_CSV}")
    print(f"Total rows: {len(out)}")


if __name__ == "__main__":
    main()

