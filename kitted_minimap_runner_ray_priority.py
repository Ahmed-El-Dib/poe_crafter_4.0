import cv2
import numpy as np
import mss
import time
import math
import pyautogui

from images.image_utils import locate_center
from images.img_paths import STAIRS
from utils.initiate_session import requires_game_ready
from macros.rpa_macros import click, press

# =========================
# CONFIG
# =========================
MINIMAP = {
    "left": 1642,
    "top": 8,
    "width": 1905 - 1642,
    "height": 272 - 8,
}

FPS = 10
CHECK_DELAY = 1 / FPS

CLICK_ORIGIN = (955, 520)

# These are screen-space movement strengths, not minimap pixels.
# X/Y are intentionally separate because the game view is widescreen while the minimap is square-ish.
CLICK_STEP_X = 300
CLICK_STEP_Y = 200
UNSTICK_STEP_X = 500
UNSTICK_STEP_Y = 400

# If a ray only has a short safe run, reduce click strength.
MIN_RAY_CLEAR_LENGTH = 16
FULL_POWER_RAY_LENGTH = 55
MIN_CLICK_POWER = 0.42

STUCK_SECONDS = 0.5
CHANGE_THRESHOLD = 2500

# Fog/crosshair tuning
MIN_FOG_AREA = 35
FORK_MIN_SEPARATION = 25

# Ray tuning
RAY_COUNT = 96                  # dense radial scan
RAY_STEP = 2                    # minimap pixels per ray sample
RAY_MAX_LENGTH_PAD = 2          # allow scan to reach minimap edge
WALL_HIT_BUFFER = 2            # stay this many px before a wall hit
FOG_HIT_BUFFER = 3              # stay this many px before a fog hit
EDGE_HIT_BUFFER = 4             # stay this many px before minimap edge
MIN_CLEARANCE = 4.0
OBSTACLE_DILATE = 1

# Direction priority tuning
USE_DIRECTION_PRIORITY = True
PRIORITY_REFRESH_SECONDS = 7.0
PRIORITY_RANK_WEIGHT = 1500.0
PRIMARY_BONUS = 850.0
SECONDARY_BONUS = 360.0
ADJACENT_SOFT_BONUS = 160.0

# Ray scoring tuning
FOG_HIT_BONUS = 1300.0
EDGE_HIT_BONUS = 520.0
WALL_HIT_PENALTY = 1800.0
CLEAR_LENGTH_WEIGHT = 11.0
CLEARANCE_WEIGHT = 22.0
CENTER_STABILITY_WEIGHT = 4.0
ANGLE_STICKINESS_WEIGHT = 190.0

# If all priority rays are blocked, allow lower priority open rays.
OPEN_RAY_MIN_LENGTH = 24

# Smoothing: only commit a new direction if it wins clearly or the old one is bad.
LAST_GOOD_ANGLE = None
LAST_GOOD_DIRECTION = None
LAST_GOOD_TIME = 0
DIRECTION_LOCK_SECONDS = 0.35
SWITCH_SCORE_MARGIN = 180.0

# Mouse mode is click-based by request.
MOUSE_BUTTON = "left"

DEBUG = False
DEBUG_WINDOW = "minimap_ray_debug"

DIRECTION_ORDER = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"]
DIRECTION_INDEX = {name: i for i, name in enumerate(DIRECTION_ORDER)}

PRIMARY_FOG_DIR = None
SECONDARY_FOG_DIR = None
LAST_PRIORITY_SEEN = 0


# =========================
# DIRECTION / PRIORITY
# =========================
def circular_dir_distance(a, b):
    if a not in DIRECTION_INDEX or b not in DIRECTION_INDEX:
        return 99
    diff = abs(DIRECTION_INDEX[a] - DIRECTION_INDEX[b])
    return min(diff, len(DIRECTION_ORDER) - diff)


def adjacent_dirs(direction):
    if direction not in DIRECTION_INDEX:
        return []
    idx = DIRECTION_INDEX[direction]
    return [
        DIRECTION_ORDER[(idx - 1) % len(DIRECTION_ORDER)],
        DIRECTION_ORDER[(idx + 1) % len(DIRECTION_ORDER)],
    ]


def build_priority_ladder():
    """
    Example: primary=SW, secondary=SE -> SW, W, S, SE, E, ...
    Primary-adjacent direction farther from secondary gets priority.
    """
    ladder = []

    def add(direction):
        if direction and direction not in ladder:
            ladder.append(direction)

    add(PRIMARY_FOG_DIR)

    if PRIMARY_FOG_DIR:
        primary_adj = adjacent_dirs(PRIMARY_FOG_DIR)
        if SECONDARY_FOG_DIR:
            primary_adj.sort(key=lambda d: circular_dir_distance(d, SECONDARY_FOG_DIR), reverse=True)
        for direction in primary_adj:
            add(direction)

    add(SECONDARY_FOG_DIR)

    if SECONDARY_FOG_DIR:
        secondary_adj = adjacent_dirs(SECONDARY_FOG_DIR)
        if PRIMARY_FOG_DIR:
            secondary_adj.sort(key=lambda d: circular_dir_distance(d, PRIMARY_FOG_DIR), reverse=True)
        for direction in secondary_adj:
            add(direction)

    remaining = [d for d in DIRECTION_ORDER if d not in ladder]
    remaining.sort(key=lambda d: (
        circular_dir_distance(d, PRIMARY_FOG_DIR) if PRIMARY_FOG_DIR else 9,
        circular_dir_distance(d, SECONDARY_FOG_DIR) if SECONDARY_FOG_DIR else 9,
    ))
    ladder.extend(remaining)
    return ladder


def priority_rank(direction):
    if not USE_DIRECTION_PRIORITY or not (PRIMARY_FOG_DIR or SECONDARY_FOG_DIR):
        return 0
    ladder = build_priority_ladder()
    return ladder.index(direction) if direction in ladder else len(ladder) + 4


def priority_score_adjustment(direction):
    """Lower is better."""
    if not USE_DIRECTION_PRIORITY or not (PRIMARY_FOG_DIR or SECONDARY_FOG_DIR):
        return 0.0

    rank = priority_rank(direction)
    score = rank * PRIORITY_RANK_WEIGHT

    if direction == PRIMARY_FOG_DIR:
        score -= PRIMARY_BONUS
    elif direction == SECONDARY_FOG_DIR:
        score -= SECONDARY_BONUS
    elif PRIMARY_FOG_DIR and direction in adjacent_dirs(PRIMARY_FOG_DIR):
        score -= ADJACENT_SOFT_BONUS

    return score


def angle_to_direction(angle_deg):
    if -22.5 <= angle_deg < 22.5:
        return "E"
    if 22.5 <= angle_deg < 67.5:
        return "SE"
    if 67.5 <= angle_deg < 112.5:
        return "S"
    if 112.5 <= angle_deg < 157.5:
        return "SW"
    if angle_deg >= 157.5 or angle_deg < -157.5:
        return "W"
    if -157.5 <= angle_deg < -112.5:
        return "NW"
    if -112.5 <= angle_deg < -67.5:
        return "N"
    return "NE"


def direction_from_points(cx, cy, tx, ty):
    return angle_to_direction(math.degrees(math.atan2(ty - cy, tx - cx)))


def angle_diff_abs(a, b):
    return abs(math.atan2(math.sin(a - b), math.cos(a - b)))


# =========================
# SCREEN CLICK TRANSLATION
# =========================
def click_toward_ray_angle(angle, ray_length, unstuck=False):
    """
    Minimap rays provide direction and confidence only.
    Actual click is relative to CLICK_ORIGIN with separate X/Y screen scales.
    """
    ux = math.cos(angle)
    uy = math.sin(angle)

    step_x = UNSTICK_STEP_X if unstuck else CLICK_STEP_X
    step_y = UNSTICK_STEP_Y if unstuck else CLICK_STEP_Y

    # If the ray has limited visible safe space, reduce click strength.
    power = min(1.0, max(MIN_CLICK_POWER, ray_length / FULL_POWER_RAY_LENGTH))

    ox, oy = CLICK_ORIGIN
    x = int(ox + ux * step_x * power)
    y = int(oy + uy * step_y * power)

    pyautogui.moveTo(x, y, duration=0.025)
    pyautogui.click(x, y, button=MOUSE_BUTTON)
    return x, y, power


# =========================
# CAPTURE / DETECTION
# =========================
def capture_minimap():
    with mss.mss() as sct:
        img = np.array(sct.grab(MINIMAP))[:, :, :3]
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def find_crosshair(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, (8, 100, 130), (35, 255, 255))

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    h, w = mask.shape
    center_x, center_y = w // 2, h // 2

    candidates = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        y = stats[i, cv2.CC_STAT_TOP]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]

        if area < 2 or area > 80:
            continue
        if y > h * 0.85:
            continue

        cx, cy = centroids[i]
        dist_to_center = (cx - center_x) ** 2 + (cy - center_y) ** 2
        candidates.append((dist_to_center, int(cx), int(cy), area, bw, bh))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    _, cx, cy, *_ = candidates[0]
    return cx, cy


def detect_fog(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    fog = cv2.inRange(hsv, (85, 120, 180), (115, 255, 255))

    kernel = np.ones((5, 5), np.uint8)
    fog = cv2.dilate(fog, kernel, iterations=2)

    # Remove circular portal/icon effects.
    circles = cv2.HoughCircles(
        fog,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=20,
        param1=50,
        param2=12,
        minRadius=6,
        maxRadius=20,
    )
    if circles is not None:
        circles = np.round(circles[0]).astype(int)
        for x, y, r in circles:
            cv2.circle(fog, (x, y), r + 4, 0, -1)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fog)
    cleaned = np.zeros_like(fog)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > MIN_FOG_AREA:
            cleaned[labels == i] = 255

    return cleaned


def detect_wall_obstacles(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # Purple/blue outlines and cyan minimap boundary/fog glow are treated as hard blockers for rays.
    purple_wall = cv2.inRange(hsv, (105, 20, 65), (145, 145, 255))
    cyan_edge = cv2.inRange(hsv, (82, 80, 90), (110, 255, 255))
    orange = cv2.inRange(hsv, (8, 100, 120), (35, 255, 255))

    obstacle = cv2.bitwise_or(purple_wall, cyan_edge)
    obstacle = cv2.bitwise_and(obstacle, cv2.bitwise_not(orange))

    kernel = np.ones((3, 3), np.uint8)
    obstacle = cv2.morphologyEx(obstacle, cv2.MORPH_CLOSE, kernel, iterations=1)
    obstacle = cv2.dilate(obstacle, kernel, iterations=OBSTACLE_DILATE)
    return obstacle


def minimap_changed(old_img, new_img):
    if old_img is None:
        return True

    old_gray = cv2.cvtColor(old_img, cv2.COLOR_RGB2GRAY)
    new_gray = cv2.cvtColor(new_img, cv2.COLOR_RGB2GRAY)
    diff = cv2.absdiff(old_gray, new_gray)
    _, diff = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
    return np.count_nonzero(diff) > CHANGE_THRESHOLD


# =========================
# PRIORITY FROM FOG BLOBS
# =========================
def get_fog_blobs(fog, cx, cy):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fog)
    blobs = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < MIN_FOG_AREA:
            continue

        ys, xs = np.where(labels == i)
        d2 = (xs - cx) ** 2 + (ys - cy) ** 2
        closest_idx = int(np.argmin(d2))
        px = int(xs[closest_idx])
        py = int(ys[closest_idx])

        blobs.append({
            "id": i,
            "point": (px, py),
            "direction": direction_from_points(cx, cy, px, py),
            "distance": math.hypot(px - cx, py - cy),
            "area": int(area),
        })

    return blobs


def update_direction_priority_from_fog(fog, cx, cy):
    global PRIMARY_FOG_DIR, SECONDARY_FOG_DIR, LAST_PRIORITY_SEEN

    if not USE_DIRECTION_PRIORITY:
        return []

    blobs = get_fog_blobs(fog, cx, cy)
    if not blobs:
        return []

    now = time.time()
    dirs_present = {b["direction"] for b in blobs}

    if PRIMARY_FOG_DIR in dirs_present or SECONDARY_FOG_DIR in dirs_present:
        LAST_PRIORITY_SEEN = now
        return blobs

    if PRIMARY_FOG_DIR is not None and now - LAST_PRIORITY_SEEN < PRIORITY_REFRESH_SECONDS:
        return blobs

    by_dir = {}
    for blob in blobs:
        direction = blob["direction"]
        if direction not in by_dir or blob["distance"] < by_dir[direction]["distance"]:
            by_dir[direction] = blob

    ordered = sorted(by_dir.values(), key=lambda b: b["distance"])
    if not ordered:
        return blobs

    primary = ordered[0]
    secondary = None
    for candidate in ordered[1:]:
        dist = math.hypot(
            candidate["point"][0] - primary["point"][0],
            candidate["point"][1] - primary["point"][1],
        )
        if dist >= FORK_MIN_SEPARATION:
            secondary = candidate
            break

    PRIMARY_FOG_DIR = primary["direction"]
    SECONDARY_FOG_DIR = secondary["direction"] if secondary else None
    LAST_PRIORITY_SEEN = now

    print(f"fog priority set: primary={PRIMARY_FOG_DIR} secondary={SECONDARY_FOG_DIR}")
    return blobs


# =========================
# RAYCASTING
# =========================
def inside_minimap(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def cast_ray(obstacle, fog, clearance, cx, cy, angle):
    """
    Ray starts at player and stops on fog, wall, or minimap edge.
    Returns the safest point before the hit, plus score metadata.
    """
    h, w = obstacle.shape
    ux = math.cos(angle)
    uy = math.sin(angle)

    max_len = int(math.hypot(w, h)) + RAY_MAX_LENGTH_PAD
    last_safe = None
    best_clearance_seen = 0.0
    hit_type = "edge"
    hit_len = 0

    for dist in range(1, max_len + 1, RAY_STEP):
        x = int(round(cx + ux * dist))
        y = int(round(cy + uy * dist))

        if not inside_minimap(x, y, w, h):
            hit_type = "edge"
            hit_len = dist
            break

        if obstacle[y, x] > 0:
            hit_type = "wall"
            hit_len = dist
            break

        clear = float(clearance[y, x]) if clearance is not None else 0.0
        best_clearance_seen = max(best_clearance_seen, clear)

        # Pixel is traversable enough to be a click-direction candidate.
        if clear >= MIN_CLEARANCE:
            last_safe = (x, y, dist, clear)

        if fog[y, x] > 0:
            hit_type = "fog"
            hit_len = dist
            break

    if hit_len == 0:
        hit_len = max_len

    if hit_type == "wall":
        target_len = max(0, hit_len - WALL_HIT_BUFFER)
    elif hit_type == "fog":
        target_len = max(0, hit_len - FOG_HIT_BUFFER)
    else:
        target_len = max(0, hit_len - EDGE_HIT_BUFFER)

    tx = int(round(cx + ux * target_len))
    ty = int(round(cy + uy * target_len))

    if not inside_minimap(tx, ty, w, h):
        return None

    # Prefer a known safe sample. If target_len lands on a low-clearance pixel, fall back to last safe.
    target_clearance = float(clearance[ty, tx]) if clearance is not None else 0.0
    if target_clearance < MIN_CLEARANCE and last_safe is not None:
        tx, ty, target_len, target_clearance = last_safe

    if target_len < MIN_RAY_CLEAR_LENGTH:
        return None

    direction = angle_to_direction(math.degrees(angle))

    return {
        "angle": angle,
        "direction": direction,
        "target": (tx, ty),
        "hit_type": hit_type,
        "hit_len": hit_len,
        "safe_len": target_len,
        "clearance": target_clearance,
        "max_clearance": best_clearance_seen,
    }


def score_ray(ray):
    score = 0.0

    # Lower priority rank is better, so subtract the adjustment.
    score -= priority_score_adjustment(ray["direction"])

    if ray["hit_type"] == "fog":
        score += FOG_HIT_BONUS
    elif ray["hit_type"] == "edge":
        score += EDGE_HIT_BONUS
    elif ray["hit_type"] == "wall":
        score -= WALL_HIT_PENALTY

    score += min(ray["safe_len"], FULL_POWER_RAY_LENGTH * 1.8) * CLEAR_LENGTH_WEIGHT
    score += min(ray["clearance"], 18.0) * CLEARANCE_WEIGHT

    # Prefer the middle of broad open corridors over rays scraping one side.
    score += min(ray["max_clearance"], 20.0) * CENTER_STABILITY_WEIGHT

    # Mild stickiness to avoid left/right flicker when scores are close.
    if LAST_GOOD_ANGLE is not None and time.time() - LAST_GOOD_TIME < DIRECTION_LOCK_SECONDS:
        score -= angle_diff_abs(ray["angle"], LAST_GOOD_ANGLE) * ANGLE_STICKINESS_WEIGHT

    return score


def choose_best_ray(img, fog, cx, cy, unstuck=False):
    global LAST_GOOD_ANGLE, LAST_GOOD_DIRECTION, LAST_GOOD_TIME

    obstacle = detect_wall_obstacles(img)

    # Fog should stop rays, not be part of wall mask. Obstacles are just solid walls/edges.
    free = (obstacle == 0).astype(np.uint8)
    clearance = cv2.distanceTransform(free, cv2.DIST_L2, 5)

    update_direction_priority_from_fog(fog, cx, cy)

    rays = []
    for i in range(RAY_COUNT):
        angle = -math.pi + (2 * math.pi * i / RAY_COUNT)
        ray = cast_ray(obstacle, fog, clearance, cx, cy, angle)
        if ray is None:
            continue
        if ray["safe_len"] < OPEN_RAY_MIN_LENGTH and ray["hit_type"] != "fog":
            continue
        ray["score"] = score_ray(ray)
        rays.append(ray)

    if not rays:
        return None, obstacle, clearance, []

    if unstuck:
        # Ignore fog/priority mostly; pick longest, clearest open direction.
        for ray in rays:
            ray["score"] = (
                ray["safe_len"] * 18.0
                + ray["clearance"] * 45.0
                - (900.0 if ray["hit_type"] == "wall" else 0.0)
            )

    rays.sort(key=lambda r: r["score"], reverse=True)
    best = rays[0]

    # Direction lock: if old direction is still valid and close in score, keep it briefly.
    if not unstuck and LAST_GOOD_DIRECTION and time.time() - LAST_GOOD_TIME < DIRECTION_LOCK_SECONDS:
        same_dir = [r for r in rays if r["direction"] == LAST_GOOD_DIRECTION]
        if same_dir:
            old_best = max(same_dir, key=lambda r: r["score"])
            if best["score"] - old_best["score"] < SWITCH_SCORE_MARGIN:
                best = old_best

    LAST_GOOD_ANGLE = best["angle"]
    LAST_GOOD_DIRECTION = best["direction"]
    LAST_GOOD_TIME = time.time()

    return best, obstacle, clearance, rays


# =========================
# DEBUG
# =========================
def draw_debug(img, obstacle, fog, rays, best, crosshair):
    if not DEBUG:
        return

    out = img.copy()
    out[obstacle > 0] = (255, 0, 0)
    out[fog > 0] = (0, 200, 255)

    cx, cy = crosshair
    for ray in rays[:18]:
        tx, ty = ray["target"]
        cv2.line(out, (cx, cy), (tx, ty), (80, 80, 80), 1)

    if best:
        tx, ty = best["target"]
        cv2.line(out, (cx, cy), (tx, ty), (0, 255, 255), 2)
        cv2.circle(out, (tx, ty), 4, (0, 255, 255), -1)

    cv2.circle(out, (cx, cy), 4, (255, 128, 0), -1)

    cv2.imshow(DEBUG_WINDOW, cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    cv2.waitKey(1)


# =========================
# MAIN LOOP
# =========================
@requires_game_ready()
def main():
    global PRIMARY_FOG_DIR, SECONDARY_FOG_DIR, LAST_GOOD_ANGLE, LAST_GOOD_DIRECTION

    previous_second_img = None
    last_stuck_check = time.time()
    stuck_ticks = 0

    try:
        while True:
            img = capture_minimap()
            crosshair = find_crosshair(img)
            fog = detect_fog(img)

            if crosshair is None:
                print("crosshair: not found")
                time.sleep(CHECK_DELAY)
                continue

            cx, cy = crosshair

            if np.count_nonzero(fog) == 0:
                PRIMARY_FOG_DIR = None
                SECONDARY_FOG_DIR = None
                LAST_GOOD_ANGLE = None
                LAST_GOOD_DIRECTION = None

                coords = locate_center(STAIRS, confidence=0.8)
                if coords:
                    click(coords)
                    time.sleep(1)
                    press("e")
                    time.sleep(1)
                    click((1648, 890))
                    break

                print(f"player=({cx},{cy}) fog=not_found stairs=not_found")
                time.sleep(CHECK_DELAY)
                continue

            now = time.time()
            stuck = False
            if now - last_stuck_check >= STUCK_SECONDS:
                stuck = not minimap_changed(previous_second_img, img)
                previous_second_img = img.copy()
                last_stuck_check = now
                stuck_ticks = stuck_ticks + 1 if stuck else 0

            best, obstacle, clearance, rays = choose_best_ray(img, fog, cx, cy, unstuck=stuck_ticks >= 1)

            if best is None:
                print(f"player=({cx},{cy}) ray=none stuck={stuck} stuck_ticks={stuck_ticks}")
                time.sleep(CHECK_DELAY)
                continue

            draw_debug(img, obstacle, fog, rays, best, (cx, cy))

            mx, my, power = click_toward_ray_angle(
                best["angle"],
                best["safe_len"],
                unstuck=stuck_ticks >= 1,
            )

            mode = "unstuck_ray" if stuck_ticks >= 1 else "priority_ray"
            print(
                f"player=({cx},{cy}) "
                f"ray_dir={best['direction']} hit={best['hit_type']} "
                f"safe_len={best['safe_len']:.1f} clear={best['clearance']:.1f} "
                f"score={best['score']:.1f} power={power:.2f} "
                f"primary={PRIMARY_FOG_DIR} secondary={SECONDARY_FOG_DIR} "
                f"ladder={build_priority_ladder() if (PRIMARY_FOG_DIR or SECONDARY_FOG_DIR) else []} "
                f"clicked=({mx},{my}) stuck={stuck} stuck_ticks={stuck_ticks} mode={mode}"
            )

            time.sleep(CHECK_DELAY)

    finally:
        # No held mouse state in this version.
        pass


if __name__ == "__main__":
    main()
