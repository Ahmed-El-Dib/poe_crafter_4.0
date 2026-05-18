from pricers.map_pricer import price_map, MIN_PRICE
def get_discounted_price(current_price, amt, discount_type="%", min_price=MIN_PRICE):
    if discount_type == "%":
        new_price = int(current_price * (1 - amt / 100))
    else:
        new_price = current_price - amt
    
    return int(max(new_price, min_price))  # Ensure price doesn't go below min_price


def reprice(map_dat, discount, discount_type="%", min_price=MIN_PRICE):
    full_price = price_map(map_dat)
    if full_price is None:
        return None
    return get_discounted_price(full_price, discount, discount_type, min_price)