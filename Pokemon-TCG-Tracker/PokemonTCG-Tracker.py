"""
Dominick Jean

Pokemon TCG Scanner
"""
import argparse                 # helps easily write user-friendly command-line interfaces
import ast                      # helps process trees of the python abstract syntax grammer
import collections              # provides alternatives to dict, list, set, and tuple
import cv2                      # assists with image processing and object detection
import imagehash as ih          # image comparison tool
import numpy as np              # tool for data analysis. working with arrays and matrices
from operator import itemgetter # allows you to retrieve specific items from an iterable easily
import os                       # provides functions for interacting with the OS. File manipulation an shell commands
import pandas as pd             # analyze data
from PIL import Image           # load images from files and create new images
from pokemontcgsdk import Card  # PokemonTCG database
from pokemontcgsdk import Set
from pokemontcgsdk import Type
from pokemontcgsdk import Supertype
from pokemontcgsdk import Subtype
from pokemontcgsdk import Rarity
import time                     # returns the CPU time of the current process

#from pokemontcgsdk import RestClient    - helps initialize API
# import cvlib as cv
# from cvlib.object_detection import draw_bbox

def calc_image_hashes(card_pool, save_to=None, hash_size=None):
    """
    Compare card on video with each card in the database and gives them a value
    Calculate perceptual hash (pHash) value for each cards in the database, 
    then store them if needed
    [card_pool] pandas dataframe containing all card information
    [save_to] path for the pickle file to be saved
    [hash_size] param for pHash algorithm
    """


# www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
def order_points(pts):
    """
    initialize a list of coordinates that will be ordered
    such that the first entry in the list is the top-left,
    the second entry is the top-right,
    third is the bottom-right,
    and the fourth is the bottom-left.
    """
    rect = np.zeros((4,2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect

# still using the getperspective as a refrence
def four_point_transform(image, pts):
    # Receive a consistend order of the points and unpack them individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordinates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left order
    dst = np.array([
        [0,0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1,]], dtype="float32")
    
    # compute the perspective transform matrix and then apply it
    mat = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, mat, (maxWidth, maxHeight))

    # if the image is horizontally long, rotate it by 90
    if maxWidth > maxHeight:
        center = (maxHeight / 2, maxHeight / 2)
        mat_rot = cv2.getRotationMatrix2D(center, 270, 1.0)
        warped = cv2.warpAffine(warped, mat_rot, (maxHeight, maxWidth))
    
    # return the warped image
    return warped

# http://www.amphident.de/en/blog/preprocessing-for-automatic-pattern-identification-in-wildlife-removing-glare.html
def remove_glare(img):
    """
    reduce the glaring in the image.
    Finds the area that has low saturation but high value,
    which is what a glare usually looks like
    """

    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, v = cv2.split(img_hsv)
    non_sat = (s < 32) * 255    # Find all pixels that are not saturated

    # Slightly decrease the area of the non-saturated pixels by a erosion operation
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    non_sat = cv2.erode(non_sat.astype(np.uint8), disk)

    # set all brightness values, where the pixels are still saturated to 0
    v[non_sat == 0] = 0
    # filter out very bright pixels
    glare = (v > 200) * 255

    # slightly increase the area of each pixel
    glare = cv2.dilate(glare.astype(np.uint8), disk)
    glare_reduced = np.ones((img.shape[0], img.shape[1], 3), dtype=np.uint8) * 200
    glare = cv2.cvtColor(glare, cv2.COLOR_GRAY2BGR)
    corrected = np.where(glare, glare_reduced, img)

    return corrected

# RestClient.configure( REDACTED API )

# card = Card.find('xy1-1')

# print(f"{card.supertype}: {card.name}")
# print(f"{card.images.large}")
# print(f"{card.tcgplayer.prices.holofoil}")

# Load test pokemon card
# '0' after the image location loads it in grayscale
test = cv2.imread("Pokemon-TCG-Tracker/Card-Images/sv4pt5-36-Dedenne.png", 0)
w, h = test.shape[::-1]

# Video feed, change the number for the camera
video = cv2.VideoCapture(1)

while True:
    ret, frame = video.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # test match
    res = cv2.matchTemplate(gray, test, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)

    # Highlight the detected card
    for pt in zip(*loc[::-1]):
        cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), (0, 255, 255), 2)
        print("Card detected!")

    # Open up a window called "Card Detection" and displays video
    cv2.imshow("Card detection", frame)

    # exit button will be set to Q
    if cv2.waitKey(1) == ord("q"):
        break
        
video.release()
cv2.destroyAllWindows()