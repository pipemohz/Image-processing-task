import logging
import datetime as dt
import os
from os.path import join
from dotenv import load_dotenv
from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2

DIGITS_LOOKUP = {
    (1, 1, 1, 0, 1, 1, 1): '0',
    (0, 0, 1, 0, 0, 1, 0): '1',
    (1, 0, 1, 1, 1, 0, 1): '2',
    (1, 0, 1, 1, 0, 1, 1): '3',
    (0, 1, 1, 1, 0, 1, 0): '4',
    (1, 1, 0, 1, 0, 1, 1): '5',
    (1, 1, 0, 1, 1, 1, 1): '6',
    (1, 0, 1, 0, 0, 1, 0): '7',
    (1, 1, 1, 1, 1, 1, 1): '8',
    (1, 1, 1, 1, 0, 1, 1): '9'
}


def process_image(path: str):
    """
    Process image to extract number.
    """
    # load the example image
    image = cv2.imread(path)

    # pre-process the image by resizing it, converting it to
    # graycale, blurring it, and computing an edge map
    image = imutils.resize(image, height=500)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    equ = cv2.equalizeHist(blurred)

    th = cv2.threshold(equ, 110, 255, cv2.THRESH_BINARY_INV)[1]

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

    warped = four_point_transform(gray, displayCnt.reshape(4, 2))
    output = four_point_transform(image, displayCnt.reshape(4, 2))

    # blur
    blur = cv2.GaussianBlur(output, (3, 3), 0)

    # convert to hsv and get saturation channel
    sat = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)[:, :, 1]

    # threshold saturation channel
    thresh = cv2.threshold(sat, 50, 255, cv2.THRESH_BINARY)[1]

    # apply morphology close and open to make mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel, iterations=1)

    # write black to input image where mask is black
    img_result = output.copy()
    img_result[mask == 0] = 0

    # find contours in the thresholded image, then initialize the
    # digit contours lists
    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[0]

    cnts = contours.sort_contours(cnts, method='left-to-right')[0]

    digitCnts = []

    # loop over the digit area candidates
    # filter contours by those related to digits
    for c in cnts:
        # compute the bounding box of the contour
        (x, y, w, h) = cv2.boundingRect(c)

        # if the contour is sufficiently large, it must be a digit
        # print(f'w,h={w},{h}')
        # cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.rectangle(mask, (x, y), (x + w, y + h), (255, 255, 255), 1)
        if w >= 30 and (h >= 30 and h <= 170):
            digitCnts.append(c)
        if w <= 14 and h <= 12:
            # Append the dot
            cv2.rectangle(mask, (x, y), (x + w, y + h), (255, 255, 255), 1)
            digitCnts.append(c)

    # sort the contours from left-to-right, then initialize the
    # actual digits themselves
    digitCnts = contours.sort_contours(digitCnts,
                                       method="left-to-right")[0]

    # print(f'digitCnts:{len(digitCnts)}')
    digits = []

    # loop over each of the digits
    for c in digitCnts:
        # extract the digit ROI
        (x, y, w, h) = cv2.boundingRect(c)
        roi = mask[y:y + h, x:x + w]

        if w <= 14 and h <= 12:
            # Append the dot
            digits.append('.')
            continue

        # compute the width and height of each of the 7 segments
        # we are going to examine
        # print(roi.shape)
        (roiH, roiW) = roi.shape
        # (dW, dH) = (int(roiW * 0.25), int(roiH * 0.15))
        (dW, dH) = (int(roiW * 0.15), int(roiH * 0.1))
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
            # print(segROI.shape)
            total = cv2.countNonZero(segROI)
            area = (xB - xA) * (yB - yA)

            # if the total number of non-zero pixels is greater than
            # 32% of the area, mark the segment as "on"
            if total / float(area) > 0.32:
                on[i] = 1

        # lookup the digit and draw it on the image
        # digit = DIGITS_LOOKUP[tuple(on)]
        # print(tuple(on))
        digit = DIGITS_LOOKUP.get(tuple(on))
        digits.append(digit)
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.putText(output, str(digit), (x - 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    # display the digits

    # cv2.imshow("Input", image)
    # cv2.imshow('Mask', mask)
    # cv2.imshow("Output", output)
    # cv2.waitKey(0)
    if digits.count('.') >= 2:
        digits.remove('.')

    num = ''
    for digit in digits:
        num += digit

    return num


def extract_numbers():
    """
    Process each image in OUTPUT_DIR and return a list with each number extracted.
    """

    load_dotenv()
    files = os.listdir(os.environ.get('OUTPUT_DIR'))
    images = [join(os.environ.get('OUTPUT_DIR'), file)
              for file in files if file.endswith('.jpg') or file.endswith('png')]

    numbers = []
    for image in images:
        try:
            number = process_image(image)
        except ValueError:
            logging.error(
                f'[{dt.datetime.now()}] Image in {image} was not processed.')
        else:
            numbers.append(number)
            logging.info(
                f'[{dt.datetime.now()}] Image in {image} was processed successfully.')

    return numbers
