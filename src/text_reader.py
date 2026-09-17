import cv2 as cv
import numpy as np
from pathlib import Path
import joblib

def cropTextField(image: np.ndarray, coordinates: tuple[int, int, int, int]) -> np.ndarray:

    x1, y1, x2, y2 = coordinates

    return image[
        y1:y2,
        x1:x2
    ]


def segmentDigits(image: np.ndarray) -> list[np.ndarray]:

    # Garante que a imagem esteja em escala de cinza
    if len(image.shape) == 3:
        gray = cv.cvtColor(
            image,
            cv.COLOR_BGR2GRAY
        )
    else:
        gray = image.copy()

    # Binarização invertida:
    # fundo = 0
    # escrita = 255
    binary = cv.threshold(
        gray,
        0,
        255,
        cv.THRESH_BINARY_INV + cv.THRESH_OTSU
    )[1]

    # Detecta linhas horizontais longas
    horizontal_kernel = cv.getStructuringElement(
        cv.MORPH_RECT,
        (80, 1)
    )

    horizontal_lines = cv.morphologyEx(
        binary,
        cv.MORPH_OPEN,
        horizontal_kernel
    )

    # Remove a linha do formulário
    without_lines = cv.subtract(
        binary,
        horizontal_lines
    )

    # Procura os componentes restantes
    contours, _ = cv.findContours(
        without_lines,
        cv.RETR_EXTERNAL,
        cv.CHAIN_APPROX_SIMPLE
    )

    digit_regions = []

    for contour in contours:

        x, y, w, h = cv.boundingRect(
            contour
        )

        # Ignora pequenos ruídos
        if h < 15 or w < 3:
            continue

        area = cv.contourArea(
            contour
        )

        if area < 30:
            continue

        digit_regions.append(
            (x, y, w, h)
        )

    # Ordena os dígitos da esquerda para direita
    digit_regions.sort(
        key=lambda region: region[0]
    )

    digits = []

    for x, y, w, h in digit_regions:

        digit = without_lines[
            y:y + h,
            x:x + w
        ]

        digits.append(
            digit
        )

    return digits

def normalizeDigit(digit: np.ndarray, canvas_size: int = 28, digit_size: int = 20) -> np.ndarray:

    if len(digit.shape) == 3:
        digit = cv.cvtColor(digit, cv.COLOR_BGR2GRAY)

    height, width = digit.shape[:2]

    scale = min(digit_size / height, digit_size/width)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))

    resized = cv.resize(digit, (new_width ,new_height), interpolation= cv.INTER_AREA)

    canvas = np.zeros((canvas_size, canvas_size), dtype= np.uint8)

    x_offset = (canvas_size - new_width) // 2
    y_offset = (canvas_size - new_height) // 2

    canvas[
        y_offset:y_offset + new_height,
        x_offset:x_offset + new_width
    ] = resized

    moments = cv.moments(canvas)

    if moments["m00"] != 0:
        center_x = (moments["m10"]/ moments["m00"])
        center_y = (moments["m01"]/ moments["m00"])

        # Centro desejado da imagem
        target_center = (canvas_size - 1) / 2

        shift_x = int(round(target_center - center_x))
        shift_y = int(round(target_center - center_y))

        translation = np.float32([
            [1, 0, shift_x],
            [0, 1, shift_y]
        ])

        canvas = cv.warpAffine(
            canvas,
            translation,
            (canvas_size, canvas_size),
            borderValue=0
        )
    return canvas

def loadDigitModels():
    base_dir = Path(__file__).parent.parent
    model_path = base_dir / "models"

    svm_model = joblib.load(model_path/"digit_svm.pkl")
    knn_model = joblib.load(model_path/"digit_knn.pkl")

    return svm_model, knn_model

def predictDigit(digit: np.ndarray, svm_model, knn_model) -> tuple[int, bool]:
    normalized = normalizeDigit(digit)

    sample = normalized.reshape(1, -1)
    sample = sample.astype(np.float32) / 255.0

    svm_prediction = svm_model.predict(sample)[0]
    knn_prediction = knn_model.predict(sample)[0]
    models_agree = (svm_prediction == knn_prediction)
    
    return svm_prediction, models_agree

def readNumber(image:np.ndarray, coordinates: tuple[int, int, int , int], svm_model, knn_model) -> str:
    field = cropTextField(image, coordinates)
    digits = segmentDigits(field)

    if len(digits) == 0:
        return "EM BRANCO"
    result = ""
    needs_review = False
    
    for digit in digits:
        prediction, models_agree = predictDigit(digit, svm_model, knn_model)
        result += str(prediction)

        if not models_agree:
            needs_review = True

    return result, needs_review

def readAge(image: np.ndarray, coordinates: tuple[int, int, int, int], svm_model, knn_model) -> tuple[str, bool]:
    value, needs_review = readNumber(image, coordinates, svm_model, knn_model)

    if value == "EM BRANCO":
        return value, False

    try:
        age = int(value)
    except ValueError:
        return value, True

    if age < 15 or age > 100:
        needs_review = True

    return str(age), needs_review



