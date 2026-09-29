from pathlib import Path
import sys
import cv2 as cv
from paddleocr import TextRecognition

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
INPUT_DIR = BASE_DIR / "formularios"

sys.path.insert(0, str(SRC_DIR))

from config import TEXT_FIELDS, ANO_COLETA
from image_processor import pdfToImage, prepareTemplate, alignToTemplate, grayscaleImage
from readers.text_reader import loadDigitModels, readNumber, readIncome, readDate

EXPECTED = {
    "FormsFull1.pdf": {
        "questionario_numero": "1",
        "idade": "21",
        "quantidade_filhos": "5",
        "renda_valor": "1400.50",
        "dia": "19",
        "mes": "09"
    },
    "FormsFull2.pdf": {
        "questionario_numero": "2",
        "idade": "24",
        "quantidade_filhos": "4",
        "renda_valor": "100.00",
        "dia": "19",
        "mes": "09"
    },
    "FormsFull3.pdf": {
        "questionario_numero": "3",
        "idade": "19",
        "quantidade_filhos": None,
        "renda_valor": "17800.00",
        "dia": "20",
        "mes": "09"
    }
}

template_pages = pdfToImage(INPUT_DIR / "FormsVazio.pdf")
template_data = [prepareTemplate(page) for page in template_pages]

svm_model, knn_model = loadDigitModels()
paddle_model = TextRecognition(model_name="latin_PP-OCRv5_mobile_rec", device="cpu")


def paddleRead(image, coordinates):
    x1, y1, x2, y2 = coordinates
    cropped = image[y1:y2, x1:x2]

    if len(cropped.shape) == 2:
        cropped = cv.cvtColor(cropped, cv.COLOR_GRAY2BGR)

    outputs = paddle_model.predict(input=cropped, batch_size=1)
    result = outputs[0].json["res"]

    return result["rec_text"].strip(), result["rec_score"]


def showResult(field, expected, current, paddle, confidence):
    current_status = "✓" if current == expected else "✗"
    paddle_status = "✓" if paddle == expected else "✗"

    print(f"{field:<22} esperado={expected:<8} atual={current_status} {current:<10} paddle={paddle_status} {paddle:<10} conf={confidence:.3f}")


for filename, expected_values in EXPECTED.items():
    print(f"\n=== {filename} ===")

    pages = pdfToImage(INPUT_DIR / filename)
    processed_pages = {}

    for i, page in enumerate(pages):
        aligned = alignToTemplate(page, template_data[i])
        processed_pages[i + 1] = grayscaleImage(aligned)

    page1 = processed_pages[1]
    page2 = processed_pages[2]

    for field in ["questionario_numero", "idade", "quantidade_filhos"]:
        expected = expected_values[field]

        if expected is None:
            continue

        current, _ = readNumber(page1, TEXT_FIELDS[1][field], svm_model, knn_model)
        paddle, confidence = paddleRead(page1, TEXT_FIELDS[1][field])

        showResult(field, expected, current, paddle, confidence)

    expected = expected_values["renda_valor"]
    current, _ = readIncome(page1, TEXT_FIELDS[1]["renda_valor"], svm_model, knn_model)
    paddle, confidence = paddleRead(page1, TEXT_FIELDS[1]["renda_valor"])

    paddle_normalized = paddle.replace(",", ".").replace("R$", "").replace(" ", "")

    try:
        paddle_normalized = f"{float(paddle_normalized):.2f}"
    except ValueError:
        pass

    showResult("renda_valor", expected, current, paddle_normalized, confidence)

    current_date, _ = readDate(page2, TEXT_FIELDS[2]["data_coleta"], ANO_COLETA, svm_model, knn_model)

    for field in ["dia", "mes"]:
        paddle, confidence = paddleRead(page2, TEXT_FIELDS[2]["data_coleta"][field])
        expected = expected_values[field]

        current = current_date.split("/")[0] if field == "dia" and "/" in current_date else ""
        current = current_date.split("/")[1] if field == "mes" and "/" in current_date else current

        showResult(field, expected, current, paddle, confidence)