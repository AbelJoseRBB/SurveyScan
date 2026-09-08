import cv2 as cv
import numpy as np


def cropRegion(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    return image[y1:y2, x1:x2]

def getGrayMean(region: np.ndarray) -> float:
    return float(np.mean(region))

def isMarked(region: np.ndarray, threshold: float = 245.0) -> bool:
    mean = float(np.mean(region))
    return getGrayMean(region) < threshold

def readMark(image: np.ndarray, coordinates: tuple[int, int, int, int], threshold: float = 245.0) -> bool:
    region = cropRegion(image, *coordinates)
    return isMarked(region, threshold)

def readSingleChoiceQuestion(image: np.ndarray, options: dict[str, tuple[int, int, int, int]], threshold: float = 245.0) -> str | None:
    for answer, coordinates in options.items():
        if readMark(image, coordinates, threshold):
            return answer
    return None


# função para teste
def getGrayStats(region: np.ndarray) -> tuple[float, int, int]:
    mean = float(np.mean(region))
    minimum = int(np.min(region))
    maximum = int(np.max(region))

    return mean, minimum, maximum


def drawTestX(
    image: np.ndarray,
    coordinates: tuple[int, int, int, int],
    thickness: int = 3
) -> np.ndarray:

    test_image = image.copy()

    x1, y1, x2, y2 = coordinates

    cv.line(
        test_image,
        (x1, y1),
        (x2, y2),
        255,
        thickness
    )

    cv.line(
        test_image,
        (x2, y1),
        (x1, y2),
        255,
        thickness
    )

    return test_image