"""Constants for avanza_stock."""

DOMAIN = "avanza_stock"
DEFAULT_NAME = "Avanza Stock GUI"

# Currency mapping - pairs are stored as QUOTE/BASE (e.g., EUR/SEK means 1 EUR = X SEK)
CURRENCY_MAP = {
    "SEK": None,  # Default, no conversion needed
    "USD": {"id": 19000, "pair": "USD/SEK", "invert": False},  # USD/SEK
    "EUR": {"id": 18998, "pair": "EUR/SEK", "invert": False},  # EUR/SEK
    "NOK": {"id": 53822, "pair": "NOK/SEK", "invert": False},  # NOK/SEK
    "DKK": {"id": 53824, "pair": "DKK/SEK", "invert": False},  # DKK/SEK
    # For SEK as base currency, we invert the existing pairs
    "SEK/USD": {"id": 19000, "pair": "USD/SEK", "invert": True},
    "SEK/EUR": {"id": 18998, "pair": "EUR/SEK", "invert": True},
    "SEK/NOK": {"id": 53822, "pair": "NOK/SEK", "invert": True},
    "SEK/DKK": {"id": 53824, "pair": "DKK/SEK", "invert": True},
}

REVERSE_CURRENCY_MAP = {info["id"]: curr for curr, info in CURRENCY_MAP.items() if info and "id" in info}
REVERSE_CURRENCY_MAP[None] = "SEK"  # Default currency

def get_currency_config(base_currency: str, quote_currency: str = "SEK") -> tuple[int | None, bool]:
    """Get currency conversion configuration.
    
    Args:
        base_currency: The currency to convert from
        quote_currency: The currency to convert to (default: SEK)
        
    Returns:
        Tuple of (conversion_currency_id, invert_conversion_currency)
    """
    if base_currency == quote_currency:
        return None, False
        
    # Try direct pair
    pair = f"{base_currency}/{quote_currency}"
    if pair in CURRENCY_MAP:
        info = CURRENCY_MAP[pair]
        return info["id"], info["invert"]
        
    # Try inverse pair
    pair = f"{quote_currency}/{base_currency}"
    if pair in CURRENCY_MAP:
        info = CURRENCY_MAP[pair]
        return info["id"], not info["invert"]  # Invert the inversion flag
        
    # Try simple currency (assuming SEK as quote)
    if base_currency in CURRENCY_MAP and isinstance(CURRENCY_MAP[base_currency], dict):
        info = CURRENCY_MAP[base_currency]
        return info["id"], info["invert"]
        
    return None, False  # Default to no conversion

# Configuration constants
CONF_STOCK = "stock"
CONF_SEARCH = "search"
CONF_INSTRUMENT_TYPE = "instrument_type"

# Search constants
INSTRUMENT_TYPES = {
    "stock": "Aktier",
    "fund": "Fonder",
    "index": "Index",
    "bond": "Obligationer",
    "certificate": "Certifikat",
    "exchange_rate": "Valutor",
    "all": "Alla"
}
CONF_SHARES = "shares"
CONF_PURCHASE_DATE = "purchase_date"
CONF_PURCHASE_PRICE = "purchase_price"
CONF_CONVERSION_CURRENCY = "conversion_currency"
CONF_INVERT_CONVERSION_CURRENCY = "invert_conversion_currency"
CONF_SHOW_TRENDING_ICON = "show_trending_icon"

# Attribute keys for extra state attributes
ATTR_TRENDING = "trending"

# Default configuration values
DEFAULT_SHOW_TRENDING_ICON = False

MONITORED_CONDITIONS = [
    "country",
    "currency",
    "dividends",
    "hasInvestmentFees",
    "highestPrice",
    "id",
    "isin",
    "lastPrice",
    "lastPriceUpdated",
    "loanFactor",
    "lowestPrice",
    "marketList",
    "marketMakerExpected",
    "marketTrades",
    "morningStarFactSheetUrl",
    "name",
    "numberOfOwners",
    "orderDepthReceivedTime",
    "pushPermitted",
    "quoteUpdated",
    "shortSellable",
    "superLoan",
    "tradable",
]

MONITORED_CONDITIONS_KEYRATIOS = [
    "directYield",
    "priceEarningsRatio",
    "volatility",
]
MONITORED_CONDITIONS += MONITORED_CONDITIONS_KEYRATIOS

MONITORED_CONDITIONS_LISTING = [
    "tickerSymbol",
    "marketPlace",
    "flagCode",
]
MONITORED_CONDITIONS += MONITORED_CONDITIONS_LISTING

MONITORED_CONDITIONS_COMPANY = [
    "description",
    "marketCapital",
    "sector",
    "totalNumberOfShares",
]
MONITORED_CONDITIONS += MONITORED_CONDITIONS_COMPANY

MONITORED_CONDITIONS_DIVIDENDS = [
    "amount",
    "exDate",
    "exDateStatus",
    "paymentDate",
]

MONITORED_CONDITIONS_DEFAULT = [
    "change",
    "changePercent",
    "name",
]

MONITORED_CONDITIONS_QUOTE = [
    "change",
    "changePercent",
    "totalValueTraded",
    "totalVolumeTraded",
]
MONITORED_CONDITIONS += MONITORED_CONDITIONS_QUOTE

MONITORED_CONDITIONS_PRICE = [
    "priceAtStartOfYear",
    "priceFiveYearsAgo",
    "priceOneMonthAgo",
    "priceOneWeekAgo",
    "priceOneYearAgo",
    "priceThreeMonthsAgo",
    "priceThreeYearsAgo",
]
MONITORED_CONDITIONS += MONITORED_CONDITIONS_PRICE

PRICE_MAPPING = {
    "priceAtStartOfYear": "startOfYear",
    "priceFiveYearsAgo": "fiveYears",
    "priceOneMonthAgo": "oneMonth",
    "priceOneWeekAgo": "oneWeek",
    "priceOneYearAgo": "oneYear",
    "priceThreeMonthsAgo": "rhreeMonths",
    "priceThreeYearsAgo": "rhreeYears",
}

CHANGE_PRICE_MAPPING = [
    ("changeOneWeek", "oneWeek"),
    ("changeOneMonth", "oneMonth"),
    ("changeThreeMonths", "threeMonths"),
    ("changeOneYear", "oneYear"),
    ("changeThreeYears", "threeYears"),
    ("changeFiveYears", "fiveYears"),
    ("changeTenYears", "tenYears"),
    ("changeCurrentYear", "startOfYear"),
]

TOTAL_CHANGE_PRICE_MAPPING = [
    ("totalChangeOneWeek", "oneWeek"),
    ("totalChangeOneMonth", "oneMonth"),
    (
        "totalChangeThreeMonths",
        "threeMonths",
    ),
    ("totalChangeOneYear", "oneYear"),
    (
        "totalChangeThreeYears",
        "threeYears",
    ),
    ("totalChangeFiveYears", "fiveYears"),
    ("totalChangeTenYears", "tenYears"),
    (
        "totalChangeCurrentYear",
        "startOfYear",
    ),
]

CHANGE_PERCENT_PRICE_MAPPING = [
    ("changePercentOneWeek", "oneWeek"),
    ("changePercentOneMonth", "oneMonth"),
    (
        "changePercentThreeMonths",
        "threeMonths",
    ),
    ("changePercentOneYear", "oneYear"),
    ("changePercentThreeYears", "threeYears"),
    ("changePercentFiveYears", "fiveYears"),
    ("changePercentTenYears", "tenYears"),
    ("changePercentCurrentYear", "startOfYear"),
]

CURRENCY_ATTRIBUTE = [
    "change",
    "highestPrice",
    "lastPrice",
    "lowestPrice",
    "priceAtStartOfYear",
    "priceFiveYearsAgo",
    "priceOneMonthAgo",
    "priceOneWeekAgo",
    "priceOneYearAgo",
    "priceSixMonthsAgo",
    "priceThreeMonthsAgo",
    "priceThreeYearsAgo",
    "totalValueTraded",
    "marketCapital",
    "dividend0_amountPerShare",
    "dividend1_amountPerShare",
    "dividend2_amountPerShare",
    "dividend3_amountPerShare",
    "dividend4_amountPerShare",
    "dividend5_amountPerShare",
    "dividend6_amountPerShare",
    "dividend7_amountPerShare",
    "dividend8_amountPerShare",
    "dividend9_amountPerShare",
    "changeOneWeek",
    "changeOneMonth",
    "changeThreeMonths",
    "changeSixMonths",
    "changeOneYear",
    "changeThreeYears",
    "changeFiveYears",
    "changeCurrentYear",
    "totalChangeOneWeek",
    "totalChangeOneMonth",
    "totalChangeThreeMonths",
    "totalChangeSixMonths",
    "totalChangeOneYear",
    "totalChangeThreeYears",
    "totalChangeFiveYears",
    "totalChangeCurrentYear",
    "totalValue",
    "totalChange",
    "profitLoss",
    "totalProfitLoss",
]
