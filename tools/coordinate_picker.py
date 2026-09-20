import cv2 as cv

SCALE = 0.5
Y_OFFSET = 0


def showCoordinates(
    event,
    x,
    y,
    flags,
    param
):

    if event == cv.EVENT_LBUTTONDOWN:

        real_x = int(x / SCALE)
        real_y = int(y / SCALE) + Y_OFFSET

        print(
            f"x={real_x}, y={real_y}"
        )


image = cv.imread(
    "output/aligned_page1.png"
)

if image is None:
    raise FileNotFoundError(
        "Não foi possível abrir a imagem."
    )


image = image[
    Y_OFFSET:,
    :
]

display = cv.resize(
    image,
    None,
    fx=SCALE,
    fy=SCALE
)

cv.imshow(
    "Formulario",
    display
)

cv.setMouseCallback(
    "Formulario",
    showCoordinates
)

cv.waitKey(0)
cv.destroyAllWindows()