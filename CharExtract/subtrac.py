import cv2

orig = cv2.imread("/Users/RithwikSudharsan 1/PycharmProjects/pythontest/Reine/1388_pre.png")
ret, orig = cv2.threshold(orig,127,255,cv2.THRESH_BINARY)
lines = cv2.imread("/Users/RithwikSudharsan 1/PycharmProjects/pythontest/Reine/img_final_bin.jpg")

final=cv2.subtract(lines, orig)

cv2.imwrite("final.png",final)