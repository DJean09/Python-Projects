"""
Dominick Jean

Pokemon TCG Scanner
"""

from pokemontcgsdk import Card
from pokemontcgsdk import Set
from pokemontcgsdk import Type
from pokemontcgsdk import Supertype
from pokemontcgsdk import Subtype
from pokemontcgsdk import Rarity
#from pokemontcgsdk import RestClient    - helps initialize API
import cv2
import numpy as np
# import cvlib as cv
# from cvlib.object_detection import draw_bbox

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