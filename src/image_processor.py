from pathlib import Path
import cv2 as cv
import numpy as np 
import pymupdf 

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

def grayscaleImage(image: np.ndarray) -> np.ndarray:
    return cv.cvtColor(image,cv.COLOR_BGR2GRAY)

def alignToTemplate(image: np.ndarray,template: np.ndarray) -> np.ndarray:
    gray_image = grayscaleImage(image)
    gray_template = grayscaleImage(template)

    orb = cv.ORB_create( nfeatures=5000)

    keypoints_image, descriptors_image = orb.detectAndCompute(gray_image,None)

    keypoints_template, descriptors_template = orb.detectAndCompute(gray_template,None)

    matcher = cv.BFMatcher(cv.NORM_HAMMING)

    matches = matcher.knnMatch(descriptors_image,descriptors_template,k=2)

    good_matches = []

    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    if len(good_matches) < 4:
        raise RuntimeError("Não foram encontrados pontos suficientes para alinhar o formulário.")

    image_points = np.float32([keypoints_image[match.queryIdx].pt for match in good_matches])

    template_points = np.float32([keypoints_template[match.trainIdx].pt for match in good_matches])

    homography, mask = cv.findHomography(
        image_points,
        template_points,
        cv.RANSAC,
        5.0
    )

    if homography is None:
        raise RuntimeError("Não foi possível calcular a homografia.")

    height, width = template.shape[:2]

    aligned = cv.warpPerspective(image,homography,(width, height),borderValue=(255, 255, 255))

    return aligned

def saveProcessedImage(
    image: np.ndarray,
    output_path: str
) -> None:

    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    extension = output.suffix

    success, encoded = cv.imencode(
        extension,
        image
    )

    if not success:
        raise RuntimeError(
            f"Não foi possível codificar a imagem: {output.name}"
        )

    encoded.tofile(
        str(output)
    )

    print(
        f"Imagem salva em: {output.resolve()}"
    )