import cv2 as cv


SCALE = 0.4


def showCoordinates(event, x, y, flags, param):

    if event == cv.EVENT_LBUTTONDOWN:

        real_x = int(x / SCALE)
        real_y = int(y / SCALE)

        print(
            f"x={real_x}, y={real_y}"
        )


image = cv.imread(
    "output/page1_processed.png"
)

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