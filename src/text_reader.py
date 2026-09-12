import cv2 as cv
import numpy as np

def cropTextField(
    image: np.ndarray,
    coordinates: tuple[int, int, int, int]
) -> np.ndarray:

    x1, y1, x2, y2 = coordinates

    return image[
        y1:y2,
        x1:x2
    ]


def segmentDigits(
    image: np.ndarray
) -> list[np.ndarray]:

    # Garante que a imagem esteja em escala de cinza
    if len(image.shape) == 3:
        gray = cv.cvtColor(
            image,
            cv.COLOR_BGR2GRAY
        )
    else:
        gray = image.copy()

    # Binarização invertida:
    # fundo = 0
    # escrita = 255
    binary = cv.threshold(
        gray,
        0,
        255,
        cv.THRESH_BINARY_INV + cv.THRESH_OTSU
    )[1]

    # Detecta linhas horizontais longas
    horizontal_kernel = cv.getStructuringElement(
        cv.MORPH_RECT,
        (80, 1)
    )

    horizontal_lines = cv.morphologyEx(
        binary,
        cv.MORPH_OPEN,
        horizontal_kernel
    )

    # Remove a linha do formulário
    without_lines = cv.subtract(
        binary,
        horizontal_lines
    )

    # Procura os componentes restantes
    contours, _ = cv.findContours(
        without_lines,
        cv.RETR_EXTERNAL,
        cv.CHAIN_APPROX_SIMPLE
    )

    digit_regions = []

    for contour in contours:

        x, y, w, h = cv.boundingRect(
            contour
        )

        # Ignora pequenos ruídos
        if h < 15 or w < 3:
            continue

        area = cv.contourArea(
            contour
        )

        if area < 30:
            continue

        digit_regions.append(
            (x, y, w, h)
        )

    # Ordena os dígitos da esquerda para direita
    digit_regions.sort(
        key=lambda region: region[0]
    )

    digits = []

    for x, y, w, h in digit_regions:

        digit = without_lines[
            y:y + h,
            x:x + w
        ]

        digits.append(
            digit
        )

    return digits

def normalizeDigit(
    digit: np.ndarray,
    size: int = 28
) -> np.ndarray:

    # Encontra o tamanho atual
    height, width = digit.shape[:2]

    # Cria uma imagem quadrada com margem
    side = max(height, width) + 20

    canvas = np.zeros(
        (side, side),
        dtype=np.uint8
    )

    # Centraliza o dígito
    x_offset = (side - width) // 2
    y_offset = (side - height) // 2

    canvas[
        y_offset:y_offset + height,
        x_offset:x_offset + width
    ] = digit

    # Redimensiona para 28x28
    normalized = cv.resize(
        canvas,
        (size, size),
        interpolation=cv.INTER_AREA
    )

    return normalized


