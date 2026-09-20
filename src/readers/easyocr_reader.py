import cv2 as cv
import numpy as np
import easyocr
from readers.answer_reader import cropRegion

def loadEasyOCR():
    return easyocr.Reader(["pt", "en"], gpu=False)


def readHandwritingEasyOCR(image: np.ndarray, coordinates: tuple[int, int, int, int], reader) -> str:
    cropped = cropRegion(image, *coordinates)

    if cropped.size == 0:
        return "ERRO NO RECORTE"

    # Converte para escala de cinza, caso necessário
    if len(cropped.shape) == 3:
        cropped = cv.cvtColor(cropped, cv.COLOR_BGR2GRAY)

    # Adiciona margens brancas
    cropped = cv.copyMakeBorder(
        cropped,
        30, 30,
        30, 30,
        cv.BORDER_CONSTANT,
        value=255
    )

    # Executa o reconhecimento
    results = reader.readtext(cropped, detail= 0, paragraph= False)

    return " ".join(results).strip()