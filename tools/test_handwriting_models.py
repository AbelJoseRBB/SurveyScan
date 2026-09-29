from pathlib import Path
from paddleocr import TextRecognition

BASE_DIR = Path(__file__).resolve().parent.parent
REVIEW_DIR = BASE_DIR / "output" / "revisao"

TESTS = {
    "questionario_2678ec2b737a_ocupacao.png": "Engenheiro",
    "questionario_3d338f703192_ocupacao.png": "Pedreira",
    "questionario_face04ca0f90_ocupacao.png": "Médico",
    "questionario_face04ca0f90_religiao_outra.png": "Budista",
    "questionario_3d338f703192_idade.png": "24"
}

print("Carregando PaddleOCR...")

model = TextRecognition(model_name="latin_PP-OCRv5_mobile_rec", device="cpu")

print("\n=== PADDLEOCR ===")

for filename, expected in TESTS.items():
    image_path = REVIEW_DIR / filename
    outputs = model.predict(input=str(image_path), batch_size=1)

    for output in outputs:
        result = output.json["res"]
        text = result["rec_text"]
        confidence = result["rec_score"]

        status = "✓" if text.casefold() == expected.casefold() else "✗"

        print(f"{status} Esperado: {expected:<12} | Reconhecido: {text:<20} | Confiança: {confidence:.3f}")