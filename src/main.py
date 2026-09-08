from image_processor import (
    pdfToImage,
    grayscaleImage
)

from answer_reader import (
    readSingleChoiceQuestion
)

from config import (
    INPUT_DIR,
    QUESTION_COORDINATES
)


def main():

    pdf_path = INPUT_DIR / "Forms75_.pdf"

    pages = pdfToImage(
        str(pdf_path)
    )

    print(
        f"Paginas encontradas: {len(pages)}"
    )

    # Converte as páginas para grayscale
    gray_pages = {
        1: grayscaleImage(pages[0]),
        2: grayscaleImage(pages[1])
    }

    print("\n===== TESTE PAGINA 1 =====")

    # Questões normais da página 1
    for question_name, options in QUESTION_COORDINATES[1].items():

        # Q12 é um grupo de subquestões
        if question_name == "q12":
            continue

        answer = readSingleChoiceQuestion(
            gray_pages[1],
            options
        )

        print(
            f"{question_name}: {answer}"
        )

    print("\n===== TESTE Q12 =====")

    for subquestion_name, options in QUESTION_COORDINATES[1]["q12"].items():

        answer = readSingleChoiceQuestion(
            gray_pages[1],
            options
        )

        print(
            f"{subquestion_name}: {answer}"
        )

    print("\n===== TESTE PAGINA 2 =====")

    for question_name, options in QUESTION_COORDINATES[2].items():

        answer = readSingleChoiceQuestion(
            gray_pages[2],
            options
        )

        print(
            f"{question_name}: {answer}"
        )


if __name__ == "__main__":
    main()