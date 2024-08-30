YEAR = 2024
VERSION = "1.0"
STEAMPULSE_GITHUB_URL = "https://github.com/AmirMahdaviAM/SteamPulse/"
STEAMPULSE_FEEDBACK_URL = "https://github.com/AmirMahdaviAM/SteamPulse/issues"
STEAMPULSE_ORIGINAL_URL = "https://github.com/amirhoseindavat/SteamPulse"
GITHUB = "https://github.com/AmirMahdaviAM/"
TELEGRAM = "https://t.me/amirmdvi"
INSTAGRAM = "https://instagram.com/amirmdvl"


MAIN_LOG = "steampulse.log"
SALE_IMG = "sale.jpg"
GAMES_DATABASE = "games_db.json"


REGION = [
    "United States",
    "United Kingdom",
    "Argentina",
    "Europe",
    "Turkey",
    "China",
    "India",
    "Russia",
    "Brazil",
    "Ukraine",
    "Kazakhstan",
    "Philippines",
    "South Asia",
    "CIS",
]

CURRENCY_KEY_REGION = {
    "Dollar": 1,
    "Pound": 2,
    "Euro": 3,
    "Yuan": 23,
    "Rupee": 24,
    "Ruble": 5,
    "Real": 7,
    "Hryvnia": 18,
    "Tenge": 37,
    "Peso": 12,
}

# CURRENCY_KEY_PRICE = {
#     "Dollar": 1.93,
#     "Pound": 1.47,
#     "Euro": 1.73,
#     "Yuan": 13.81,
#     "Rupee": 162.25,
#     "Ruble": 176.92,
#     "Real": 10.74,
#     "Hryvnia": 80.23,
#     "Tenge": 935.88,
#     "Peso": 109.08,
#     "Tooman": 101000,
# }

CURRENCY_KEY_PRICE = {
    "Tooman": 0,
    "Dollar": 0,
    "Pound": 0,
    "Euro": 0,
    "Yuan": 0,
    "Rupee": 0,
    "Ruble": 0,
    "Real": 0,
    "Hryvnia": 0,
    "Tenge": 0,
    "Peso": 0,
}


def currency(region: str):

    CURRENCY_SYMBOL_POS = "prefix"
    CURRENCY_FLOAT = True
    CURRENCY_NUMBER = 1

    match region:
        case "United States":
            CURRENCY_NAME = "Dollar"
            CURRENCY_ISO = "US"
            CURRENCY_SYMBOL = "$"

        case "United Kingdom":
            CURRENCY_NAME = "Pound"
            CURRENCY_ISO = "GB"
            CURRENCY_SYMBOL = "£"
            CURRENCY_NUMBER = 2

        case "Argentina":
            CURRENCY_NAME = "Dollar"
            CURRENCY_ISO = "AR"
            CURRENCY_SYMBOL = "$"

        case "Europe":
            CURRENCY_NAME = "Euro"
            CURRENCY_ISO = "NL"
            CURRENCY_SYMBOL = "€"
            CURRENCY_SYMBOL_POS = "suffix"
            CURRENCY_NUMBER = 3

        case "Turkey":
            CURRENCY_NAME = "Dollar"
            CURRENCY_ISO = "TR"
            CURRENCY_SYMBOL = "$"

        case "China":
            CURRENCY_NAME = "Yuan"
            CURRENCY_ISO = "CN"
            CURRENCY_SYMBOL = "¥"
            CURRENCY_NUMBER = 23

        case "India":
            CURRENCY_NAME = "Rupee"
            CURRENCY_ISO = "IN"
            CURRENCY_SYMBOL = "₹"
            CURRENCY_FLOAT = False
            CURRENCY_NUMBER = 24

        case "Russia":
            CURRENCY_NAME = "Ruble"
            CURRENCY_ISO = "RU"
            CURRENCY_SYMBOL = "₽"
            CURRENCY_SYMBOL_POS = "suffix"
            CURRENCY_FLOAT = False
            CURRENCY_NUMBER = 5

        case "Brazil":
            CURRENCY_NAME = "Real"
            CURRENCY_ISO = "BR"
            CURRENCY_SYMBOL = "R$"
            CURRENCY_NUMBER = 7

        case "Ukraine":
            CURRENCY_NAME = "Hryvnia"
            CURRENCY_ISO = "UA"
            CURRENCY_SYMBOL = "₴"
            CURRENCY_SYMBOL_POS = "suffix"
            CURRENCY_FLOAT = False
            CURRENCY_NUMBER = 18

        case "Kazakhstan":
            CURRENCY_NAME = "Tenge"
            CURRENCY_ISO = "KZ"
            CURRENCY_SYMBOL = "₸"
            CURRENCY_SYMBOL_POS = "suffix"
            CURRENCY_FLOAT = False
            CURRENCY_NUMBER = 37

        case "Philippines":
            CURRENCY_NAME = "Peso"
            CURRENCY_ISO = "PH"
            CURRENCY_SYMBOL = "₱"
            CURRENCY_NUMBER = 12

        case "South Asia":
            CURRENCY_NAME = "Dollar"
            CURRENCY_ISO = "PK"
            CURRENCY_SYMBOL = "$"

        case "CIS":
            CURRENCY_NAME = "Dollar"
            CURRENCY_ISO = "AZ"
            CURRENCY_SYMBOL = "$"

    return {
        "name": CURRENCY_NAME,
        "iso": CURRENCY_ISO,
        "symbol": CURRENCY_SYMBOL,
        "symbol_pos": CURRENCY_SYMBOL_POS,
        "float": CURRENCY_FLOAT,
        "number": CURRENCY_NUMBER,
    }
