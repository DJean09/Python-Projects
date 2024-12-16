"""
Dominick Jean

Roman Numeral Converter
"""
import math

def FindOnes(num):
    result = ""

    firstdigit = num % 10

    ones = firstdigit % 5

    if firstdigit == 9:
        result += "IX"
    elif firstdigit >= 5:
        result += "V"
        if firstdigit >= 6:
            result += "I" * ones
    elif firstdigit == 4:
        result += "IV"
    elif firstdigit >= 1:
        result += "I" * ones

    return result

def FindTens(num):
    result = ""

    seconddigit = num % 100

    tens = seconddigit / 10
    if tens > 5:
        tens -= 5
    tens = math.floor(tens)

    if seconddigit >= 90:
        result += "XC"
    elif seconddigit >= 50:
        result += "L"
        if seconddigit >= 60:
            result += "X" * tens
    elif seconddigit >= 40:
        result += "XL"
    elif seconddigit >= 10:
        result += "X" * tens

    return result

def FindHundreds(num):
    result = ""

    thirddigit = num % 1000

    hundreds = thirddigit / 100
    if hundreds > 5:
        hundreds -= 5
    hundreds = math.floor(hundreds)

    if thirddigit >= 900:
        result += "CM"
    elif thirddigit >= 500:
        result += "D"
        if thirddigit >= 600:
            result += "C" * hundreds
    elif thirddigit >= 400:
        result += "CD"
    elif thirddigit >= 100:
        result += "C" * hundreds

    return result

def FindThousands(num):
    result = ""

    fourthdigit = num % 10000

    thousands = fourthdigit / 1000
    if thousands > 5:
        thousands -= 5
    thousands = math.floor(thousands)

    result += "M" * thousands

    return result



print("You can convert a number to Roman Numerals (Up to 3999)")
while True:
    roman = ""

    try:
        number = int(input("Enter a number to convert: "))

        if number > 10:
            roman = FindOnes(number)
        elif number < 100:
            roman = FindTens(number)
            roman += FindOnes(number)
        elif number < 1000:
            roman = FindHundreds(number)
            roman += FindTens(number)
            roman += FindOnes(number)
        elif number < 4000:
            roman = FindThousands(number)
            roman += FindHundreds(number)
            roman += FindTens(number)
            roman += FindOnes(number)
    except ValueError:
        print("Invalid response")

    print(roman)

    response = int(input("Do you want to do another number? 1 (yes)/2 (no): "))
    if response == 2:
        quit()