from config import INPUT_DIR, OUTPUT_DIR, QUESTION_COORDINATES, TEXT_FIELDS, ANO_COLETA, EXCEL_FILE
from image_processor import pdfToImage, alignToTemplate, grayscaleImage, prepareTemplate
from readers.answer_reader import readForm
from readers.text_reader import loadDigitModels, readNumericFields, readDate
from readers.handwriting_reader import loadHandwritingModel
from readers.easyocr_reader import loadEasyOCR
from readers.handwriting_comparison import readHandwrittenFields
from excel_exporter import exportQuestionnaires
import hashlib 


TEMPLATE_FILE = INPUT_DIR / "FormsVazio.pdf"

def generateFormID(pdf_path) -> str:
    file_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    return file_hash[:12]


def processQuestionnaire(pdf_path, form_id, template_data, svm_model, knn_model, processor, trocr_model, easyocr_reader):
    print(f"\nProcessando questionário {form_id}: {pdf_path.name}")

    form_pages = pdfToImage(pdf_path)

    if len(form_pages) != len(template_data):
        raise ValueError(f"Quantidade de páginas incompatível: esperado {len(template_data)}, recebido {len(form_pages)}.")

    processed_pages = {}

    for i, form_page in enumerate(form_pages):
        aligned_page = alignToTemplate(form_page, template_data[i])
        processed_pages[i + 1] = grayscaleImage(aligned_page)

    objective_answers = readForm(processed_pages, QUESTION_COORDINATES)
    numeric_answers = readNumericFields(processed_pages[1], TEXT_FIELDS[1], objective_answers, svm_model, knn_model, form_id, OUTPUT_DIR/ "revisao")

    date_value, date_review = readDate(processed_pages[2], TEXT_FIELDS[2]["data_coleta"], ANO_COLETA, svm_model, knn_model)
    date_answer = {"valor": date_value, "revisar": date_review}

    handwritten_answers = readHandwrittenFields(processed_pages[1], TEXT_FIELDS[1], objective_answers, form_id, processor, trocr_model, easyocr_reader, OUTPUT_DIR / "revisao")

    return {
        "identificador_processamento": form_id,
        "objetivas": objective_answers,
        "numericas": numeric_answers,
        "data_coleta": date_answer,
        "manuscritas": handwritten_answers
    }


def main():
    pdf_files = sorted(pdf_path for pdf_path in INPUT_DIR.glob("*.pdf") if pdf_path.name.lower() != TEMPLATE_FILE.name.lower())

    if not pdf_files:
        print("Nenhum questionário encontrado na pasta de formulários.")
        return

    print("Carregando formulário vazio...")
    template_pages = pdfToImage(TEMPLATE_FILE)
    template_data = [prepareTemplate(page) for page in template_pages]

    print("Carregando modelos numéricos...")
    svm_model, knn_model = loadDigitModels()

    print("Carregando modelos de escrita manuscrita...")
    processor, trocr_model = loadHandwritingModel()
    easyocr_reader = loadEasyOCR()

    questionnaires = []
    errors = []

    for index, pdf_path in enumerate(pdf_files, start=1):

        form_id = generateFormID(pdf_path)

        try:
            result = processQuestionnaire(pdf_path, form_id, template_data, svm_model, knn_model, processor, trocr_model, easyocr_reader)
            questionnaires.append(result)
            print(f"Questionário {form_id} processado com sucesso.")
        except Exception as error:
            errors.append((pdf_path.name, str(error)))
            print(f"Erro ao processar {pdf_path.name}: {error}")

    if questionnaires:
        exportQuestionnaires(questionnaires=questionnaires, output_path=EXCEL_FILE)
    else:
        print("\nNenhum questionário foi processado com sucesso.")

    print(f"\nProcessamento concluído: {len(questionnaires)} de {len(pdf_files)} questionários.")

    if errors:
        print("\n=== FORMULÁRIOS COM ERRO ===")
        for filename, error in errors:
            print(f"- {filename}: {error}")


if __name__ == "__main__":
    main()