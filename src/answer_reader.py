import cv2 as cv
import numpy as np


def cropRegion(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    return image[y1:y2, x1:x2]


def getFillScore(region: np.ndarray) -> int:
    return cv.countNonZero(region)

def isMarked(region: np.ndarray, threshold: int = 30) -> bool:
    return getFillScore(region) > threshold

def readMark(image: np.ndarray, coordinates: tuple[int, int, int, int], threshold: int = 30) -> bool:

    region = cropRegion(
        image,
        *coordinates
    )

    return isMarked(
        region,
        threshold
    )


# função para teste
def drawTestX(region: np.ndarray, margin: int = 10, thickness: int = 3) -> np.ndarray:

    test_region = region.copy()

    height, width = test_region.shape[:2]

    cv.line(
        test_region,
        (margin, margin),
        (width - margin, height - margin),
        255,
        thickness
    )

    cv.line(
        test_region,
        (width - margin, margin),
        (margin, height - margin),
        255,
        thickness
    )

    return test_region