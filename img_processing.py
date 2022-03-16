import os
import numpy as np
from os.path import join
from dotenv import load_dotenv
from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2

load_dotenv()

files = os.listdir(os.environ.get('OUTPUT_DIR'))
images = [join(os.environ.get('OUTPUT_DIR'), file)
          for file in files if file.endswith('.jpg') or file.endswith('png')]

DIGITS_LOOKUP = {
    (1, 1, 1, 0, 1, 1, 1): 0,
    (0, 0, 1, 0, 0, 1, 0): 1,
    (1, 0, 1, 1, 1, 1, 0): 2,
    (1, 0, 1, 1, 0, 1, 1): 3,
    (0, 1, 1, 1, 0, 1, 0): 4,
    (1, 1, 0, 1, 0, 1, 1): 5,
    (1, 1, 0, 1, 1, 1, 1): 6,
    (1, 0, 1, 0, 0, 1, 0): 7,
    (1, 1, 1, 1, 1, 1, 1): 8,
    (1, 1, 1, 1, 0, 1, 1): 9
}

# load the example image
image = cv2.imread(images[0])

# pre-process the image by resizing it, converting it to
# graycale, blurring it, and computing an edge map
image = imutils.resize(image, height=500)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

blurred = cv2.GaussianBlur(gray, (5, 5), 0)
equ = cv2.equalizeHist(blurred)
clahe = cv2.createCLAHE()
# clahe = cv2.createCLAHE(clipLimit=40.0)
cl1 = clahe.apply(blurred)

th = cv2.threshold(equ, 110, 255, cv2.THRESH_BINARY_INV)[1]
# th = cv2.adaptiveThreshold(cl1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,2)
# th1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,2)

# edged = cv2.Canny(th, 50, 200, 255)
cnts, hierarchy = cv2.findContours(
    th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

# loop over the contours
for c in cnts:
    # approximate the contour
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)

    # if the contour has four vertices, then we have found
    # the thermostat display
    if len(approx) == 4:
        displayCnt = approx
        break

# extract the thermostat display, apply a perspective transform
# to it
warped = four_point_transform(cl1, displayCnt.reshape(4, 2))
output = four_point_transform(image, displayCnt.reshape(4, 2))

# threshold the warped image, then apply a series of morphological
# operations to cleanup the thresholded image
thresh = cv2.threshold(warped, 110, 255, cv2.THRESH_BINARY_INV)[1]
# thresh = cv2.adaptiveThreshold(warped, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,2)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)


# find contours in the thresholded image, then initialize the
# digit contours lists
cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)[0]


digitCnts = []

# loop over the digit area candidates
for c in cnts:
    # compute the bounding box of the contour
    (x, y, w, h) = cv2.boundingRect(c)

    # if the contour is sufficiently large, it must be a digit
    # print(f'w,h={w},{h}')
    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 1)
    if w >= 30 and (h >= 30 and h <= 170):
        digitCnts.append(c)

# cv2.imshow('test', output)
# cv2.imshow('threst', thresh)
# cv2.waitKey(0)

# sort the contours from left-to-right, then initialize the
# actual digits themselves
digitCnts = contours.sort_contours(digitCnts,
	method="left-to-right")[0]
print(thresh.shape)
print(f'digitCnts:{len(digitCnts)}')
digits = []

# loop over each of the digits
# print('digitCnts', digitCnts)
for c in digitCnts:
    # extract the digit ROI
    (x, y, w, h) = cv2.boundingRect(c)
    roi = thresh[y:y + h, x:x + w]

    # compute the width and height of each of the 7 segments
    # we are going to examine
    # print(roi.shape)
    (roiH, roiW) = roi.shape
    # (dW, dH) = (int(roiW * 0.25), int(roiH * 0.15))
    (dW, dH) = (int(roiW * 0.25), int(roiH * 0.10))
    dHC = int(roiH * 0.05)

    # define the set of 7 segments
    segments = [
        ((0, 0), (w, dH)),  # top
        ((0, 0), (dW, h // 2)),  # top-left
        ((w - dW, 0), (w, h // 2)),  # top-right
        ((0, (h // 2) - dHC), (w, (h // 2) + dHC)),  # center
        ((0, h // 2), (dW, h)),  # bottom-left
        ((w - dW, h // 2), (w, h)),  # bottom-right
        ((0, h - dH), (w, h))  # bottom
    ]
    # cv2.rectangle(output, roi[0], (w, dH), (255, 0, 0), 1)
    # cv2.rectangle(output, (0, h - dH), (w, h), (255, 0, 0), 1)
    on = [0] * len(segments)

    # sort the contours from left-to-right, then initialize the
    # actual digits themselves
    # loop over the segments
    for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
        # extract the segment ROI, count the total number of
        # thresholded pixels in the segment, and then compute
        # the area of the segment
        segROI = roi[yA:yB, xA:xB]
        print(segROI.shape)
        total = cv2.countNonZero(segROI)
        area = (xB - xA) * (yB - yA)

        # if the total number of non-zero pixels is greater than
        # 50% of the area, mark the segment as "on"
        if total / float(area) > 0.5:
            on[i] = 1
    
    # lookup the digit and draw it on the image
    # digit = DIGITS_LOOKUP[tuple(on)]
    print(tuple(on))
    digit = DIGITS_LOOKUP.get(tuple(on))
    digits.append(digit)
    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 1)
    cv2.putText(output, str(digit), (x - 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

# display the digits
print(digits)
# print(u"{}{}.{} \u00b0C".format(*digits))
cv2.imshow("Input", image)
cv2.imshow('Thresh', thresh)
cv2.imshow("Output", output)
cv2.waitKey(0)
