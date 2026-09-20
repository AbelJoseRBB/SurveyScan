import cv2 as cv
import numpy as np
import easyocr


def loadEasyOCR():
    return easyocr.Reader(
        ["pt", "en"],
        gpu=False
    )


def readHandwritingEasyOCR(
    image: np.ndarray,
    coordinates: tuple[int, int, int, int],
    reader
) -> str:

    x1, y1, x2, y2 = coordinates

    cropped = image[y1:y2, x1:x2]

    if cropped.size == 0:
        return "ERRO NO RECORTE"

    # Converte para escala de cinza, caso necessário
    if len(cropped.shape) == 3:
        cropped = cv.cvtColor(
            cropped,
            cv.COLOR_BGR2GRAY
        )

    # Adiciona margens brancas
    cropped = cv.copyMakeBorder(
        cropped,
        30, 30,
        30, 30,
        cv.BORDER_CONSTANT,
        value=255
    )

    # Executa o reconhecimento
    results = reader.readtext(
        cropped,
        detail=0,
        paragraph=False
    )

    return " ".join(results).strip()