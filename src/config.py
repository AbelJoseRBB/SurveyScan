from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

INPUT_DIR = BASE_DIR / "formularios"
OUTPUT_DIR = BASE_DIR / "output"

EXCEL_FILE = OUTPUT_DIR / "resultado.xlsx"