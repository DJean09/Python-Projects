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

recent = ""

def calc_image_hashes(card_pool, hash_size=16):
    """
    Compare card on video with each card in the database and gives them a value
    Calculate perceptual hash (pHash) value for each cards in the database, 
    then store them if needed
    [card_pool] folder containing all card images
    [hash_size] param for pHash algorithm
    [return] dictionary of card hashes
    """
    card_hashes = {}

    for filename in os.listdir(card_pool):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            card_name = filename.split('.')[0]  # Extract the card name (e.g. "xy1-1")
            img_path = os.path.join(card_pool, filename)

            # load and preprocess image
            img = cv2.imread(img_path)

            # preprocessing steps like resizing and grayscaling
            img = cv2.resize(img, (600, 400))
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh_val = 150 # adjust based on image quality
            _, img_thresh = cv2.threshold(img_gray, thresh_val, 255, cv2.THRESH_BINARY)

            # get image hash
            hash_val = ih.phash(Image.fromarray(img_thresh), hash_size=hash_size)

            card_hashes[card_name] = hash_val.hash.flatten()
    
    return card_hashes


# www.pyimagesearch.com/2014/08/25/4-point-opencv-getperspective-transform-example/
def order_points(pts):
    """
    initialize a list of coordinates that will be ordered
    such that the first entry in the list is the top-left,
    the second entry is the top-right,
    third is the bottom-right,
    and the fourth is the bottom-left.
    [pts] list of points
    [return] ordered list of points
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
    [img] source image
    [return] image with reduced glare
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

def find_card(img, thresh_c=5, kernel_size=(3,3), size_thresh=10000):
    """
    find contours of all cards in the image
    [img] source image
    [thresh_c] value of the constant C for adaptive thresholding
    [kernel_size] dimension of the kernel used for dilation and erosion
    [size_thresh] threshold in pixels of the contour to be a candidate
    [return] list of contours of the cards in the image
    """
    # pre-processing - grayscale, blurring, thresholding
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.medianBlur(img_gray, 5)
    img_thresh = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 5, thresh_c)

    # dilute the image, then erode them to remove minor noises
    kernel = np.ones(kernel_size, np.uint8)
    img_dilate = cv2.dilate(img_thresh, kernel, iterations=1)
    img_erode = cv2.erode(img_dilate, kernel, iterations=1)

    # find the contour
    _, cnts, hier = cv2.findContours(img_erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(cnts) == 0:
        return []
    
    # the hierarchy from cv2.findContours() is similar to a tree: 
    # each node has an access to the parent, the first child their previous and next node
    # using recursive search, find the uppermost contour in the hierarchy that satisfies the condition
    # the candidate contour must be rectangle (has 4 points) and should be larger than a threshold
    cnts_rect = []
    stack = [(0, hier[0][0])]
    while len(stack) > 0:
        i_cnt, h = stack.pop()
        i_next, i_prev, i_child, i_parent = h

        if i_next != -1:
            stack.append((i_next, hier[0][i_next]))
        
        cnt = cnt[i_cnt]
        size = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        if size >= size_thresh and len(approx) == 4:
            cnts_rect.append(approx)
        else:
            if i_child != -1:
                stack.append((i_child, hier[0][i_child]))
        
    return cnts_rect

def display_card_info(card, api_base_url):
    """
    Display card information in a window.
    [card] card object containing information
    """
    info_img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(info_img, f"Name: {card.name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(info_img, f"Set: {card.set.name}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(info_img, f"Rarity: {card.rarity}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if card.tcgplayer and card.tcgplayer.prices and card.tcgplayer.prices.holofoil:
        price = card.tcgplayer.prices.holofoil.market
        cv2.putText(info_img, f"Price: ${price:.2f}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    else:
        cv2.putText(info_img, "Price: None", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(info_img, f"API URL: {api_base_url}/{card.id}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imshow("Card Information", info_img)

def detect_frame(frame, card_hashes, hash_size, api_base_url, api_key=None, display=False, debug=False, thresh_c=5, kernel_size=(3,3), size_thresh=10000):
    """
    identify all the cards in the input frame
    [frame] input frame
    [card_hashes] dictionary of card hashes
    [hash_size] pHash hash size
    [api_base_url] base URL for the
    [api_key] API key for the Pokemon TCG API
    [display] whether to display the result
    [debug] whether to display debug information
    [thresh_c] value of the constant C for adaptive thresholding
    [kernel_size] dimension of the kernel used for dilation and erosion
    [size_thresh] threshold in pixels of the contour to be a candidate
    [return] list of detected cards
    """
    # Preprocessing the frame
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_blur = cv2.medianBlur(frame_gray, 5)
    frame_thresh = cv2.adaptiveThreshold(frame_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 5, thresh_c)

    # Dilate and erode the image to remove minor noises
    kernel = np.ones(kernel_size, np.uint8)
    frame_dilate = cv2.dilate(frame_thresh, kernel, iterations=1)
    frame_erode = cv2.erode(frame_dilate, kernel, iterations=1)

    # Find contours ----
    cnts, hier = cv2.findContours(frame_erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(cnts) == 0:
        return []
    
    # Filter contours and process each card
    cards = []
    stack = [(0, hier[0][0])]
    while len(stack) > 0:
        i_cnt, h = stack.pop()
        i_next, i_prev, i_child, i_parent = h

        if i_next != -1:
            stack.append((i_next, hier[0][i_next]))
        
        cnt = cnts[i_cnt]
        size = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        if size >= size_thresh and len(approx) == 4:
            # Get the card image
            pts = approx.reshape(4, 2)
            warped = four_point_transform(frame, pts)
            warped = remove_glare(warped)

            # Compare the card image with the database
            hash_val = ih.phash(Image.fromarray(warped), hash_size=hash_size)
            card_name = None
            min_dist = float('inf')
            for name, hash_db in card_hashes.items():
                # MAY HAVE TO BE FIXED ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                # dist = np.linalg.norm(hash_val.hash.flatten() - hash_db)
                dist = np.linalg.norm(np.bitwise_xor(hash_val.hash.flatten(), hash_db))
                if dist < min_dist:
                    min_dist = dist
                    card_name = name
            
            # Get the card information
            card = Card.find(card_name)
            cards.append(card)
            
            # Display the card information
            # if debug:
            #     print(f"Card detected: {card_name}")
            #     print(f"Name: {card.name}")
            #     print(f"Set: {card.set.name}")
            #     print(f"Rarity: {card.rarity}")
            #     print(f"Price: {card.tcgplayer.prices.holofoil}")
            #     print(f"Image: {card.images.large}")
            #     print(f"API URL: {api_base_url}/{card.id}")
            
            # Draw border on detected card
            x, y, w, h = cv2.boundingRect(approx)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Display the current card
            if display:
                #cv2.imshow("Card", warped)
                global recent
                if recent != card.id:                       # Only updates if new card
                    display_card_info(card, api_base_url)
                    recent = card.id
    return cards


def main():
    # RestClient.configure( REDACTED API )

    video = cv2.VideoCapture(1)

    while True:
        # Capture the video feed
        ret, frame = video.read()
        card_hashes = calc_image_hashes("Pokemon-TCG-Tracker/Card-Images")
        cards = detect_frame(frame, card_hashes, 16, "https://api.pokemontcgio/v2/cards", display=True, debug=True)
    
        # Open up a window called "Card Detection" and displays video
        cv2.imshow("Card detection", frame)
    
        # exit button will be set to Q
        if cv2.waitKey(1) == ord("q"):
            break

    # Release the video feed and close all windows
    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()