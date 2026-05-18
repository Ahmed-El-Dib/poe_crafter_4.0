import cv2
import numpy as np
import mss
import time
import math
import heapq
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
CLICK_STEP = 300
UNSTICK_CLICK_STEP = 620

STUCK_SECONDS = 0.5
CHANGE_THRESHOLD = 2500

# Fog/crosshair tuning
MIN_FOG_AREA = 40
FORK_MIN_SEPARATION = 25

# Frontier fog targeting
# Instead of chasing the closest fog pixel, only use fog that touches reachable hallway.
FOG_FRONTIER_DILATE = 3          # how far from reachable hallway fog may be considered relevant
FOG_FRONTIER_GOAL_DILATE = 4     # how far back into hallway to pick the safe goal beside fog
MIN_FRONTIER_AREA = 8
MIN_FRONTIER_CONTACT = 10
MAX_ROUND_ICON_AREA = 90
ROUND_ICON_ASPECT_LIMIT = 1.45


# Navigation tuning
OBSTACLE_DILATE = 2          # thicker walls = safer, but too high can close narrow halls
MIN_CLEARANCE = 4.0          # minimum pixels away from walls/edges on minimap
IDEAL_WAYPOINT_DIST = 42     # how far ahead along the minimap path to aim
MAX_WAYPOINT_DIST = 58
REPLAN_EVERY_SECONDS = 0.17
GOAL_LOCK_SECONDS = 2.0
GOAL_RELOCK_DISTANCE = 30

# Direction priority tuning
# Primary/secondary are chosen once from the first real fork, then strongly preferred.
# This preserves route intent without allowing straight-line wall crossing.
USE_DIRECTION_PRIORITY = True
PRIMARY_DIRECTION_BONUS = 900.0
SECONDARY_DIRECTION_BONUS = 420.0
WRONG_DIRECTION_PENALTY = 260.0
PRIORITY_RANK_PENALTY = 950.0
PRIORITY_REFRESH_SECONDS = 7.0     # if primary disappears for this long, allow a new primary/secondary pair

# A* tuning
ASTAR_DOWNSCALE = 2          # 2 is much faster. Use 1 if your minimap is tiny/fragile.
ASTAR_MAX_VISITED = 14000
CLEARANCE_COST_WEIGHT = 18.0
TURN_COST_WEIGHT = 0.25

# Fallback ray sampler tuning
RAY_COUNT = 32
RAY_MINI_STEP = 48
RAY_CHECK_SAMPLES = 32

DEBUG = False
DEBUG_WINDOW = "minimap_nav_debug"

# Mouse movement mode
# Holds the movement mouse button down after the first navigation press.
# The script then only moves the cursor to steer; it does not spam click.
HOLD_MOUSE_BUTTON = False
MOUSE_BUTTON = "left"
MOUSE_IS_DOWN = False

DIRECTION_ORDER = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"]
DIRECTION_INDEX = {name: i for i, name in enumerate(DIRECTION_ORDER)}

def estimate_corridor_flow(walkable, cx, cy):
    radius = 25

    ys, xs = np.where(walkable > 0)

    pts = []

    for x, y in zip(xs, ys):
        dx = x - cx
        dy = y - cy

        d = math.hypot(dx, dy)

        if 6 < d < radius:
            pts.append([dx, dy])

    if len(pts) < 8:
        return (0, -1)

    pts = np.array(pts, dtype=np.float32)

    mean, eigenvectors = cv2.PCACompute(pts, mean=None)

    vx, vy = eigenvectors[0]

    # choose direction pointing away from center mass
    if vy > 0:
        vx, vy = -vx, -vy

    return (vx, vy)

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
    Route preference ladder.
    Example: primary=SW, secondary=SE -> SW, W, S, SE, E, ...
    The primary-adjacent direction farther from secondary wins first.
    Then secondary, then secondary-adjacent directions farther from primary.
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

    # Add remaining directions by closeness to primary first, then secondary.
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
    if direction in ladder:
        return ladder.index(direction)
    return len(ladder) + 4

# Runtime state
LOCKED_GOAL = None
LOCKED_GOAL_TIME = 0
LAST_PATH = []
LAST_REPLAN = 0
PRIMARY_FOG_DIR = None
SECONDARY_FOG_DIR = None
LAST_PRIORITY_SEEN = 0


# =========================
# BASIC UTILS
# =========================
def direction_to_vector(direction):
    mapping = {
        "N":  (0, -1),
        "NE": (1, -1),
        "E":  (1, 0),
        "SE": (1, 1),
        "S":  (0, 1),
        "SW": (-1, 1),
        "W":  (-1, 0),
        "NW": (-1, -1),
    }
    dx, dy = mapping[direction]
    length = math.hypot(dx, dy)
    return dx / length, dy / length


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
    angle = math.degrees(math.atan2(ty - cy, tx - cx))
    return angle_to_direction(angle)


def hold_mouse_down_once():
    global MOUSE_IS_DOWN

    if HOLD_MOUSE_BUTTON and not MOUSE_IS_DOWN:
        pyautogui.mouseDown(button=MOUSE_BUTTON)
        MOUSE_IS_DOWN = True


def release_mouse_if_held():
    global MOUSE_IS_DOWN

    if MOUSE_IS_DOWN:
        pyautogui.mouseUp(button=MOUSE_BUTTON)
        MOUSE_IS_DOWN = False


def click_toward_vector(dx, dy, step):
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None

    dx /= length
    dy /= length
    ox, oy = CLICK_ORIGIN
    x = int(ox + dx * step)
    y = int(oy + dy * step)

    pyautogui.moveTo(x, y, duration=0.025)

    if HOLD_MOUSE_BUTTON:
        # First movement target presses the button down. After that, steering is
        # done by moving the cursor only. No repeated click/up events.
        hold_mouse_down_once()
    else:
        pyautogui.click(x, y, button=MOUSE_BUTTON)

    return x, y


def click_toward_point(cx, cy, tx, ty, step=CLICK_STEP):
    return click_toward_vector(tx - cx, ty - cy, step)


def capture_minimap():
    with mss.mss() as sct:
        img = np.array(sct.grab(MINIMAP))[:, :, :3]
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# =========================
# DETECTION
# =========================
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

    # Remove portal circles / circular effects if they look like fog.
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


def detect_wall_obstacles(img, fog=None, block_fog=True):
    """
    Detect minimap outlines/walls/edges as obstacle pixels.
    This is intentionally conservative: walls are dilated so the route prefers hallway centers.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # Pale purple/blue minimap outlines.
    purple_wall = cv2.inRange(hsv, (105, 20, 65), (145, 145, 255))

    # Bright cyan fog edge / map glow should also not be crossed.
    cyan_edge = cv2.inRange(hsv, (82, 80, 90), (110, 255, 255))

    # Orange player/crosshair is not an obstacle.
    orange = cv2.inRange(hsv, (8, 100, 120), (35, 255, 255))

    obstacle = cv2.bitwise_or(purple_wall, cyan_edge)
    obstacle = cv2.bitwise_and(obstacle, cv2.bitwise_not(orange))

    # Fog is a target frontier, not walkable. Keep it blocked so A* stops beside it.
    # Some callers pass block_fog=False when building local geometry only.
    if block_fog and fog is not None:
        obstacle = cv2.bitwise_or(obstacle, fog)

    kernel = np.ones((3, 3), np.uint8)
    obstacle = cv2.morphologyEx(obstacle, cv2.MORPH_CLOSE, kernel, iterations=1)
    obstacle = cv2.dilate(obstacle, kernel, iterations=OBSTACLE_DILATE)

    return obstacle


def flood_reachable_from_player(obstacle, cx, cy):
    """
    Build a reachable mask from the player through non-obstacle pixels.
    This prevents straight-line wall crossing and keeps target selection local to connected halls.
    """
    h, w = obstacle.shape
    free = (obstacle == 0).astype(np.uint8)

    # Keep flood fill from leaking through the whole black background too easily.
    # We still allow a large area because hall interiors are often dark.
    border_blocked = free.copy()
    border_blocked[0, :] = 0
    border_blocked[-1, :] = 0
    border_blocked[:, 0] = 0
    border_blocked[:, -1] = 0

    seed = nearest_free_pixel(border_blocked, cx, cy, max_radius=12)
    if seed is None:
        return np.zeros_like(obstacle)

    sx, sy = seed
    mask = np.zeros((h + 2, w + 2), np.uint8)
    filled = border_blocked.copy()
    cv2.floodFill(filled, mask, (sx, sy), 2)
    reachable = (filled == 2).astype(np.uint8) * 255

    return reachable


def nearest_free_pixel(mask, x, y, max_radius=30):
    h, w = mask.shape
    x = int(np.clip(x, 0, w - 1))
    y = int(np.clip(y, 0, h - 1))

    if mask[y, x] > 0:
        return x, y

    for r in range(1, max_radius + 1):
        x0, x1 = max(0, x - r), min(w - 1, x + r)
        y0, y1 = max(0, y - r), min(h - 1, y + r)
        candidates = []

        for xx in range(x0, x1 + 1):
            candidates.append((xx, y0))
            candidates.append((xx, y1))
        for yy in range(y0, y1 + 1):
            candidates.append((x0, yy))
            candidates.append((x1, yy))

        best = None
        best_d2 = 10**9
        for xx, yy in candidates:
            if mask[yy, xx] > 0:
                d2 = (xx - x) ** 2 + (yy - y) ** 2
                if d2 < best_d2:
                    best_d2 = d2
                    best = (xx, yy)
        if best:
            return best

    return None


# =========================
# FOG TARGETING
# =========================
def make_fog_frontiers(fog, reachable, clearance, cx, cy):
    """
    Return meaningful fog frontier clusters.

    Raw fog blobs can be huge and wrap around walls, so chasing the closest fog
    pixel is misleading. A valid frontier is fog that touches the currently
    reachable hallway. Each frontier stores a hallway-side goal candidate, so
    movement targets the path entrance into fog rather than the fog mass itself.
    """
    safe = ((reachable > 0) & (clearance >= MIN_CLEARANCE)).astype(np.uint8) * 255
    if np.count_nonzero(safe) == 0:
        safe = reachable.copy()

    near_reachable = cv2.dilate(
        reachable,
        np.ones((FOG_FRONTIER_DILATE, FOG_FRONTIER_DILATE), np.uint8),
        iterations=2,
    )

    # Only fog touching the reachable hallway can be a useful target.
    frontier = cv2.bitwise_and(fog, near_reachable)

    # Reduce chunky fog regions into contact patches. This makes big fog areas
    # split by hallway openings instead of becoming one misleading blob.
    frontier = cv2.morphologyEx(frontier, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(frontier)
    frontiers = []

    for i in range(1, num_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < MIN_FRONTIER_AREA:
            continue

        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        aspect = max(w, h) / max(min(w, h), 1)

        # Reject tiny round icon-like leftovers. Real fog/path contact usually
        # has some length or enough area.
        if area <= MAX_ROUND_ICON_AREA and aspect <= ROUND_ICON_ASPECT_LIMIT:
            continue

        component = (labels == i).astype(np.uint8) * 255

        hallway_contact = cv2.bitwise_and(
            cv2.dilate(component, np.ones((3, 3), np.uint8), iterations=1),
            reachable,
        )
        contact_pixels = int(np.count_nonzero(hallway_contact))
        if contact_pixels < MIN_FRONTIER_CONTACT:
            continue

        # Pick a safe hallway-side goal next to this frontier.
        goal_zone = cv2.bitwise_and(
            cv2.dilate(component, np.ones((FOG_FRONTIER_GOAL_DILATE, FOG_FRONTIER_GOAL_DILATE), np.uint8), iterations=2),
            safe,
        )
        gy, gx = np.where(goal_zone > 0)
        if len(gx) == 0:
            # Looser fallback: reachable, even if low clearance.
            goal_zone = cv2.bitwise_and(
                cv2.dilate(component, np.ones((FOG_FRONTIER_GOAL_DILATE + 2, FOG_FRONTIER_GOAL_DILATE + 2), np.uint8), iterations=2),
                reachable,
            )
            gy, gx = np.where(goal_zone > 0)
            if len(gx) == 0:
                continue

        fx, fy = centroids[i]
        best_goal = None
        best_score = float("inf")

        for px, py in zip(gx, gy):
            px = int(px)
            py = int(py)
            dist_to_frontier = math.hypot(px - fx, py - fy)
            dist_to_player = math.hypot(px - cx, py - cy)
            clear = float(clearance[py, px])
            goal_dir = direction_from_points(cx, cy, px, py)

            score = (
                dist_to_frontier * 2.0
                + dist_to_player * 0.18
                - clear * 2.4
                + direction_priority_adjustment(goal_dir) * 0.45
            )
            if score < best_score:
                best_score = score
                best_goal = (px, py)

        if best_goal is None:
            continue

        direction_point = best_goal
        direction = direction_from_points(cx, cy, direction_point[0], direction_point[1])

        # Keep a fog-side point too for priority/fork separation logging.
        ys, xs = np.where(labels == i)
        d2 = (xs - cx) ** 2 + (ys - cy) ** 2
        closest_idx = int(np.argmin(d2))
        fog_point = (int(xs[closest_idx]), int(ys[closest_idx]))
        fog_direction = direction_from_points(cx, cy, fog_point[0], fog_point[1])

        frontiers.append({
            "id": i,
            "area": area,
            "contact": contact_pixels,
            "bbox": (x, y, w, h),
            "point": fog_point,
            "goal": best_goal,
            "direction": direction,
            "fog_direction": fog_direction,
            "distance": math.hypot(best_goal[0] - cx, best_goal[1] - cy),
            "centroid": (float(fx), float(fy)),
        })

    return frontiers, frontier


def update_direction_priority(frontiers):
    """
    Pick primary/secondary once from separated frontier directions, then keep
    them sticky. Frontiers are hallway-side openings, which are more reliable
    than raw fog blob directions.
    """
    global PRIMARY_FOG_DIR, SECONDARY_FOG_DIR, LAST_PRIORITY_SEEN

    if not USE_DIRECTION_PRIORITY or not frontiers:
        return

    now = time.time()
    dirs_present = {f["direction"] for f in frontiers}

    if PRIMARY_FOG_DIR in dirs_present or SECONDARY_FOG_DIR in dirs_present:
        LAST_PRIORITY_SEEN = now
        return

    # If both priority dirs vanished for a while, treat this as a new fork/branch.
    if PRIMARY_FOG_DIR is not None and now - LAST_PRIORITY_SEEN < PRIORITY_REFRESH_SECONDS:
        return

    by_dir = {}
    for f in frontiers:
        direction = f["direction"]
        if direction not in by_dir or f["distance"] < by_dir[direction]["distance"]:
            by_dir[direction] = f

    ordered = sorted(by_dir.values(), key=lambda f: f["distance"])
    if not ordered:
        return

    primary = ordered[0]
    secondary = None

    for candidate in ordered[1:]:
        dist = math.hypot(
            candidate["goal"][0] - primary["goal"][0],
            candidate["goal"][1] - primary["goal"][1],
        )
        # At first forks, primary/secondary usually sit near right angles. Prefer
        # clearly separated openings so noise does not become the secondary.
        dir_sep = circular_dir_distance(primary["direction"], candidate["direction"])
        if dist >= FORK_MIN_SEPARATION and dir_sep >= 2:
            secondary = candidate
            break

    PRIMARY_FOG_DIR = primary["direction"]
    SECONDARY_FOG_DIR = secondary["direction"] if secondary else None
    LAST_PRIORITY_SEEN = now

    print(f"fog priority set: primary={PRIMARY_FOG_DIR} secondary={SECONDARY_FOG_DIR}")


def direction_priority_adjustment(direction):
    """
    Lower score is better. This is intentionally much stronger than distance.
    It lets A* keep safety/wall avoidance, but goal selection follows:
    primary -> primary-adjacent farther from secondary -> other primary-adjacent
    -> secondary -> secondary-adjacent farther from primary -> everything else.
    """
    if not USE_DIRECTION_PRIORITY or not (PRIMARY_FOG_DIR or SECONDARY_FOG_DIR):
        return 0.0

    rank = priority_rank(direction)
    bonus = 0.0
    if direction == PRIMARY_FOG_DIR:
        bonus = PRIMARY_DIRECTION_BONUS
    elif direction == SECONDARY_FOG_DIR:
        bonus = SECONDARY_DIRECTION_BONUS

    return rank * PRIORITY_RANK_PENALTY - bonus


def choose_reachable_goal(fog, reachable, clearance, cx, cy):
    """
    Pick a reachable safe hallway pixel adjacent to a meaningful fog frontier.
    This avoids chasing random fog pixels inside huge fog regions or UI/icon noise.
    """
    global LOCKED_GOAL, LOCKED_GOAL_TIME

    now = time.time()
    frontiers, _ = make_fog_frontiers(fog, reachable, clearance, cx, cy)
    if not frontiers:
        LOCKED_GOAL = None
        return None

    update_direction_priority(frontiers)

    candidates = []
    for f in frontiers:
        gx, gy = f["goal"]
        goal_direction = direction_from_points(cx, cy, gx, gy)
        frontier_direction = f["direction"]
        dist_to_player = math.hypot(gx - cx, gy - cy)
        clear_bonus = float(clearance[gy, gx])

        # Reward actual hallway contact, not just fog area. This prevents large
        # fog masses from dominating if only a tiny piece touches the path.
        contact_bonus = min(f["contact"], 80) * 1.5
        area_penalty = max(0, f["area"] - 250) * 0.015

        score = (
            dist_to_player * 0.38
            - clear_bonus * 2.0
            - contact_bonus
            + area_penalty
            + direction_priority_adjustment(frontier_direction) * 1.0
            + direction_priority_adjustment(goal_direction) * 0.65
        )
        candidates.append((score, gx, gy, f))

    candidates.sort(key=lambda item: item[0])
    _, best_x, best_y, best_frontier = candidates[0]
    best = (best_x, best_y)

    # Keep a short goal lock only if it still agrees with the active priority ladder.
    if LOCKED_GOAL is not None and now - LOCKED_GOAL_TIME < GOAL_LOCK_SECONDS:
        lx, ly = LOCKED_GOAL
        h, w = reachable.shape
        if 0 <= lx < w and 0 <= ly < h and reachable[ly, lx] > 0:
            locked_dir = direction_from_points(cx, cy, lx, ly)
            best_dir = direction_from_points(cx, cy, best[0], best[1])
            if priority_rank(locked_dir) <= priority_rank(best_dir):
                return LOCKED_GOAL

    if LOCKED_GOAL is None or math.hypot(best[0] - LOCKED_GOAL[0], best[1] - LOCKED_GOAL[1]) > GOAL_RELOCK_DISTANCE:
        LOCKED_GOAL_TIME = now

    LOCKED_GOAL = best
    return LOCKED_GOAL

# =========================
# A* PATHING
# =========================
def downscale_mask(mask, factor):
    if factor <= 1:
        return mask.copy()
    h, w = mask.shape
    small = cv2.resize(mask, (w // factor, h // factor), interpolation=cv2.INTER_NEAREST)
    return small


def astar_path(reachable, clearance, start, goal):
    factor = ASTAR_DOWNSCALE

    small_reach = downscale_mask(reachable, factor)
    small_clear = cv2.resize(clearance, (small_reach.shape[1], small_reach.shape[0]), interpolation=cv2.INTER_AREA)

    sx, sy = int(start[0] / factor), int(start[1] / factor)
    gx, gy = int(goal[0] / factor), int(goal[1] / factor)

    h, w = small_reach.shape
    if not (0 <= sx < w and 0 <= sy < h and 0 <= gx < w and 0 <= gy < h):
        return []

    if small_reach[sy, sx] == 0:
        ns = nearest_free_pixel(small_reach, sx, sy, max_radius=8)
        if ns is None:
            return []
        sx, sy = ns

    if small_reach[gy, gx] == 0:
        ng = nearest_free_pixel(small_reach, gx, gy, max_radius=16)
        if ng is None:
            return []
        gx, gy = ng

    neighbors = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414),
    ]

    def heuristic(x, y):
        return math.hypot(gx - x, gy - y)

    open_heap = []
    heapq.heappush(open_heap, (heuristic(sx, sy), 0.0, sx, sy, 0, 0))

    came_from = {}
    best_g = {(sx, sy): 0.0}
    visited = 0

    while open_heap and visited < ASTAR_MAX_VISITED:
        _, g, x, y, pdx, pdy = heapq.heappop(open_heap)
        visited += 1

        if (x, y) == (gx, gy):
            path = [(x, y)]
            while (x, y) in came_from:
                x, y = came_from[(x, y)]
                path.append((x, y))
            path.reverse()
            return [(px * factor, py * factor) for px, py in path]

        if g > best_g.get((x, y), float("inf")) + 1e-6:
            continue

        for dx, dy, base_cost in neighbors:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            if small_reach[ny, nx] == 0:
                continue

            # Prevent diagonal corner cutting through blocked pixels.
            if dx != 0 and dy != 0:
                if small_reach[y, nx] == 0 or small_reach[ny, x] == 0:
                    continue

            clear = max(float(small_clear[ny, nx]), 0.1)
            clearance_penalty = CLEARANCE_COST_WEIGHT / clear
            turn_penalty = 0.0
            if (pdx, pdy) != (0, 0) and (dx, dy) != (pdx, pdy):
                turn_penalty = TURN_COST_WEIGHT

            ng = g + base_cost + clearance_penalty + turn_penalty
            if ng < best_g.get((nx, ny), float("inf")):
                best_g[(nx, ny)] = ng
                came_from[(nx, ny)] = (x, y)
                f = ng + heuristic(nx, ny)
                heapq.heappush(open_heap, (f, ng, nx, ny, dx, dy))

    return []


def waypoint_from_path(path, cx, cy):
    if not path:
        return None

    last = (cx, cy)
    traveled = 0.0

    for p in path[1:]:
        seg = math.hypot(p[0] - last[0], p[1] - last[1])
        traveled += seg
        last = p

        if traveled >= IDEAL_WAYPOINT_DIST:
            return p

    # Path is short; use the furthest safe point available.
    return path[-1]


# =========================
# FALLBACK: SAFE RAY SAMPLER
# =========================
def line_clear(obstacle, cx, cy, tx, ty):
    h, w = obstacle.shape
    for i in range(RAY_CHECK_SAMPLES + 1):
        t = i / RAY_CHECK_SAMPLES
        x = int(round(cx + (tx - cx) * t))
        y = int(round(cy + (ty - cy) * t))
        if not (0 <= x < w and 0 <= y < h):
            return False
        if obstacle[y, x] > 0:
            return False
    return True


def fallback_safe_ray_target(obstacle, clearance, fog, cx, cy, reachable=None):
    if reachable is None:
        reachable = flood_reachable_from_player(obstacle, cx, cy)

    frontiers, _ = make_fog_frontiers(fog, reachable, clearance, cx, cy)
    if frontiers:
        # Use the best frontier goal as the desired direction for local ray fallback.
        frontiers.sort(key=lambda f: (
            direction_priority_adjustment(f["direction"]),
            f["distance"],
            -f["contact"],
        ))
        desired_x, desired_y = frontiers[0]["goal"]
    else:
        fog_ys, fog_xs = np.where(fog > 0)
        if len(fog_xs) == 0:
            return None
        desired_x = float(np.mean(fog_xs))
        desired_y = float(np.mean(fog_ys))

    h, w = obstacle.shape
    best = None
    best_score = -float("inf")

    desired_angle = math.atan2(desired_y - cy, desired_x - cx)

    for i in range(RAY_COUNT):
        angle = -math.pi + (2 * math.pi * i / RAY_COUNT)
        tx = int(round(cx + math.cos(angle) * RAY_MINI_STEP))
        ty = int(round(cy + math.sin(angle) * RAY_MINI_STEP))

        if not (0 <= tx < w and 0 <= ty < h):
            continue
        if obstacle[ty, tx] > 0:
            continue
        if reachable[ty, tx] == 0:
            continue
        if not line_clear(obstacle, cx, cy, tx, ty):
            continue

        clear = float(clearance[ty, tx])
        if clear < MIN_CLEARANCE:
            continue

        angle_diff = abs(math.atan2(math.sin(angle - desired_angle), math.cos(angle - desired_angle)))
        progress = -angle_diff
        desired_dist = math.hypot(tx - desired_x, ty - desired_y)
        ray_dir = angle_to_direction(math.degrees(angle))
        score = progress * 55.0 - desired_dist * 0.16 + clear * 3.2 - direction_priority_adjustment(ray_dir) * 0.85

        if score > best_score:
            best_score = score
            best = (tx, ty)

    return best


# =========================
# STUCK / DEBUG
# =========================
def minimap_changed(old_img, new_img):
    if old_img is None:
        return True

    old_gray = cv2.cvtColor(old_img, cv2.COLOR_RGB2GRAY)
    new_gray = cv2.cvtColor(new_img, cv2.COLOR_RGB2GRAY)
    diff = cv2.absdiff(old_gray, new_gray)
    _, diff = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
    changed_pixels = np.count_nonzero(diff)
    return changed_pixels > CHANGE_THRESHOLD


def draw_debug(img, obstacle, reachable, path, goal, waypoint, crosshair):
    if not DEBUG:
        return

    out = img.copy()
    out[obstacle > 0] = (255, 0, 0)
    out[reachable > 0] = (0, 60, 0)

    if path:
        for x, y in path:
            cv2.circle(out, (int(x), int(y)), 1, (255, 255, 0), -1)

    if goal:
        cv2.circle(out, goal, 5, (255, 0, 255), 2)
    if waypoint:
        cv2.circle(out, waypoint, 5, (0, 255, 255), 2)
    if crosshair:
        cv2.circle(out, crosshair, 4, (255, 128, 0), -1)

    cv2.imshow(DEBUG_WINDOW, cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
    cv2.waitKey(1)


# =========================
# NAV DECISION
# =========================
def compute_navigation_target(img, fog, cx, cy, force_replan=False):
    global LAST_PATH, LAST_REPLAN

    obstacle = detect_wall_obstacles(img, fog)
    reachable = flood_reachable_from_player(obstacle, cx, cy)
    clearance = cv2.distanceTransform((reachable > 0).astype(np.uint8), cv2.DIST_L2, 5)

    goal = choose_reachable_goal(fog, reachable, clearance, cx, cy)
    waypoint = None

    now = time.time()
    should_replan = force_replan or not LAST_PATH or now - LAST_REPLAN >= REPLAN_EVERY_SECONDS

    if goal and should_replan:
        LAST_PATH = astar_path(reachable, clearance, (cx, cy), goal)
        LAST_REPLAN = now

    if LAST_PATH:
        waypoint = waypoint_from_path(LAST_PATH, cx, cy)

    if waypoint is None:
        waypoint = fallback_safe_ray_target(obstacle, clearance, fog, cx, cy, reachable)

    draw_debug(img, obstacle, reachable, LAST_PATH, goal, waypoint, (cx, cy))
    return waypoint, goal, bool(LAST_PATH)


def unstuck_target(img, fog, cx, cy):
    """
    When stuck, do not hammer random opposite compass directions.
    Recompute and exaggerate the safest legal direction from current local geometry.
    """
    obstacle = detect_wall_obstacles(img, fog)
    reachable = flood_reachable_from_player(obstacle, cx, cy)
    clearance = cv2.distanceTransform((reachable > 0).astype(np.uint8), cv2.DIST_L2, 5)

    # Temporarily prefer maximum clearance around the player, not fog progress.
    h, w = obstacle.shape
    best = None
    best_score = -float("inf")

    for i in range(RAY_COUNT):
        angle = -math.pi + (2 * math.pi * i / RAY_COUNT)
        tx = int(round(cx + math.cos(angle) * RAY_MINI_STEP))
        ty = int(round(cy + math.sin(angle) * RAY_MINI_STEP))

        if not (0 <= tx < w and 0 <= ty < h):
            continue
        if obstacle[ty, tx] > 0 or reachable[ty, tx] == 0:
            continue
        if not line_clear(obstacle, cx, cy, tx, ty):
            continue

        score = float(clearance[ty, tx])
        if score > best_score:
            best_score = score
            best = (tx, ty)

    return best


# =========================
# MAIN LOOP
# =========================
@requires_game_ready()
def main():
    global LOCKED_GOAL, LAST_PATH, PRIMARY_FOG_DIR, SECONDARY_FOG_DIR

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
                LOCKED_GOAL = None
                LAST_PATH = []
                PRIMARY_FOG_DIR = None
                SECONDARY_FOG_DIR = None

                coords = locate_center(STAIRS, confidence=0.8)
                if coords:
                    # Navigation is done; release before intentional UI/interact clicks.
                    release_mouse_if_held()
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

            if stuck_ticks >= 1:
                target = unstuck_target(img, fog, cx, cy)
                step = UNSTICK_CLICK_STEP
                mode = "unstuck"
                # Force a clean replan after the bump.
                LAST_PATH = []
            else:
                target, goal, has_path = compute_navigation_target(img, fog, cx, cy)
                step = CLICK_STEP
                mode = "astar" if has_path else "ray"

            if target is None:
                print(f"player=({cx},{cy}) target=none stuck={stuck} mode=none")
                time.sleep(CHECK_DELAY)
                continue

            tx, ty = target
            clicked = click_toward_point(cx, cy, tx, ty, step=step)
            direction = direction_from_points(cx, cy, tx, ty)

            if clicked is None:
                time.sleep(CHECK_DELAY)
                continue

            mx, my = clicked
            print(
                f"player=({cx},{cy}) target=({tx},{ty}) direction={direction} "
                f"primary={PRIMARY_FOG_DIR} secondary={SECONDARY_FOG_DIR} "
                f"ladder={build_priority_ladder() if (PRIMARY_FOG_DIR or SECONDARY_FOG_DIR) else []} "
                f"clicked=({mx},{my}) stuck={stuck} stuck_ticks={stuck_ticks} mode={mode}"
            )

            time.sleep(CHECK_DELAY)

    finally:
        release_mouse_if_held()

if __name__ == "__main__":
    main()
