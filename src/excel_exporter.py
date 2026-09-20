from pathlib import Path
import pandas as pd
from openpyxl.styles import PatternFill

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


def flattenQuestionnaire(questionnaire: dict) -> dict:
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

    return {columnName(field): value for field, value in row.items()}


def exportQuestionnaires(questionnaires: list[dict], output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    questionnaire_rows = [flattenQuestionnaire(questionnaire) for questionnaire in questionnaires]
    review_rows = [row for questionnaire in questionnaires for row in flattenReview(questionnaire)]

    questionnaire_df = pd.DataFrame(questionnaire_rows)

    review_columns = [
        "questionario", 
        "campo", 
        "valor_lido", 
        "trocr", 
        "easyocr", 
        "sugestao_trocr", 
        "sugestao_easyocr", 
        "imagem"
    ]
    review_df = pd.DataFrame(review_rows, columns=review_columns)

    with pd.ExcelWriter(output_path) as writer:
        questionnaire_df.to_excel(writer, index=False, sheet_name="Questionarios")
        review_df.to_excel(writer, index=False, sheet_name="Revisao")

        highlightReviewCells(writer.sheets["Questionarios"], questionnaires)

    print(f"\nPlanilha salva em: {output_path}")


def flattenReview(questionnaire: dict) -> list[dict]:
    rows = []
    form_id = questionnaire["identificador_processamento"]

    def addReview(field: str, value: str, trocr: str = "", easyocr: str = "", suggestion_trocr: str = "", suggestion_easyocr: str = "", image: str = "") -> None:
        rows.append({
            "questionario": form_id,
            "campo": field,
            "valor_lido": value,
            "trocr": trocr,
            "easyocr": easyocr,
            "sugestao_trocr": suggestion_trocr,
            "sugestao_easyocr": suggestion_easyocr,
            "imagem": image
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
            addReview(field, result["valor"])

    date_result = questionnaire["data_coleta"]

    if date_result["revisar"]:
        addReview("data_coleta", date_result["valor"])

    for field, result in questionnaire["manuscritas"].items():
        if not result["revisar"]:
            continue

        suggestions = result.get("sugestoes") or {}
        trocr_suggestion = (suggestions.get("trocr") or {}).get("sugestao") or ""
        easyocr_suggestion = (suggestions.get("easyocr") or {}).get("sugestao") or ""

        addReview(field, result["valor"], result.get("trocr", ""), result.get("easyocr", ""), trocr_suggestion, easyocr_suggestion, result.get("imagem", ""))

    return rows


def getHandwrittenValue(result: dict) -> str:
    """
    Retorna o valor a ser exibido na aba principal.
    Se houver revisão, tenta utilizar uma sugestão do RapidFuzz.
    """

    if not result["revisar"]:
        return result["valor"]

    suggestions = result.get("sugestoes") or {}
    trocr_suggestion = (suggestions.get("trocr") or {}).get("sugestao")
    easyocr_suggestion = (suggestions.get("easyocr") or {}).get("sugestao")

    # Usa a sugestão apenas quando os dois OCRs
    # apontam para a mesma palavra do vocabulário.
    if trocr_suggestion and trocr_suggestion == easyocr_suggestion:
        return trocr_suggestion
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