from itertools import combinations

from macros.item_parser import parse_deli_orb
from focus_window import focus_window
import pyautogui
from images.img_paths import *
from images.image_utils import locate_center

from macros.rpa_macros import *
# Graceful global shutdown handling
from pynput import keyboard


from utils.initiate_session import requires_game_ready


TARGETS = ["Diviner's"]

HORTI_CRAFT = (962, 606)
HORTI_ITEM = (963, 482)
HORTI_SEARCH = (535, 814)
HORTI_SELECT = (574, 327)

COST_PER_TRY = 9.5

ORB_VALUES = {
    "Fine": 420,
    "Skittering": 450,
    "Diviner's": 850,
}

DEFAULT_ORB_VALUE = 350

ORB_STATS = {
    "initial_seen": {},
    "reroll_seen": {},
    "kept_seen": {},
}


def orb_value(orb_type):
    return ORB_VALUES.get(orb_type, DEFAULT_ORB_VALUE)


def normalize_type(orb):
    return orb["type"] if orb and "type" in orb else None


def record_orb(orb, bucket):
    orb_type = normalize_type(orb)

    if not orb_type:
        return

    if orb_type not in ORB_STATS[bucket]:
        ORB_STATS[bucket][orb_type] = 0

    ORB_STATS[bucket][orb_type] += 1


def good_to_keep(orb):
    orb_type = orb["type"].lower()
    return any(target.lower() in orb_type for target in TARGETS)


def setup_deli_craft():
    click(HORTI_SEARCH)
    time.sleep(0.2)
    pyautogui.typewrite("deli")
    click(HORTI_SELECT)



def flip_orb():
    orb = parse_deli_orb(HORTI_ITEM)

    tries = 0
    success = False
    final_value = 0
    final_type = None

    while orb and not good_to_keep(orb):
        if locate_center(OUT_OF_JUICE):
            print("Out of juice, stopping flips.")
            exit()

        click(HORTI_CRAFT)

        tries += 1

        orb = parse_deli_orb(HORTI_ITEM)
        record_orb(orb, "reroll_seen")

    if orb and good_to_keep(orb):
        success = True
        final_type = normalize_type(orb)
        final_value = orb_value(final_type)

        record_orb(orb, "kept_seen")

        ctrl_click(HORTI_ITEM)

    return {
        "tries": tries,
        "successes": 1 if success else 0,
        "cost": tries * COST_PER_TRY,
        "revenue": final_value,
        "profit": final_value - (tries * COST_PER_TRY),
        "final_type": final_type,
    }


def print_observed_weights():
    counts = ORB_STATS["reroll_seen"]
    total = sum(counts.values())

    print("\n===== OBSERVED REROLL WEIGHTS =====")

    if total == 0:
        print("No reroll data recorded.")
        print("===================================\n")
        return

    for orb_type, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        chance = count / total
        one_in_n = 1 / chance

        print(
            f"{orb_type}: {count} hits | "
            f"{chance * 100:.2f}% | "
            f"1 in {one_in_n:.2f} | "
            f"value {orb_value(orb_type)}c"
        )

    print("===================================\n")


def print_kept_summary():
    counts = ORB_STATS["kept_seen"]
    total = sum(counts.values())

    print("\n===== KEPT ORB SUMMARY =====")

    if total == 0:
        print("No kept orbs recorded.")
        print("===========================\n")
        return

    for orb_type, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{orb_type}: {count} kept | value {orb_value(orb_type)}c each")

    print("===========================\n")


def compute_best_keep_combo():
    counts = ORB_STATS["reroll_seen"]
    total_rolls = sum(counts.values())

    print("\n===== BEST KEEP TARGET ANALYSIS =====")

    if total_rolls == 0:
        print("No reroll data available.")
        print("=====================================\n")
        return

    orb_types = list(counts.keys())
    results = []

    for size in range(1, len(orb_types) + 1):
        for combo in combinations(orb_types, size):
            success_hits = sum(counts[t] for t in combo)

            if success_hits == 0:
                continue

            success_chance = success_hits / total_rolls
            one_in_n = 1 / success_chance

            avg_success_value = (
                sum(counts[t] * orb_value(t) for t in combo) / success_hits
            )

            avg_cost_per_success = COST_PER_TRY / success_chance
            expected_net_per_success = avg_success_value - avg_cost_per_success

            results.append(
                {
                    "combo": combo,
                    "one_in_n": one_in_n,
                    "success_chance": success_chance,
                    "avg_success_value": avg_success_value,
                    "avg_cost_per_success": avg_cost_per_success,
                    "expected_net_per_success": expected_net_per_success,
                }
            )

    results.sort(key=lambda x: x["expected_net_per_success"], reverse=True)

    best = results[0]

    print("Best keep targets:", ", ".join(best["combo"]))
    print(f"Observed success chance: 1 in {best['one_in_n']:.2f} tries")
    print(f"Average value per success: {best['avg_success_value']:.2f}c")
    print(f"Average cost per success: {best['avg_cost_per_success']:.2f}c")
    print(f"Expected net per success: {best['expected_net_per_success']:.2f}c")

    print("\nTop 10 combos:")
    for result in results[:10]:
        print(
            f"{', '.join(result['combo'])} | "
            f"1 in {result['one_in_n']:.2f} | "
            f"value {result['avg_success_value']:.2f}c | "
            f"cost {result['avg_cost_per_success']:.2f}c | "
            f"net {result['expected_net_per_success']:.2f}c"
        )

    print("=====================================\n")

@requires_game_ready()
def orb_flipper():
    INVENTORY_GRID_ROWS = 5
    INVENTORY_GRID_COLS = 12
    INVENTORY_GRID_START_X = 1292
    INVENTORY_GRID_START_Y = 612
    INVENTORY_GRID_CELL_SIZE = 53

    total_orbs = 0
    total_tries = 0
    total_successes = 0
    total_cost = 0
    total_revenue = 0
    total_profit = 0

    setup_deli_craft()

    for col in range(INVENTORY_GRID_COLS):
        for row in range(INVENTORY_GRID_ROWS):
            x = INVENTORY_GRID_START_X + col * INVENTORY_GRID_CELL_SIZE
            y = INVENTORY_GRID_START_Y + row * INVENTORY_GRID_CELL_SIZE
            coords = (x, y)
            orb = parse_deli_orb((x, y))

            if orb:
                record_orb(orb, "initial_seen")
                total_orbs += 1

                if not good_to_keep(orb):
                    ctrl_click(coords)
                    result = flip_orb()

                    total_tries += result["tries"]
                    total_successes += result["successes"]
                    total_cost += result["cost"]
                    total_revenue += result["revenue"]
                    total_profit += result["profit"]
                else:
                    value = orb_value(orb["type"])

                    record_orb(orb, "kept_seen")

                    total_successes += 1
                    total_revenue += value
                    total_profit += value

    one_in_n = (total_tries / total_successes) if total_successes else 0
    avg_cost_per_success = (total_cost / total_successes) if total_successes else 0
    roi = (total_profit / total_cost * 100) if total_cost else 0

    print("\n===== ORB FLIP KPI SUMMARY =====")
    print(f"Total orbs checked: {total_orbs}")
    print(f"Total tries: {total_tries}")
    print(f"Total successes: {total_successes}")
    print(f"Chance of success: 1 in {one_in_n:.2f} tries")
    print(f"Total cost: {total_cost}c")
    print(f"Total return: {total_revenue}c")
    print(f"Total profit: {total_profit}c")
    print(f"Average cost per success: {avg_cost_per_success:.2f}c")
    print(f"ROI: {roi:.2f}%")
    print("================================\n")

    print_observed_weights()
    print_kept_summary()
    compute_best_keep_combo()


if __name__ == "__main__":
    orb_flipper()