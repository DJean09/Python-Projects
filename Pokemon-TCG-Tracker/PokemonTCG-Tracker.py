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
import cv2 as cv

# RestClient.configure( REDACTED API )

card = Card.find('xy1-1')

print(f"{card.supertype}: {card.name}")
print(f"{card.images.large}")
print(f"{card.tcgplayer.prices.holofoil}")