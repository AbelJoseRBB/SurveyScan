from pathlib import Path

from config import (
    INPUT_DIR,
    OUTPUT_DIR,
    QUESTION_COORDINATES,
    TEXT_FIELDS,
    ANO_COLETA
)

from image_processor import (
    pdfToImage,
    alignToTemplate,
    grayscaleImage
)

from readers.answer_reader import readForm

from readers.text_reader import (
    loadDigitModels,
    readNumericFields,
    readDate
)

from readers.handwriting_reader import loadHandwritingModel
from readers.easyocr_reader import loadEasyOCR
from readers.handwriting_comparison import readHandwrittenFields


def main():

    # 1. Carregamento dos modelos
    print("Carregando modelos numéricos...")
    svm_model, knn_model = loadDigitModels()

    print("Carregando modelos de escrita manuscrita...")
    processor, trocr_model = loadHandwritingModel()
    easyocr_reader = loadEasyOCR()

    # 2. Carregamento dos formulários
    print("Carregando formulários...")

    template_pages = pdfToImage(
        str(INPUT_DIR / "FormsVazio.pdf")
    )

    form_pages = pdfToImage(
        str(INPUT_DIR / "FormsFull.pdf")
    )

    # 3. Alinhamento e pré-processamento
    processed_pages = {}

    for i, form_page in enumerate(form_pages):

        aligned_page = alignToTemplate(
            form_page,
            template_pages[i]
        )

        processed_pages[i + 1] = grayscaleImage(
            aligned_page
        )

    # 4. Respostas objetivas
    objective_answers = readForm(
        processed_pages,
        QUESTION_COORDINATES
    )

    # 5. Campos numéricos
    numeric_answers = readNumericFields(
        processed_pages[1],
        TEXT_FIELDS[1],
        objective_answers,
        svm_model,
        knn_model
    )

    # 6. Data de coleta
    date_value, date_review = readDate(
        processed_pages[2],
        TEXT_FIELDS[2]["data_coleta"],
        ANO_COLETA,
        svm_model,
        knn_model
    )

    date_answer = {
        "valor": date_value,
        "revisar": date_review
    }

    # 7. Campos manuscritos
    handwritten_answers = readHandwrittenFields(
        image=processed_pages[1],
        text_fields=TEXT_FIELDS[1],
        objective_answers=objective_answers,
        form_id="001",
        processor=processor,
        trocr_model=trocr_model,
        easyocr_reader=easyocr_reader,
        output_dir=Path(OUTPUT_DIR) / "revisao"
    )

    # 8. Resultado consolidado do questionário
    questionnaire_result = {
        "identificador_processamento": "001",
        "objetivas": objective_answers,
        "numericas": numeric_answers,
        "data_coleta": date_answer,
        "manuscritas": handwritten_answers
    }

    # 9. Exibição dos resultados
    print("\n========== RESULTADO DO QUESTIONÁRIO ==========")

    print("\n=== RESPOSTAS OBJETIVAS ===")
    for field, value in questionnaire_result["objetivas"].items():
        print(f"{field}: {value}")

    print("\n=== CAMPOS NUMÉRICOS ===")
    for field, result in questionnaire_result["numericas"].items():
        print(
            f"{field}: {result['valor']} "
            f"| Revisar: {result['revisar']}"
        )

    print("\n=== DATA DE COLETA ===")
    print(
        f"{date_answer['valor']} "
        f"| Revisar: {date_answer['revisar']}"
    )

    print("\n=== CAMPOS MANUSCRITOS ===")
    for field, result in questionnaire_result["manuscritas"].items():

        print(
            f"{field}: {result['valor']} "
            f"| Revisar: {result['revisar']}"
        )

        if result.get("sugestoes") is not None:
            print(f"  Sugestões: {result['sugestoes']}")

    # 10. Campos que precisam de revisão
    fields_to_review = []

    for field, result in numeric_answers.items():
        if result["revisar"]:
            fields_to_review.append(field)

    if date_answer["revisar"]:
        fields_to_review.append("data_coleta")

    for field, result in handwritten_answers.items():
        if result["revisar"]:
            fields_to_review.append(field)

    print("\n=== CAMPOS PARA REVISÃO ===")

    if fields_to_review:
        for field in fields_to_review:
            print(f"- {field}")
    else:
        print("Nenhum campo sinalizado para revisão.")


if __name__ == "__main__":
    main()