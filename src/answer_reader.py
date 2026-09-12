import numpy as np

def cropRegion(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    return image[y1:y2, x1:x2]

def getGrayMean(region: np.ndarray) -> float:
    return float(np.mean(region))

def isMarked(region: np.ndarray, threshold: float = 245.0) -> bool:
    return getGrayMean(region) < threshold

def readMark(image: np.ndarray, coordinates: tuple[int, int, int, int], threshold: float = 245.0) -> bool:
    region = cropRegion(image, *coordinates)
    return isMarked(region, threshold)

def readSingleChoiceQuestion(image: np.ndarray, options: dict[str, tuple[int, int, int, int]], threshold: float = 245.0) -> str | None:
    marked_answers = []

    for answer, coordinates in options.items():
        if readMark(image, coordinates, threshold):
            marked_answers.append(answer)

    if len(marked_answers) == 0:
        return "EM BRANCO"
    if len(marked_answers) > 1:
        return "AMBÍGUA"
    
    return marked_answers[0]

def readForm(pages: dict[int, np.ndarray], question_coordinates: dict) -> dict:
    answers = {}

    # Página 1
    for question_name, options in question_coordinates[1].items():

        # Q12 possuoi subquestoes
        if question_name == "q12":
            q12_answers = {}

            for subquestion_name, sub_options in options.items():
                q12_answers[subquestion_name] = readSingleChoiceQuestion(pages[1], sub_options)
                answers["q12"] = q12_answers

        else:
            answers[question_name] = readSingleChoiceQuestion(pages[1], options)

    # Página 2
    for question_name, options in question_coordinates[2].items():
        answers[question_name] = readSingleChoiceQuestion(pages[2], options)

    return answers    