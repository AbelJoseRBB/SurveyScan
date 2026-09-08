from pathlib import Path
import cv2 as cv
import numpy as np 
import pymupdf 
import sys


def pdfToImage(pdf_path: str, dpi: int = 300) -> list[np.ndarray]:
    doc =  pymupdf.open(pdf_path)
    imgs = []

    for page in doc:
        pixmap = page.get_pixmap(dpi=dpi)

        image = np.frombuffer(
            pixmap.samples,
            dtype=np.uint8
        )

        image = image.reshape(
            pixmap.height,
            pixmap.width,
            pixmap.n
        )

        # PyMuPDF fornece RGB/RGBA, enquanto OpenCV trabalha com BGR.
        if pixmap.n == 4:
            image = cv.cvtColor(image, cv.COLOR_RGBA2BGR)
        else:
            image = cv.cvtColor(image, cv.COLOR_RGB2BGR)

        imgs.append(image)

    doc.close()

    return imgs



def loadImage(image_path: str) -> np.ndarray:
    img = cv.imread(image_path)

    if img is None:
        sys.exit(f"ERROR: Could not read the image: {image_path}.")

    return img

def grayscaleImage(image: np.ndarray) -> np.ndarray:
    return cv.cvtColor(image,cv.COLOR_BGR2GRAY)


# função antiga 
def preprocessImage(image: np.ndarray) -> np.ndarray:
    # conversão da imagem para cinza
    gray_img = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    # binariza a imagem
    binary = cv.threshold(
        gray_img,
        0,
        255,
        cv.THRESH_BINARY_INV + cv.THRESH_OTSU
    )[1]

    return binary


def saveProcessedImage(image: np.ndarray, output_path: str) -> None:
    output = Path(output_path)

    output.parent.mkdir(
        parents= True,
        exist_ok= True
    )

    cv.imwrite(str(output), image)

    

