# Ativar venv
# .\venv\Scripts\Activate.ps1 

from image_processor import preprocessImage, saveProcessedImage, pdfToImage

def main():
    pages = pdfToImage(
        "formularios/Forms.pdf"
    )

    print(f"Paginas encontradas: {len(pages)}")


    for i, page in enumerate(pages, start=1):

        processed = preprocessImage(page)

        saveProcessedImage(
            processed,
            f"output/page{i}_processed.png"
        )

        print(f"Pagina {i} processada.") 

if __name__ == "__main__":
    main()