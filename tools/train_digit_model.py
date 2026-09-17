from pathlib import Path

import joblib
import numpy as np

from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

BASE_DIR = Path(__file__).parent.parent

MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "digit_knn.pkl"

def main():

    print("BAIXANDO/CARREGANDO MNIST...")

    mnist = fetch_openml(
        "mnist_784",
        version=1,
        as_frame=False
    )

    X = mnist.data.astype(np.float32)
    Y = mnist.target.astype(np.int64)

    X = X / 255.0

    X = X[:20000]
    Y = Y[:20000]

    X_train, X_test, Y_train, Y_test = train_test_split(
        X,
        Y,
        test_size=0.2,
        random_state=42,
        stratify=Y
    )

    print(f"Amostras de treinamento: {len(X_train)}")

    print(f"Amostras de teste: {len(X_test)}")

    print("Treinando KNN...")

    model = KNeighborsClassifier(
        n_neighbors=3,
        weights="distance"
    )

    model.fit(X_train, Y_train)

    print("Testando Modelo...")

    predictions = model.predict(X_test)

    accuracy = accuracy_score(Y_test, predictions)

    print(f"Acuracia no MNIST: {accuracy:.2%}")

    MODEL_DIR.mkdir(parents= True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Modelo Salvo em {MODEL_PATH}")

if __name__ == "__main__":
    main()