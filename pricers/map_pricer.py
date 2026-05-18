# =========================
# TUNING
# =========================

MIN_PRICE = 19
INFLATION = 20

TOO_GOOD_CURRENCY_THRESHOLD = 158
TOO_GOOD_CURRENCY_PRICE = 1299
PERFECT_MOD_PRICE = 599

CURRENCY_TIERS = [
    {"min_currency": 151, "base": 229, "bonus_mult": 1.250, "inflation_mult": 1.25},
    {"min_currency": 128, "base": 199, "bonus_mult": 1, "inflation_mult": 1.25},
    {"min_currency": 120, "base": 159, "bonus_mult": 1, "inflation_mult": 1.25},
    {"min_currency": 111, "base": 49,  "bonus_mult": 0.75, "inflation_mult": 1.1},
    {"min_currency": 90,  "base": 19,  "bonus_mult": 0.18, "inflation_mult": 0.10},
]

PACK_BONUS_START = 30
PACK_BONUS_STEP = 5
PACK_BONUS_FLAT = 25
PACK_BONUS_SCALE = 40
PACK_BONUS_EXPONENT = 1.5
PACK_SIZE_INFLATION_MULT = 1

QUANTITY_BONUS_START = 80
QUANTITY_BONUS_STEP = 5
QUANTITY_BONUS_FLAT = 5
QUANTITY_BONUS_SCALE = 15
QUANTITY_BONUS_EXPONENT = 1.2

PACK_SIZE_PRICE_RULES = [
    {"ps": 90, "price": 449, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 84, "price": 289, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 80, "price": 249, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 75, "price": 129, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 70, "price": 109, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 65, "price": 99, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 62, "price": 84, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 60, "price": 69, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 55, "price": 59, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 50, "price": 54, "inflation": PACK_SIZE_INFLATION_MULT},
    {"ps": 40, "price": 24, "inflation": PACK_SIZE_INFLATION_MULT},
]

OTHER_PRICE_RULES = [
    {"extra": 100, "ps": 40, "mc": None, "q": None, "price": 99, "inflation": 0.25},
    {"extra": 100, "ps": None, "mc": 91, "q": 80, "price": 99, "inflation": 0.25},
    {"extra": 100, "ps": 31, "mc": None, "q": None, "price": 49, "inflation": 0.25},
    {"extra": 100, "ps": None, "mc": 71, "q": 80, "price": 49, "inflation": 0.25},
]

MAP_SUFFIX_TARGETS = [
    "of Collection",
    "of Splinters",
    "of Defiance",
    "of Imbibing",
    "of Persistence",
    "of Decaying"
]

MAP_PREFIX_TARGETS = [
    "Antagonist's",
    "Diluted",
    "Hungering",
    "Punishing",
    "Stalwart",
    "Valdo's",
]
# =========================
# HELPERS
# =========================

def min_match(value: int, threshold: int | None) -> bool:
    return threshold is None or value >= threshold


def old_quantity_bonus(quantity: int) -> int:
    return max(0, (quantity - 80) // 2)


def rule_price(
    price: int,
    quantity: int,
    inflation_mult: float,
    include_quantity_bonus: bool = True,
) -> int:
    total = price + int(INFLATION * inflation_mult)

    if include_quantity_bonus:
        total += old_quantity_bonus(quantity)

    return int(total)


def exponential_bonus(value, start, step, flat, scale, exponent):
    over = value - start

    if over <= 0:
        return 0

    levels = over / step
    return flat + scale * (levels ** exponent)


def pack_size_bonus(pack_size):
    return exponential_bonus(
        value=pack_size,
        start=PACK_BONUS_START,
        step=PACK_BONUS_STEP,
        flat=PACK_BONUS_FLAT,
        scale=PACK_BONUS_SCALE,
        exponent=PACK_BONUS_EXPONENT,
    )


def quantity_bonus(quantity):
    return exponential_bonus(
        value=quantity,
        start=QUANTITY_BONUS_START,
        step=QUANTITY_BONUS_STEP,
        flat=QUANTITY_BONUS_FLAT,
        scale=QUANTITY_BONUS_SCALE,
        exponent=QUANTITY_BONUS_EXPONENT,
    )


def get_currency_tier(more_currency):
    for tier in CURRENCY_TIERS:
        if more_currency >= tier["min_currency"]:
            return tier

    return None


# =========================
# PERFECT MOD HELPERS
# =========================

def is_perfect_suffix(map_data):
    mods = map_data.get("mods", [])
    return sum(
        1
        for mod in mods
        if mod["type"] == "suffix" and mod["name"] in MAP_SUFFIX_TARGETS
    ) >= 3


def is_perfect_prefix(map_data):
    mods = map_data.get("mods", [])
    return sum(
        1
        for mod in mods
        if mod["type"] == "prefix" and mod["name"] in MAP_PREFIX_TARGETS
    ) >= 3


# =========================
# PRICERS
# =========================

def price_currency_map(more_currency, pack_size, quantity):
    if more_currency > TOO_GOOD_CURRENCY_THRESHOLD:
        return TOO_GOOD_CURRENCY_PRICE

    tier = get_currency_tier(more_currency)

    if tier is None:
        return MIN_PRICE

    raw_bonus = pack_size_bonus(pack_size) + quantity_bonus(quantity)
    scaled_bonus = raw_bonus * tier["bonus_mult"]

    price = (
        tier["base"]
        + scaled_bonus
        + int(INFLATION * tier["inflation_mult"])
    )

    return max(MIN_PRICE, int(round(price)))


def price_packsize_map(pack_size, quantity):
    prices = []

    for rule in PACK_SIZE_PRICE_RULES:
        if min_match(pack_size, rule["ps"]):
            prices.append(
                rule_price(
                    price=rule["price"],
                    quantity=quantity,
                    inflation_mult=rule["inflation"],
                    include_quantity_bonus=True,
                )
            )

    return max(prices) if prices else None


def price_other_map(more_maps, more_scarabs, more_currency, pack_size, quantity):
    prices = []
    best_extra = max(more_maps, more_scarabs)

    for rule in OTHER_PRICE_RULES:
        if (
            min_match(best_extra, rule["extra"])
            and min_match(pack_size, rule["ps"])
            and min_match(more_currency, rule["mc"])
            and min_match(quantity, rule["q"])
        ):
            prices.append(
                rule_price(
                    price=rule["price"],
                    quantity=quantity,
                    inflation_mult=rule["inflation"],
                    include_quantity_bonus=False,
                )
            )

    return max(prices) if prices else None


def price_map(map_data):
    stats = map_data.get("stats", {})

    quantity = stats.get("quantity", 0)
    pack_size = stats.get("pack_size", 0)
    more_maps = stats.get("more_maps", 0)
    more_currency = stats.get("more_currency", 0)
    more_scarabs = stats.get("more_scarabs", 0)

    prices = [MIN_PRICE]

    if is_perfect_prefix(map_data) or is_perfect_suffix(map_data):
        prices.append(PERFECT_MOD_PRICE)

    prices.append(
        price_currency_map(
            more_currency=more_currency,
            pack_size=pack_size,
            quantity=quantity,
        )
    )

    pack_size_price = price_packsize_map(pack_size, quantity)
    if pack_size_price is not None:
        prices.append(pack_size_price)

    other_price = price_other_map(
        more_maps=more_maps,
        more_scarabs=more_scarabs,
        more_currency=more_currency,
        pack_size=pack_size,
        quantity=quantity,
    )
    if other_price is not None:
        prices.append(other_price)

    return max(prices)

