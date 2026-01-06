# model_trainer_mini_tuning.py
import pandas as pd                 # pandas -> csv読み込みに使う
from sklearn.model_selection import train_test_split, GridSearchCV      # データセットを訓練用とテスト用に分割する関数
from sklearn.metrics import classification_report, accuracy_score    # precision / recall/ f1を含むテキストレポート作成、正解率計算の関数
import lightgbm as lgb    # ２値分類用モデル
import joblib     # モデルの読み込みに使用するライブラリ
import numpy as np    # 数値計算ライブラリnumpy

FEATURES_PATH = "dataset_minimal_java.csv"    # 読み込みデータセット指定
REPEAT_SEEDS = [42, 2023, 7, 99, 123]  # 複数乱数シード

def main():
    df = pd.read_csv(FEATURES_PATH, encoding="utf-8")    # データフレーム作成
    print(f"Loaded {len(df)} file pairs")     # 読み込んだ行数を出力 (動作確認用)

    features = [
        "import_similarity", "method_similarity"
    ]                          # 特徴量定義
    X = df[features]    # 特徴行列X作成
    y = df["label"]    # ラベルy

    # ================================
    # 1. ハイパーパラメータ探索
    # ================================
    param_grid = {    # 最適地を選ぶ
        "num_leaves": [15, 31, 63],
        "learning_rate": [0.01, 0.05, 0.1],
        "n_estimators": [50, 100, 200],
        "max_depth": [-1, 10, 20]
    }

    base_model = lgb.LGBMClassifier(objective="binary")

    grid = GridSearchCV(
        base_model,
        param_grid,
        cv=5,
        scoring="accuracy",
        n_jobs=-1
    )

    grid.fit(X, y)

    best_params = grid.best_params_
    print("✅ Best Parameters:", best_params)


    # ================================
    # 2. 複数Seedで安定性評価
    # ================================
    accuracies = []

    for seed in REPEAT_SEEDS:
        print(f"\n=== Seed {seed} ===")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            stratify=y,
            random_state=seed
        )

        model = lgb.LGBMClassifier(
            objective='binary',
            **best_params
        )

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        accuracies.append(acc)

        print(classification_report(y_test, y_pred, digits=4))
        print(f"Accuracy: {acc:.4f}")

    print("\n=== Summary ===")
    print(f"Mean Accuracy: {np.mean(accuracies):.4f}")
    print(f"Std Accuracy:  {np.std(accuracies):.4f}")

    joblib.dump(model, "lgbm_model_optimized.pkl")
    print("✅ Saved model: lgbm_model_optimized.pkl")


if __name__ == "__main__":
    main()


