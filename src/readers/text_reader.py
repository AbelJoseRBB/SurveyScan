from pathlib import Path
from datetime import datetime
import cv2 as cv
import numpy as np
import joblib

def cropTextField(image: np.ndarray, coordinates: tuple[int, int, int, int]) -> np.ndarray:

    x1, y1, x2, y2 = coordinates

    return image[y1:y2, x1:x2]


def segmentDigits(image: np.ndarray) -> list[np.ndarray]:
    regions = segmentDigitsWithPositions(image)
    return [digit for digit, _, _, _, _ in regions]

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

        canvas = cv.warpAffine(canvas, translation, (canvas_size, canvas_size), borderValue=0)

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

def readNumber(image:np.ndarray, coordinates: tuple[int, int, int , int], svm_model, knn_model) -> tuple[str, bool]:
    field = cropTextField(image, coordinates)
    digits = segmentDigits(field)

    if len(digits) == 0:
        return "EM BRANCO", True
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

def readNumericFields(image: np.ndarray, text_fields: dict, objective_answers: dict, svm_model, knn_model) -> dict:

    results = {}

    # Numero Questionario 
    number, needs_review = readNumber(image, text_fields["questionario_numero"], svm_model, knn_model)

    results["questionario_numero"] = {
        "valor" : number,
        "revisar" : needs_review or number == "EM BRANCO"
    }

    # Idade
    age, needs_review = readAge(image, text_fields["idade"], svm_model, knn_model)

    results["idade"] = {
        "valor": age,
        "revisar": needs_review or age == "EM BRANCO"
    }

    # Quantidade de filhos
    if objective_answers["tem_filhos"] == "Sim":

        quant, needs_review = readNumber(image, text_fields["quantidade_filhos"], svm_model, knn_model)
        
        results["quantidade_filhos"] = {
            "valor": quant,
            "revisar": (needs_review or quant == "EM BRANCO" or (quant.isdigit() and int(quant) == 0))
        }
    else:
        results["quantidade_filhos"] ={
            "valor": "0" if objective_answers["tem_filhos"] == "Não"
            else "Verificar Resposta",
            "revisar": objective_answers["tem_filhos"] != "Não"
        }
    
    # Renda Mensal 
    if objective_answers["renda_mensal"] == "Sim":

        valor, needs_review = readIncome(image, text_fields["renda_valor"], svm_model, knn_model)
                
        results["renda_valor"] = {
            "valor": valor,
            "revisar": needs_review or valor == "EM BRANCO"
        }
    else:
        results["renda_valor"] = {
            "valor": "NÃO SE APLICA" if objective_answers["renda_mensal"] == "Não"
            else "Verificar Resposta",
            "revisar": objective_answers["renda_mensal"] != "Não"
        }

    return results

def segmentDigitsWithPositions(image: np.ndarray) -> list[tuple[np.ndarray, int, int, int, int]]:

    if len(image.shape) == 3:
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]

    horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (80, 1))

    horizontal_lines = cv.morphologyEx(binary, cv.MORPH_OPEN, horizontal_kernel)

    without_lines = cv.subtract(binary, horizontal_lines)

    contours, _ = cv.findContours(without_lines, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    digit_regions = []

    for contour in contours:
        x, y, w, h = cv.boundingRect(contour)

        if h < 15 or w < 3:
            continue

        if cv.contourArea(contour) < 30:
            continue

        digit_regions.append((x, y, w, h))

    digit_regions.sort(key=lambda region: region[0])

    digits = []

    for x, y, w, h in digit_regions:
        digit = without_lines[y:y + h, x:x + w]
        digits.append((digit, x, y, w, h))

    return digits

def findIncomeSeparators(image: np.ndarray, digit_regions: list)-> list[tuple[int, int, int, int]]:
    if len(image.shape) == 3:
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]

    horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (80, 1))
    horizontal_lines = cv.morphologyEx(binary, cv.MORPH_OPEN, horizontal_kernel)

    without_lines = cv.subtract(binary, horizontal_lines)

    contours, _ = cv.findContours(without_lines, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    separators = []

    for contour in contours:

        x, y, w, h = cv.boundingRect(contour)

        # Ignora componentes muito pequenos
        if w < 2 or h < 2:
            continue

        # Ignora componentes grandes, provavelmente dígitos
        if h >= 15:
            continue

        # Verifica se o componente está entre dois dígitos
        for i in range(len(digit_regions) - 1):

            _, digit_x, _, digit_w, _ = digit_regions[i]

            _, next_x, _, _, _ = digit_regions[i + 1]

            digit_end = digit_x + digit_w

            if x >= digit_end and x + w <= next_x:

                separators.append((x, y, w, h))
                break

    return separators

def readIncome(image: np.ndarray, coordinates: tuple[int, int, int, int], svm_model, knn_model)-> tuple[str, bool]:

    field = cropTextField(image, coordinates)

    digit_regions = segmentDigitsWithPositions(field)

    if len(digit_regions) == 0:
        return "EM BRANCO", True

    digits = ""
    needs_review = False

    for digit, _, _, _, _ in digit_regions:

        prediction, models_agree = predictDigit(digit, svm_model, knn_model)

        digits += str(prediction)

        if not models_agree:
            needs_review = True

    separators = findIncomeSeparators(field, digit_regions)

    # Verifica se existe um separador antes dos dois últimos dígitos
    has_decimal_separator = False

    if len(digit_regions) >= 3:
        _, last_integer_x, _, last_integer_w, _ = digit_regions[-3]
        _, first_decimal_x, _, _, _ = digit_regions[-2]

        integer_end = last_integer_x + last_integer_w

        for separator_x, _, separator_w, _ in separators:
            if separator_x >= integer_end and separator_x + separator_w <= first_decimal_x:
                has_decimal_separator = True
                break

    # Com separador decimal: dois últimos dígitos são centavos
    if has_decimal_separator:
        reais = digits[:-2]
        centavos = digits[-2:]

        return f"{int(reais)}.{centavos}", needs_review

    # Sem separador decimal: todos os dígitos representam reais
    return f"{int(digits):.2f}", needs_review

def readDate(image: np.ndarray, coordinates: dict, year: int, svm_model, knn_model)->tuple[str, bool]:

    day, review_day = readNumber(image, coordinates["dia"], svm_model, knn_model)
    month, review_month = readNumber(image, coordinates["mes"], svm_model, knn_model)

    # Verifica se algum campo está vazio
    if day == "EM BRANCO" or month == "EM BRANCO":
        return "EM BRANCO", True

    # Verifica se os modelos discordaram
    needs_review = review_day or review_month

    if len(day) > 2 or len(month) > 2:
        return f"{day}/{month}/{year}", True
    
    # Monta a data com dois dígitos para dia e mês
    date_text = f"{day.zfill(2)}/{month.zfill(2)}/{year}"

    # Verifica se a data existe
    try:
        datetime.strptime(date_text, "%d/%m/%Y")
    except ValueError:
        needs_review = True

    return date_text, needs_review
