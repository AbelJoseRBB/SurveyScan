# Ativar venv
# .\venv\Scripts\Activate.ps1

from image_processor import (
    preprocessImage,
    pdfToImage
)

from answer_reader import (
    cropRegion,
    getFillScore,
    readMark,
    drawTestX
)


def main():
    pages = pdfToImage(
        "formularios/Forms.pdf"
    )

    print(f"Paginas encontradas: {len(pages)}")

    # Processa a primeira página
    processed = preprocessImage(
        pages[0]
    )

    # Região interna da alternativa Masculino
    masculino_coords = (
        627,
        765,
        655,
        797
    )

    # Teste 1: alternativa vazia
    empty_region = cropRegion(
        processed,
        *masculino_coords
    )

    empty_score = getFillScore(
        empty_region
    )

    empty_marked = readMark(
        processed,
        masculino_coords
    )

    print("\n--- Teste vazio ---")
    print(f"Score: {empty_score}")
    print(f"Marcado: {empty_marked}")

    # Teste 2: cria um X artificial na região
    marked_region = drawTestX(
        empty_region
    )

    marked_score = getFillScore(
        marked_region
    )

    print("\n--- Teste com X artificial ---")
    print(f"Score: {marked_score}")

    # Aqui testamos diretamente a lógica do threshold
    # usando a região já marcada artificialmente
    from answer_reader import isMarked

    marked_result = isMarked(
        marked_region
    )

    print(f"Marcado: {marked_result}")


if __name__ == "__main__":
    main()