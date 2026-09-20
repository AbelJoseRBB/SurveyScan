from config import (
    INPUT_DIR,
    QUESTION_COORDINATES,
    TEXT_FIELDS,
    ANO_COLETA
)

from image_processor import (
    pdfToImage,
    alignToTemplate,
    grayscaleImage
)

from answer_reader import readForm

from text_reader import (
    loadDigitModels,
    readNumericFields,
    readDate
)


def main():

    print("Carregando modelos...")
    svm_model, knn_model = loadDigitModels()

    # Carrega os PDFs
    template_pages = pdfToImage(
        str(INPUT_DIR / "FormsVazio.pdf")
    )

    form_pages = pdfToImage(
        str(INPUT_DIR / "FormsFull.pdf")
    )

    # Alinha e processa as duas páginas
    processed_pages = {}

    for i, form_page in enumerate(form_pages):

        aligned_page = alignToTemplate(
            form_page,
            template_pages[i]
        )

        processed_pages[i + 1] = grayscaleImage(
            aligned_page
        )

    # 1. Respostas objetivas
    objective_answers = readForm(
        processed_pages,
        QUESTION_COORDINATES
    )

    # 2. Campos numéricos da primeira página
    numeric_answers = readNumericFields(
        processed_pages[1],
        TEXT_FIELDS[1],
        objective_answers,
        svm_model,
        knn_model
    )

    # 3. Data da segunda página
    date, date_needs_review = readDate(
        processed_pages[2],
        TEXT_FIELDS[2]["data_coleta"],
        ANO_COLETA,
        svm_model,
        knn_model
    )

    numeric_answers["data_coleta"] = {
        "valor": date,
        "revisar": date_needs_review
    }

    # 4. Resultado geral do formulário
    form_result = {
        "respostas_objetivas": objective_answers,
        "campos_numericos": numeric_answers
    }

    print("\n=== RESULTADO GERAL ===")

    print("\nRESPOSTAS OBJETIVAS:")
    for question, answer in form_result["respostas_objetivas"].items():
        print(f"{question}: {answer}")

    print("\nCAMPOS NUMÉRICOS:")
    for field, result in form_result["campos_numericos"].items():
        print(
            f"{field}: {result['valor']} "
            f"| Revisar: {result['revisar']}"
        )


if __name__ == "__main__":
    main()