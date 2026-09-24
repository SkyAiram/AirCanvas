import math


def distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.hypot(
        x2 - x1,
        y2 - y1
    )


def finger_up(landmarks, tip, pip):
    """
    Detecta si un dedo está levantado.

    Para índice, medio, anular y meñique.
    """

    if len(landmarks) < 21:
        return False

    return landmarks[tip][1] < landmarks[pip][1]


def get_fingers(landmarks):

    if len(landmarks) < 21:
        return {
            "index": False,
            "middle": False,
            "ring": False,
            "pinky": False
        }

    return {
        "index": finger_up(
            landmarks,
            8,
            6
        ),

        "middle": finger_up(
            landmarks,
            12,
            10
        ),

        "ring": finger_up(
            landmarks,
            16,
            14
        ),

        "pinky": finger_up(
            landmarks,
            20,
            18
        )
    }


def detect_pinch(
    landmarks,
    threshold=40
):

    if len(landmarks) < 21:
        return False

    thumb = landmarks[4]
    index = landmarks[8]

    pinch_distance = distance(
        thumb,
        index
    )

    return pinch_distance < threshold


def detect_gesture(landmarks):

    if len(landmarks) < 21:
        return "NONE"

    fingers = get_fingers(
        landmarks
    )

    # ========================
    # PINZA
    # ========================

    if detect_pinch(landmarks):
        return "DRAW"

    # ========================
    # DOS DEDOS
    # ========================

    if (
        fingers["index"]
        and fingers["middle"]
        and not fingers["ring"]
        and not fingers["pinky"]
    ):
        return "SELECT"

    # ========================
    # SOLO ÍNDICE
    # ========================

    if (
        fingers["index"]
        and not fingers["middle"]
        and not fingers["ring"]
        and not fingers["pinky"]
    ):
        return "MOVE"

    # ========================
    # MANO ABIERTA
    # ========================

    if (
        fingers["index"]
        and fingers["middle"]
        and fingers["ring"]
        and fingers["pinky"]
    ):
        return "ERASE"

    return "NONE"