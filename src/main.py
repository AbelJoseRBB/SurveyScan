from config import INPUT_DIR, TEXT_FIELDS

from image_processor import (
    pdfToImage,
    alignToTemplate,
    grayscaleImage
)

from text_reader import (
    loadDigitModels,
    readAge
)


def main():

    print("Carregando modelos...")

    svm_model, knn_model = loadDigitModels()

    template_pages = pdfToImage(
        str(INPUT_DIR / "FormsVazio.pdf")
    )

    form_pages = pdfToImage(
        str(INPUT_DIR / "FormsFullC.pdf")
    )

    aligned_page = alignToTemplate(
        form_pages[0],
        template_pages[0]
    )

    gray_page = grayscaleImage(
        aligned_page
    )

    age, needs_review = readAge(
        gray_page,
        TEXT_FIELDS[1]["idade"],
        svm_model,
        knn_model
    )

    print(f"Idade reconhecida: {age}")
    print(f"Revisar: {needs_review}")


if __name__ == "__main__":
    main()