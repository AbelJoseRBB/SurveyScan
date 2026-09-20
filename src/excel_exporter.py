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

    row = {
        "identificador_processamento":
            questionnaire["identificador_processamento"]
    }

    # Respostas objetivas que não serão combinadas com outros campos
    combined_fields = {
        "religiao",
        "trabalha",
        "renda_mensal",
        "tem_filhos"
    }

    for field, value in objective.items():

        if field in combined_fields:
            continue

        if isinstance(value, dict):
            for subfield, subvalue in value.items():
                row[f"{field}_{subfield}"] = subvalue
        else:
            row[field] = value

    # Campos numéricos independentes
    row["questionario_numero"] = numeric["questionario_numero"]["valor"]
    row["idade"] = numeric["idade"]["valor"]

    # Religião: alternativa marcada ou resposta escrita
    if objective["religiao"] == "Outra":
        row["religiao"] = getHandwrittenValue(
            handwritten["religiao_outra"]
        )
    else:
        row["religiao"] = objective["religiao"]

    # Ocupação: substitui o Sim pela profissão escrita
    if objective["trabalha"] == "Sim":
        row["ocupacao"] = getHandwrittenValue(
            handwritten["ocupacao"]
        )
    elif objective["trabalha"] == "Não":
        row["ocupacao"] = "NÃO SE APLICA"
    else:
        row["ocupacao"] = objective["trabalha"]

    # Renda: substitui o Sim pelo valor informado
    if objective["renda_mensal"] == "Sim":
        row["renda_mensal"] = numeric["renda_valor"]["valor"]
    elif objective["renda_mensal"] == "Não":
        row["renda_mensal"] = "NÃO SE APLICA"
    else:
        row["renda_mensal"] = objective["renda_mensal"]

    # Filhos: substitui o Sim pela quantidade informada
    if objective["tem_filhos"] == "Sim":
        row["tem_filhos"] = numeric["quantidade_filhos"]["valor"]
    elif objective["tem_filhos"] == "Não":
        row["tem_filhos"] = 0
    else:
        row["tem_filhos"] = objective["tem_filhos"]

    # Data
    row["data_coleta"] = questionnaire["data_coleta"]["valor"]

    return {
        columnName(field): value
        for field, value in row.items()
    }


def exportQuestionnaires(questionnaires: list[dict], output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Aba principal
    questionnaire_rows = [
        flattenQuestionnaire(questionnaire)
        for questionnaire in questionnaires
    ]

    # Aba de revisão
    review_rows = []

    for questionnaire in questionnaires:
        review_rows.extend(flattenReview(questionnaire))

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

    review_df = pd.DataFrame(
        review_rows,
        columns=review_columns
    )

    with pd.ExcelWriter(output_path) as writer:

        questionnaire_df.to_excel(
            writer,
            index=False,
            sheet_name="Questionarios"
        )

        review_df.to_excel(
            writer,
            index=False,
            sheet_name="Revisao"
        )

        worksheet = writer.sheets["Questionarios"]

        highlightReviewCells(
            worksheet,
            questionnaires
        )

    print(f"\nPlanilha salva em: {output_path}")

def flattenReview(questionnaire: dict) -> list[dict]:

    rows = []

    form_id = questionnaire["identificador_processamento"]

    # Campos numéricos
    for field, result in questionnaire["numericas"].items():

        if result["revisar"]:
            rows.append({
                "questionario": form_id,
                "campo": field,
                "valor_lido": result["valor"],
                "trocr": "",
                "easyocr": "",
                "sugestao_trocr": "",
                "sugestao_easyocr": "",
                "imagem": ""
            })

    # Data de coleta
    date_result = questionnaire["data_coleta"]

    if date_result["revisar"]:
        rows.append({
            "questionario": form_id,
            "campo": "data_coleta",
            "valor_lido": date_result["valor"],
            "trocr": "",
            "easyocr": "",
            "sugestao_trocr": "",
            "sugestao_easyocr": "",
            "imagem": ""
        })

    # Campos manuscritos
    for field, result in questionnaire["manuscritas"].items():

        if not result["revisar"]:
            continue

        suggestions = result.get("sugestoes") or {}

        rows.append({
            "questionario": form_id,
            "campo": field,
            "valor_lido": result["valor"],
            "trocr": result.get("trocr", ""),
            "easyocr": result.get("easyocr", ""),
            "sugestao_trocr": (
                suggestions.get("trocr") or {}
            ).get("sugestao", ""),
            "sugestao_easyocr": (
                suggestions.get("easyocr") or {}
            ).get("sugestao", ""),
            "imagem": result.get("imagem", "")
        })

    return rows

def getHandwrittenValue(result: dict) -> str:
    """
    Retorna o valor a ser exibido na aba principal.
    Se houver revisão, tenta utilizar uma sugestão do RapidFuzz.
    """

    if not result["revisar"]:
        return result["valor"]

    suggestions = result.get("sugestoes") or {}

    trocr_suggestion = (
        suggestions.get("trocr") or {}
    ).get("sugestao")

    easyocr_suggestion = (
        suggestions.get("easyocr") or {}
    ).get("sugestao")

    # Usa a sugestão apenas quando os dois OCRs
    # apontam para a mesma palavra do vocabulário.
    if (
        trocr_suggestion
        and trocr_suggestion == easyocr_suggestion
    ):
        return trocr_suggestion

    return "VERIFICAR"



def highlightReviewCells(worksheet, questionnaires: list[dict]) -> None:

    yellow_fill = PatternFill(
        fill_type="solid",
        fgColor="FFF2CC"
    )

    red_fill = PatternFill(
        fill_type="solid",
        fgColor="F4CCCC"
    )

    columns = {
        cell.value: cell.column
        for cell in worksheet[1]
    }

    def highlight(row_number, field, value):

        column_name = columnName(field)

        if column_name not in columns:
            return

        cell = worksheet.cell(
            row=row_number,
            column=columns[column_name]
        )

        cell.fill = red_fill

    for row_number, questionnaire in enumerate(
        questionnaires,
        start=2
    ):

        objective = questionnaire["objetivas"]
        numeric = questionnaire["numericas"]
        handwritten = questionnaire["manuscritas"]

        # Campos numéricos independentes
        for field in ("questionario_numero", "idade"):

            result = numeric[field]

            if result["revisar"]:
                highlight(row_number, field, result["valor"])

        # Religião
        if (
            objective["religiao"] == "Outra"
            and handwritten["religiao_outra"]["revisar"]
        ):
            highlight(
                row_number,
                "religiao",
                getHandwrittenValue(handwritten["religiao_outra"])
            )

        # Ocupação
        if (
            objective["trabalha"] == "Sim"
            and handwritten["ocupacao"]["revisar"]
        ):
            highlight(
                row_number,
                "ocupacao",
                getHandwrittenValue(handwritten["ocupacao"])
            )

        # Renda
        if (
            objective["renda_mensal"] == "Sim"
            and numeric["renda_valor"]["revisar"]
        ):
            highlight(
                row_number,
                "renda_mensal",
                numeric["renda_valor"]["valor"]
            )

        # Quantidade de filhos
        if (
            objective["tem_filhos"] == "Sim"
            and numeric["quantidade_filhos"]["revisar"]
        ):
            highlight(
                row_number,
                "tem_filhos",
                numeric["quantidade_filhos"]["valor"]
            )

        # Data
        date_result = questionnaire["data_coleta"]

        if date_result["revisar"]:
            highlight(
                row_number,
                "data_coleta",
                date_result["valor"]
            )