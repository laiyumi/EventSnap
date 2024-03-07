import cv2 as cv
import numpy as np

# stack all the images in one window
def stackImages(imgArray,scale,lables=[]):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]

    # print(f"width = '{width}' and height = '{height}'")
    # print(f"rows = '{rows}' and cols = '{cols}'")
    # print(f"rowsAvailable = '{rowsAvailable}'")

    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                imgArray[x][y] = cv.resize(imgArray[x][y], (0, 0), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y] = cv.cvtColor(imgArray[x][y], cv.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows

        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)

    else:
        for x in range(0, rows):
            imgArray[x] = cv.resize(imgArray[x], (0, 0), None, scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv.cvtColor(imgArray[x], cv.COLOR_GRAY2BGR)
        hor = np.hstack(imgArray)
        ver = hor

    if len(lables) != 0:
        eachImgWidth= int(ver.shape[1] / cols)
        eachImgHeight = int(ver.shape[0] / rows)

        # print(f"eachImgWidth = '{eachImgWidth}' and eachImgHeight = '{eachImgHeight}'")

        for d in range(0, rows):
            for c in range (0,cols):
                cv.rectangle(ver,(c*eachImgWidth,eachImgHeight*d),(c*eachImgWidth+len(lables[d][c])*13+27,30+eachImgHeight*d),(255,255,255),cv.FILLED)
                cv.putText(ver,lables[d][c],(eachImgWidth*c+10,eachImgHeight*d+20),cv.FONT_HERSHEY_COMPLEX,0.7,(255,0,255),2)

            # print(f"rectangle coordinates = '{(c*eachImgWidth, eachImgHeight*d)}' and '{(c*eachImgWidth+len(lables[d])*13+27, 30+eachImgHeight*d)}'")
    return ver