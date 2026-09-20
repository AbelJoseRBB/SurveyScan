import cv2 as cv
import numpy as np
from pathlib import Path
from readers.handwriting_reader import readHandwriting
from readers.easyocr_reader import readHandwritingEasyOCR
from readers.fuzz_matcher import suggestText, OCCUPATIONS, RELIGIONS    

def compareHandwriting(image: np.ndarray, coordinates: tuple[int, int, int, int], field_name: str, form_id: str, processor, trocr_model, easyocr_reader, output_dir: Path) -> dict:
    # Reconhecimento com os dois modelos
    trocr_text = readHandwriting(image, coordinates, processor, trocr_model)
    easyocr_text = readHandwritingEasyOCR(image, coordinates, easyocr_reader)

    # Comparação das transições 
    agreement = ( bool(trocr_text) and bool(easyocr_text) and trocr_text.casefold() == easyocr_text.casefold())

    # Sugestão rapid fuzz
    suggestions = None
    vocabularies = {"ocupacao": OCCUPATIONS, "religiao_outra": RELIGIONS}

    if not agreement and field_name in vocabularies:
        vocabulary = vocabularies[field_name]
        suggestions = {
            "trocr": suggestText(trocr_text, vocabulary),
            "easyocr": suggestText(easyocr_text, vocabulary)
        }

    # Salvar a imagem original do campo
    x1, y1, x2, y2 = coordinates
    cropped = image[y1:y2, x1:x2]

    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"questionario_{form_id}_{field_name}.png"
    saved_image = ""

    if cropped.size > 0:
        success, encoded = cv.imencode(".png", cropped)

        if success:
            encoded.tofile(str(image_path))
            saved_image = str(image_path)

    return {
        "valor": trocr_text if agreement else "VERIFICAR",
        "trocr": trocr_text,
        "easyocr": easyocr_text,
        "concordancia": agreement,
        "sugestoes": suggestions,
        "revisar": not agreement or not bool(saved_image),
        "imagem": saved_image 
    }

def readHandwrittenFields(image: np.ndarray, text_fields: dict, objective_answers: dict, form_id: str, processor, trocr_model, easyocr_reader, output_dir: Path)->dict:

    results =  {}

    # Religião: ler somente quando a alternativa "Outra" estiver marcada.
    religiao = objective_answers.get("religiao")

    if religiao == "Outra":
        results["religiao_outra"] = compareHandwriting(
            image= image,
            coordinates= text_fields["religiao_outra"],
            field_name= "religiao_outra",
            form_id=form_id,
            processor= processor,
            trocr_model=trocr_model,
            easyocr_reader= easyocr_reader,
            output_dir= output_dir
        )
    elif religiao in {"Católica", "Protestante", "Espírita", "Sem Religião"}:
        results["religiao_outra"] = {
            "valor": "NÃO SE APLICA",
            "revisar": False
        }
    else:
        results["religiao_outra"] = {
            "valor": "VERIFICAR",
            "revisar": True
        }

    # Ocupação: ler somente quando a pessoa informar que trabalha.
    trabalha = objective_answers.get("trabalha")
    if trabalha == "Sim":
        results["ocupacao"] = compareHandwriting(
            image=image,
            coordinates=text_fields["ocupacao"],
            field_name="ocupacao",
            form_id=form_id,
            processor=processor,
            trocr_model=trocr_model,
            easyocr_reader=easyocr_reader,
            output_dir=output_dir
        )
    elif trabalha == "Não":
        results["ocupacao"] = {
            "valor": "NÃO SE APLICA",
            "revisar": False
        }
    else:
        results["ocupacao"] = {
            "valor": "VERIFICAR",
            "revisar": True
        }
    return results