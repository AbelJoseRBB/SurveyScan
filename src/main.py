from image_processor import (
    pdfToImage,
    alignToTemplate,
    grayscaleImage
)

from text_reader import (
    cropTextField,
    readNumber
)

from config import (
    INPUT_DIR,
    TEXT_FIELDS
)


def main():

    template_pages = pdfToImage(
        str(INPUT_DIR / "FormsVazio.pdf")
    )

    form_pages = pdfToImage(
        str(INPUT_DIR / "FormsFullC.pdf")
    )

    aligned = alignToTemplate(
        form_pages[0],
        template_pages[0]
    )

    gray = grayscaleImage(
        aligned
    )

    idade_region = cropTextField(
        gray,
        TEXT_FIELDS[1]["idade"]
    )

    idade = readNumber(
        idade_region
    )

    print(
        f"Idade reconhecida: {idade}"
    )


if __name__ == "__main__":
    main()