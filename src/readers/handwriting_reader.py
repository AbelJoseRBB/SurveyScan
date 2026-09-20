import cv2 as cv
import numpy as np
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

MODEL_NAME = "microsoft/trocr-base-handwritten"

def loadHandwritingModel():
    processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
    model.eval()

    return processor, model

def readHandwriting(image: np.ndarray, coordinates: tuple[int, int, int, int], processor, model)->str:
    x1, y1, x2, y2 = coordinates
    height = image.shape[0]

    cropped = image[y1:y2, x1:x2]

    if cropped.size == 0:
        return "ERRO NO RECORTE"

    # Converte para escala de cinza, se necessário
    if len(cropped.shape) == 3:
        cropped = cv.cvtColor(cropped, cv.COLOR_BGR2GRAY)

    # Adiciona margens brancas ao redor da palavra
    cropped = cv.copyMakeBorder(cropped, 
        30, 30, # Superior e inferior
        30, 30, # Esquerda e direita 
        cv.BORDER_CONSTANT,
        value=255   
    )

    rgb = cv.cvtColor(cropped, cv.COLOR_GRAY2RGB)
    pil_image = Image.fromarray(rgb)

    pixel_values = processor(images = pil_image, return_tensors = "pt").pixel_values

    generate_ids = model.generate(pixel_values, max_new_tokens = 32)

    text = processor.batch_decode(generate_ids, skip_special_tokens = True)[0]

    return text.strip()

