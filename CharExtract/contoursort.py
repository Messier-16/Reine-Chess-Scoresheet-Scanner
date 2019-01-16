import cv2

def get_contour_precedence(contour, cols):
    tolerance_factor = 10
    origin = cv2.boundingRect(contour)
    return ((origin[1] // tolerance_factor) * tolerance_factor) * cols + origin[0]

img = cv2.imread("/Users/RithwikSudharsan 1/PycharmProjects/pythontest/Reine/CharExtract/Image_bin.jpg", 0)

_, img = cv2.threshold(img, 70, 255, cv2.THRESH_BINARY)

im, contours, h = cv2.findContours(img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

contours.sort(key=lambda x:get_contour_precedence(x, img.shape[1]))

# For debugging purposes.
for i in range(len(contours)):
    img = cv2.putText(img, str(i), cv2.boundingRect(contours[i])[:2], cv2.FONT_HERSHEY_COMPLEX, 1, [125])
    cv2.imwrite("debug.png",img)
