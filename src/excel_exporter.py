from pathlib import Path
import pandas as pd
from openpyxl.styles import PatternFill
from openpyxl.drawing.image import Image as ExcelImage

COLUMN_NAMES = {
    "identificador_processamento": "ID",
    "questionario_numero": "Nº do questionário",
    "idade": "Idade",
    "sexo": "Sexo",
    "cor": "Cor",
    "estado_civil": "Estado civil",
    "religiao": "Religião",
    "ocupacao": "Ocupação",
    "renda_mensal": "Renda mensal (R$)",
    "tem_filhos": "Nº Filhos",
    "periodo_academico": "Período acadêmico",
    "data_coleta": "Data da coleta",

    "q10_ouviu_falar": "Q10",
    "q11_definicao": "Q11",

    "q12_procedimento_sem_consentimento": "Q12.1",
    "q12_gritar_humilhar": "Q12.2",
    "q12_episiotomia_rotina": "Q12.3",
    "q12_impedir_acompanhante": "Q12.4",
    "q12_negar_alivio_dor": "Q12.5",
    "q12_comentarios_ofensivos": "Q12.6",
    "q12_ocitocina_sem_explicacao": "Q12.7",

    "q13_autoavaliacao": "Q13"
}

def columnName(field: str) -> str:
    return COLUMN_NAMES.get(field, field)

def insertReviewImages(worksheet, review_rows: list[dict]) -> None:
    image_column = 4
    worksheet.column_dimensions["D"].width = 35

    for row_number, review in enumerate(review_rows, start=2):
        image_path = review.get("imagem")

        if not image_path or not Path(image_path).exists():
            continue

        image = ExcelImage(image_path)

        max_width = 250
        max_height = 80
        scale = min(max_width / image.width, max_height / image.height)

        image.width *= scale
        image.height *= scale

        worksheet.row_dimensions[row_number].height = image.height * 0.75
        worksheet.add_image(image, f"D{row_number}")
        worksheet.cell(row=row_number, column=image_column).value = ""

def flattenQuestionnaire(questionnaire: dict, manual_corrections: dict) -> dict:
    objective = questionnaire["objetivas"]
    numeric = questionnaire["numericas"]
    handwritten = questionnaire["manuscritas"]

    row = {"identificador_processamento": questionnaire["identificador_processamento"]}
    combined_fields = {"religiao", "trabalha", "renda_mensal", "tem_filhos"}

    for field, value in objective.items():
        if field in combined_fields:
            continue

        if isinstance(value, dict):
            for subfield, subvalue in value.items():
                row[f"{field}_{subfield}"] = subvalue
        else:
            row[field] = value

    row["questionario_numero"] = numeric["questionario_numero"]["valor"]
    row["idade"] = numeric["idade"]["valor"]

    if objective["religiao"] == "Outra":
        row["religiao"] = getHandwrittenValue(handwritten["religiao_outra"])
    else:
        row["religiao"] = objective["religiao"]

    if objective["trabalha"] == "Sim":
        row["ocupacao"] = getHandwrittenValue(handwritten["ocupacao"])
    elif objective["trabalha"] == "Não":
        row["ocupacao"] = "NÃO SE APLICA"
    else:
        row["ocupacao"] = objective["trabalha"]

    if objective["renda_mensal"] == "Sim":
        row["renda_mensal"] = numeric["renda_valor"]["valor"]
    elif objective["renda_mensal"] == "Não":
        row["renda_mensal"] = "NÃO SE APLICA"
    else:
        row["renda_mensal"] = objective["renda_mensal"]

    if objective["tem_filhos"] == "Sim":
        row["tem_filhos"] = numeric["quantidade_filhos"]["valor"]
    elif objective["tem_filhos"] == "Não":
        row["tem_filhos"] = 0
    else:
        row["tem_filhos"] = objective["tem_filhos"]

    row["data_coleta"] = questionnaire["data_coleta"]["valor"]

    form_id = str(questionnaire["identificador_processamento"])
    for(correction_id, field), correction in manual_corrections.items():
        if correction_id != form_id:
            continue
        
        if field in row:
            row[field] = correction

    return {columnName(field): value for field, value in row.items()}

def loadManualCorrections(output_path: Path)-> dict:
    if not output_path.exists():
        return {}
    try:
        review_df = pd.read_excel(output_path, sheet_name="Revisao")
    except (FileNotFoundError, ValueError):
        return {}
    if "correcao_manual" not in review_df.columns:
        return {}

    corrections = {}

    for _, row in review_df.iterrows():
        correction = row["correcao_manual"]

        if pd.isna(correction) or not str(correction).strip():
            continue

        key = (str(row["questionario"]), str(row["campo"]))
        corrections[key] = str(correction).strip()
    
    return corrections

def exportQuestionnaires(questionnaires: list[dict], output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manual_corrections = loadManualCorrections(output_path)
    questionnaire_rows = [flattenQuestionnaire(questionnaire, manual_corrections) for questionnaire in questionnaires]
    review_rows = [row for questionnaire in questionnaires for row in flattenReview(questionnaire, manual_corrections)]

    questionnaire_df = pd.DataFrame(questionnaire_rows)

    review_columns = [
        "questionario", 
        "campo", 
        "valor_lido", 
        "imagem",
        "correcao_manual"
    ]
    review_df = pd.DataFrame(review_rows, columns=review_columns)

    with pd.ExcelWriter(output_path) as writer:
        questionnaire_df.to_excel(writer, index=False, sheet_name="Questionarios")
        review_df.to_excel(writer, index=False, sheet_name="Revisao")

        review_sheet = writer.sheets["Revisao"]
        insertReviewImages(review_sheet, review_rows)
        highlightReviewCells(writer.sheets["Questionarios"], questionnaires)

    print(f"\nPlanilha salva em: {output_path}")


def flattenReview(questionnaire: dict, manual_corrections: dict) -> list[dict]:
    rows = []
    form_id = questionnaire["identificador_processamento"]

    def addReview(field: str, value: str, trocr: str = "", easyocr: str = "", suggestion_trocr: str = "", suggestion_easyocr: str = "", image: str = "") -> None:
        key = (str(questionnaire["identificador_processamento"]), field)
        correction = manual_corrections.get(key, "")
        rows.append({
            "questionario": form_id,
            "campo": field,
            "valor_lido": value,
            "trocr": trocr,
            "easyocr": easyocr,
            "sugestao_trocr": suggestion_trocr,
            "sugestao_easyocr": suggestion_easyocr,
            "imagem": image,
            "correcao_manual": correction
        })

    for field, value in questionnaire["objetivas"].items():
        if isinstance(value, dict):
            for subfield, subvalue in value.items():
                if subvalue == "AMBÍGUA":
                    addReview(f"{field}_{subfield}", subvalue)
        elif value == "AMBÍGUA":
            addReview(field, value)

    for field, result in questionnaire["numericas"].items():
        if result["revisar"]:
            addReview(field, result["valor"], image=result.get("imagem", ""))

    date_result = questionnaire["data_coleta"]

    if date_result["revisar"]:
        addReview("data_coleta", date_result["valor"])

    for field, result in questionnaire["manuscritas"].items():
        if not result["revisar"]:
            continue

        suggestions = result.get("sugestoes") or {}
        trocr_suggestion = (suggestions.get("trocr") or {}).get("sugestao") or ""
        easyocr_suggestion = (suggestions.get("easyocr") or {}).get("sugestao") or ""

        value_read = result.get("trocr", "").strip()

        if not value_read:
            value_read = result.get("easyocr", "").strip()

        if not value_read:
            value_read = result.get("valor", "VERIFICAR")

        addReview(field, value_read, result.get("trocr", ""), result.get("easyocr", ""), trocr_suggestion, easyocr_suggestion, result.get("imagem", ""))

    return rows


def getHandwrittenValue(result: dict) -> str:
    if not result["revisar"]:
        return result["valor"]

    suggestions = result.get("sugestoes") or {}
    trocr_suggestion = (suggestions.get("trocr") or {}).get("sugestao")
    easyocr_suggestion = (suggestions.get("easyocr") or {}).get("sugestao")

    if trocr_suggestion and trocr_suggestion == easyocr_suggestion:
        return trocr_suggestion

    trocr_text = result.get("trocr", "").strip()
    easyocr_text = result.get("easyocr", "").strip()

    if trocr_text and trocr_text != "ERRO NO RECORTE":
        return trocr_text

    if easyocr_text and easyocr_text != "ERRO NO RECORTE":
        return easyocr_text

    return "VERIFICAR"


def highlightReviewCells(worksheet, questionnaires: list[dict]) -> None:
    yellow_fill = PatternFill(fill_type="solid", fgColor="FFF2CC")
    red_fill = PatternFill(fill_type="solid", fgColor="F4CCCC")

    columns = {cell.value: cell.column for cell in worksheet[1]}

    def highlight(row_number: int, field: str) -> None:
        column = columns.get(columnName(field))

        if column is None:
            return

        cell = worksheet.cell(row=row_number, column=column)
        cell.fill = red_fill if cell.value in ("VERIFICAR", "AMBÍGUA", "EM BRANCO") else yellow_fill

    for row_number, questionnaire in enumerate(questionnaires, start=2):
        objective = questionnaire["objetivas"]
        numeric = questionnaire["numericas"]
        handwritten = questionnaire["manuscritas"]

        # Questões objetivas ambíguas
        for field, value in objective.items():
            if isinstance(value, dict):
                for subfield, subvalue in value.items():
                    if subvalue == "AMBÍGUA":
                        highlight(row_number, f"{field}_{subfield}")
            elif value == "AMBÍGUA" and field not in {"religiao", "trabalha", "renda_mensal", "tem_filhos"}:
                highlight(row_number, field)

        # Campos numéricos independentes
        for field in ("questionario_numero", "idade"):
            if numeric[field]["revisar"]:
                highlight(row_number, field)

        # Religião e ocupação
        if objective["religiao"] == "Outra":
            if handwritten["religiao_outra"]["revisar"]:
                highlight(row_number, "religiao")
        elif objective["religiao"] == "AMBÍGUA":
            highlight(row_number, "religiao")

        if objective["trabalha"] == "Sim":
            if handwritten["ocupacao"]["revisar"]:
                highlight(row_number, "ocupacao")
        elif objective["trabalha"] not in {"Sim", "Não"}:
            highlight(row_number, "ocupacao")

        # Renda e quantidade de filhos
        if numeric["renda_valor"]["revisar"]:
            highlight(row_number, "renda_mensal")

        if numeric["quantidade_filhos"]["revisar"]:
            highlight(row_number, "tem_filhos")

        # Data
        if questionnaire["data_coleta"]["revisar"]:
            highlight(row_number, "data_coleta")