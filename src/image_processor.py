from pathlib import Path

import cv2 as cv
import numpy as np
import pymupdf


def pdfToImage(pdf_path: str | Path, dpi: int = 300) -> list[np.ndarray]:
    """Converte as páginas de um PDF em imagens BGR."""

    images = []

    with pymupdf.open(str(pdf_path)) as doc:
        for page in doc:
            pixmap = page.get_pixmap(dpi=dpi, alpha=False)

            image = np.frombuffer(pixmap.samples, dtype=np.uint8)
            image = image.reshape(pixmap.height, pixmap.width, pixmap.n)
            image = cv.cvtColor(image, cv.COLOR_RGB2BGR)

            images.append(image)

    return images


def grayscaleImage(image: np.ndarray) -> np.ndarray:
    """Converte uma imagem BGR para tons de cinza."""

    return cv.cvtColor(image, cv.COLOR_BGR2GRAY)


def prepareTemplate(template: np.ndarray) -> dict:
    """Calcula os pontos de referência do formulário vazio para reutilização."""

    gray_template = grayscaleImage(template)
    orb = cv.ORB_create(nfeatures=5000)

    keypoints, descriptors = orb.detectAndCompute(gray_template, None)

    if descriptors is None or len(keypoints) < 4:
        raise RuntimeError("Não foi possível identificar pontos suficientes na página do formulário vazio.")

    return {
        "keypoints": keypoints,
        "descriptors": descriptors,
        "shape": template.shape[:2]
    }


def alignToTemplate(image: np.ndarray, template_data: dict) -> np.ndarray:
    """Alinha uma página preenchida utilizando os dados do formulário vazio."""

    gray_image = grayscaleImage(image)
    orb = cv.ORB_create(nfeatures=5000)

    keypoints_image, descriptors_image = orb.detectAndCompute(gray_image, None)

    if descriptors_image is None or len(keypoints_image) < 4:
        raise RuntimeError("Não foi possível identificar pontos suficientes na página preenchida.")

    matcher = cv.BFMatcher(cv.NORM_HAMMING)
    matches = matcher.knnMatch(descriptors_image, template_data["descriptors"], k=2)

    good_matches = []

    for pair in matches:
        if len(pair) < 2:
            continue

        m, n = pair

        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    if len(good_matches) < 4:
        raise RuntimeError("Não foram encontrados pontos suficientes para alinhar o formulário.")

    image_points = np.float32([keypoints_image[match.queryIdx].pt for match in good_matches])
    template_points = np.float32([template_data["keypoints"][match.trainIdx].pt for match in good_matches])

    homography, _ = cv.findHomography(image_points, template_points, cv.RANSAC, 5.0)

    if homography is None:
        raise RuntimeError("Não foi possível calcular a homografia.")

    height, width = template_data["shape"]

    return cv.warpPerspective(image, homography, (width, height), borderValue=(255, 255, 255))


def saveProcessedImage(image: np.ndarray, output_path: str | Path) -> None:
    """Salva uma imagem processada no caminho informado."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    success, encoded = cv.imencode(output.suffix, image)

    if not success:
        raise RuntimeError(f"Não foi possível codificar a imagem: {output.name}")

    encoded.tofile(str(output))

    print(f"Imagem salva em: {output.resolve()}")