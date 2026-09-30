from pathlib import Path
import pandas as pd
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
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


def loadManualCorrections(output_path: Path) -> dict:
    if not output_path.exists():
        return {}

    corrections = {}

    for sheet_name in ("Correcoes", "Revisao"):
        try:
            df = pd.read_excel(output_path, sheet_name=sheet_name)
        except (FileNotFoundError, ValueError):
            continue

        if not {"ID", "Campo", "Correção"}.issubset(df.columns):
            continue

        for _, row in df.iterrows():
            correction = row["Correção"]

            if pd.isna(correction) or not str(correction).strip():
                continue

            key = (str(row["ID"]), str(row["Campo"]))
            corrections[key] = str(correction).strip()

    return corrections


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


def flattenQuestionnaire(questionnaire: dict, manual_corrections: dict) -> dict:
    objective = questionnaire["objetivas"]
    numeric = questionnaire["numericas"]
    handwritten = questionnaire["manuscritas"]

    form_id = str(questionnaire["identificador_processamento"])

    questionario_numero = numeric["questionario_numero"]["valor"]
    idade = numeric["idade"]["valor"]

    if objective["religiao"] == "Outra":
        religiao = getHandwrittenValue(handwritten["religiao_outra"])
    else:
        religiao = objective["religiao"]

    if objective["trabalha"] == "Sim":
        ocupacao = getHandwrittenValue(handwritten["ocupacao"])
    elif objective["trabalha"] == "Não":
        ocupacao = "NÃO SE APLICA"
    else:
        ocupacao = objective["trabalha"]

    if objective["renda_mensal"] == "Sim":
        renda_mensal = numeric["renda_valor"]["valor"]
    elif objective["renda_mensal"] == "Não":
        renda_mensal = "NÃO SE APLICA"
    else:
        renda_mensal = objective["renda_mensal"]

    if objective["tem_filhos"] == "Sim":
        tem_filhos = numeric["quantidade_filhos"]["valor"]
    elif objective["tem_filhos"] == "Não":
        tem_filhos = 0
    else:
        tem_filhos = objective["tem_filhos"]

    row = {
        "identificador_processamento": questionnaire["identificador_processamento"],
        "questionario_numero": questionario_numero,
        "data_coleta": questionnaire["data_coleta"]["valor"],
        "idade": idade,
        "sexo": objective["sexo"],
        "cor": objective["cor"],
        "estado_civil": objective["estado_civil"],
        "religiao": religiao,
        "ocupacao": ocupacao,
        "renda_mensal": renda_mensal,
        "tem_filhos": tem_filhos,
        "periodo_academico": objective["periodo_academico"],
        "q10_ouviu_falar": objective["q10_ouviu_falar"],
        "q11_definicao": objective["q11_definicao"]
    }

    for field, value in objective.items():
        if isinstance(value, dict):
            for subfield, subvalue in value.items():
                row[f"{field}_{subfield}"] = subvalue
                
    row["q12_ocitocina_sem_explicacao"] = objective["q12_ocitocina_sem_explicacao"]
    row["q13_autoavaliacao"] = objective["q13_autoavaliacao"]

    correction_fields = {
        "religiao_outra": "religiao",
        "renda_valor": "renda_mensal",
        "quantidade_filhos": "tem_filhos"
    }

    for (correction_id, field), correction in manual_corrections.items():
        if correction_id != form_id:
            continue

        target_field = correction_fields.get(field, field)

        if target_field in row:
            row[target_field] = correction

    return {columnName(field): value for field, value in row.items()}


def flattenReview(questionnaire: dict, manual_corrections: dict) -> list[dict]:
    rows = []
    form_id = questionnaire["identificador_processamento"]

    def addReview(field: str, value: str, trocr: str = "", easyocr: str = "", suggestion_trocr: str = "", suggestion_easyocr: str = "", image: str = "") -> None:
        key = (str(questionnaire["identificador_processamento"]), field)
        correction = manual_corrections.get(key, "")

        if correction:
            return
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


def formatWorksheet(worksheet) -> None:
    header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True)

    border_side = Side(style="thin", color="D9E2F3")
    cell_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

    worksheet.freeze_panes = "A2"

    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.sheet_view.showGridLines =False

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = cell_border

    worksheet.row_dimensions[1].height = 24

    for column in range(1, worksheet.max_column + 1):
        column_letter = get_column_letter(column)
        max_length = 0

        for cell in worksheet[column_letter]:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))

        worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 10), 20)

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="center")
            cell.border = cell_border

    if worksheet.title == "Questionarios":
        centered_columns = {
            "Nº do questionário",
            "Data da coleta",
            "Idade",
            "Sexo",
            "Cor",
            "Estado civil",
            "Nº Filhos",
            "Período acadêmico",
            "Q10",
            "Q12.1",
            "Q12.2",
            "Q12.3",
            "Q12.4",
            "Q12.5",
            "Q12.6",
            "Q12.7",
            "Q13"
        }

        columns = {cell.value: cell.column for cell in worksheet[1]}

        date_column = columns.get("Data da coleta")

        if date_column is not None:
            for row_number in range(2, worksheet.max_row + 1):
                worksheet.cell(row=row_number, column=date_column).number_format = "dd/mm/yyyy"

        for column_name in centered_columns:
            column = columns.get(column_name)

            if column is None:
                continue

            for row_number in range(2, worksheet.max_row + 1):
                worksheet.cell(row=row_number, column=column).alignment = Alignment(horizontal="center", vertical="center")

        q11_column = columns.get("Q11")

        if q11_column is not None:
            q11_letter = get_column_letter(q11_column)
            worksheet.column_dimensions[q11_letter].width = 25

            for row_number in range(2, worksheet.max_row + 1):
                worksheet.cell(row=row_number, column=q11_column).alignment = Alignment(vertical="center", wrap_text=True)

        id_column = columns.get("ID")

        if id_column is not None:
            worksheet.column_dimensions[get_column_letter(id_column)].width = 15

    for column in range(worksheet.max_column + 1, 16385):
        worksheet.column_dimensions[get_column_letter(column)].hidden =True


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


def highlightReviewCells(worksheet, questionnaires: list[dict], manual_corrections: dict) -> None:
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
        form_id = str(questionnaire["identificador_processamento"])
        def isCorrected(field: str) -> bool:
            return (form_id, field) in manual_corrections
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
            if numeric[field]["revisar"] and not isCorrected(field):
                highlight(row_number, field)

        # Religião e ocupação
        if objective["religiao"] == "Outra":
            if handwritten["religiao_outra"]["revisar"] and not isCorrected("religiao_outra"):
                highlight(row_number, "religiao")
        elif objective["religiao"] == "AMBÍGUA":
            highlight(row_number, "religiao")

        if objective["trabalha"] == "Sim":
            if handwritten["ocupacao"]["revisar"] and not isCorrected("ocupacao"):
                highlight(row_number, "ocupacao")
        elif objective["trabalha"] not in {"Sim", "Não"}:
            highlight(row_number, "ocupacao")

        # Renda e quantidade de filhos
        if numeric["renda_valor"]["revisar"] and not isCorrected("renda_valor"):
            highlight(row_number, "renda_mensal")

        if numeric["quantidade_filhos"]["revisar"] and not isCorrected("quantidade_filhos"):
            highlight(row_number, "tem_filhos")

        # Data
        if questionnaire["data_coleta"]["revisar"] and not isCorrected("data_coleta"):
            highlight(row_number, "data_coleta")


def exportQuestionnaires(questionnaires: list[dict], output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manual_corrections = loadManualCorrections(output_path)
    questionnaire_rows = [flattenQuestionnaire(questionnaire, manual_corrections) for questionnaire in questionnaires]
    review_rows = [row for questionnaire in questionnaires for row in flattenReview(questionnaire, manual_corrections)]

    questionnaire_df = pd.DataFrame(questionnaire_rows)
    questionnaire_df = questionnaire_df.replace("", pd.NA)
    questionnaire_df = questionnaire_df.dropna(axis=1, how="all")

    integer_columns = [
        "Nº do questionário",
        "Idade",
        "Nº Filhos"
    ]

    for column in integer_columns:
        if column in questionnaire_df.columns:
            questionnaire_df[column] = pd.to_numeric(questionnaire_df[column], errors="coerce").astype("Int64")

    if "Data da coleta" in questionnaire_df.columns:
        questionnaire_df["Data da coleta"] = pd.to_datetime(questionnaire_df["Data da coleta"], format="%d/%m/%Y", errors="coerce")

    review_columns = [
        "questionario", 
        "campo", 
        "valor_lido", 
        "imagem",
        "correcao_manual"
    ]

    review_df = pd.DataFrame(review_rows, columns=review_columns)

    review_df = review_df.rename(columns={
        "questionario": "ID",
        "campo": "Campo",
        "valor_lido": "Valor lido",
        "imagem": "Imagem",
        "correcao_manual": "Correção"
    })

    correction_rows = []

    for (form_id, field), correction in manual_corrections.items():
        correction_rows.append({
            "ID": form_id,
            "Campo": field,
            "Correção": correction
        })

    corrections_df = pd.DataFrame(correction_rows, columns=["ID", "Campo", "Correção"])

    with pd.ExcelWriter(output_path) as writer:
        questionnaire_df.to_excel(writer, index=False, sheet_name="Questionarios")
        review_df.to_excel(writer, index=False, sheet_name="Revisao")
        corrections_df.to_excel(writer, index=False, sheet_name="Correcoes")

        questionnaire_sheet = writer.sheets["Questionarios"]
        review_sheet = writer.sheets["Revisao"]
        corrections_sheet = writer.sheets["Correcoes"]

        formatWorksheet(questionnaire_sheet)
        formatWorksheet(review_sheet)
        formatWorksheet(corrections_sheet)
        insertReviewImages(review_sheet, review_rows)
        highlightReviewCells(writer.sheets["Questionarios"], questionnaires, manual_corrections)

    print(f"\nPlanilha salva em: {output_path}")
