import numpy as np

def cropRegion(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    # Recorta uma região da imagem.
    return image[y1:y2, x1:x2]


def isMarked(region: np.ndarray, threshold: float = 245.0) -> bool:
    # Verifica se a região está marcada com base na intensidade média dos pixels.
    if region.size == 0:
        raise ValueError("Não foi possível verificar a marcação: região da imagem vazia.")

    return float(np.mean(region)) < threshold


def readMark(image: np.ndarray, coordinates: tuple[int, int, int, int], threshold: float = 245.0) -> bool:
    # Verifica se uma alternativa está marcada.
    region = cropRegion(image, *coordinates)
    return isMarked(region, threshold)


def readSingleChoiceQuestion(image: np.ndarray, options: dict[str, tuple[int, int, int, int]], threshold: float = 245.0) -> str:
    # Lê uma questão de escolha única.
    marked_answers = []

    for answer, coordinates in options.items():
        if readMark(image, coordinates, threshold):
            marked_answers.append(answer)

    if not marked_answers:
        return "EM BRANCO"

    if len(marked_answers) > 1:
        return "AMBÍGUA"

    return marked_answers[0]


def readForm(pages: dict[int, np.ndarray], question_coordinates: dict) -> dict:
    # Lê as respostas objetivas de todas as páginas configuradas.
    answers = {}

    for page_number, questions in question_coordinates.items():
        image = pages[page_number]

        for question_name, options in questions.items():
            if question_name == "q12":
                answers["q12"] = {
                    subquestion_name: readSingleChoiceQuestion(image, sub_options)
                    for subquestion_name, sub_options in options.items()
                }
            else:
                answers[question_name] = readSingleChoiceQuestion(image, options)

    return answers