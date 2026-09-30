import cv2 as cv


SCALE = 0.5
Y_OFFSET = 0
IMAGE_PATH = "output/aligned_page1.png"
WINDOW_NAME = "Formulario"


def showCoordinates(event, x, y, flags, param):
    if event != cv.EVENT_LBUTTONDOWN:
        return

    real_x = int(x / SCALE)
    real_y = int(y / SCALE) + Y_OFFSET
    print(f"x={real_x}, y={real_y}")


def main():
    image = cv.imread(IMAGE_PATH)

    if image is None:
        raise FileNotFoundError(f"Não foi possível abrir a imagem: {IMAGE_PATH}")

    image = image[Y_OFFSET:, :]
    display = cv.resize(image, None, fx=SCALE, fy=SCALE)

    cv.imshow(WINDOW_NAME, display)
    cv.setMouseCallback(WINDOW_NAME, showCoordinates)
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
