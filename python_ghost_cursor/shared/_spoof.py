import math
import random
import numpy as np
from typing import Union, Optional, Dict, List
from python_ghost_cursor.shared._math import (
    Vector,
    magnitude,
    direction,
    bezierCurve,
)


def fitts(distance: float, width: float) -> float:
    a = 0
    b = 2
    id_ = math.log2(distance / width + 1)
    return a + b * id_


def path(
    start: Vector, end: Union[Dict, Vector], spreadOverride: Optional[float] = None
) -> List[Vector]:
    defaultWidth = 100
    minSteps = 25
    if isinstance(end, dict):
        width = end["width"]
        end = Vector(end["x"], end["y"])
    else:
        width = defaultWidth
    curve = bezierCurve(start, end, spreadOverride)
    length = curve.length * 0.8
    baseTime = random.random() * minSteps
    steps = math.ceil((math.log2(fitts(length, width) + 1) + baseTime) * 3)
    s_vals = np.linspace(0.0, 1.0, steps)
    points = curve.evaluate_multi(s_vals)
    vectors = []
    for i in range(steps):
        vectors.append(Vector(points[0][i], points[1][i]))
    return clampPositive(vectors)


def clampPositive(vectors: List[Vector]) -> List[Vector]:
    clamp0 = lambda elem: max(0, elem)
    return [Vector(clamp0(el.x), clamp0(el.y)) for el in vectors]


overshootThreshold = 500


def should_overshoot(a: Vector, b: Vector) -> bool:
    return magnitude(direction(a, b)) > overshootThreshold


def get_path(start: Dict, end: Dict) -> List[Dict]:
    vectors = path(Vector(**start), Vector(**end))
    return [el.__dict__ for el in vectors]


def get_random_box_point(
    box: Dict, padding_percentage: Optional[float] = None
) -> Vector:
    """Get a random point on a box"""
    paddingWidth = paddingHeight = 0
    if (
        padding_percentage is not None
        and padding_percentage > 0
        and padding_percentage < 100
    ):
        paddingWidth = box["width"] * padding_percentage / 100
        paddingHeight = box["height"] * padding_percentage / 100
    return Vector(
        box["x"] + (paddingWidth / 2) + random.random() * (box["width"] - paddingWidth),
        box["y"]
        + (paddingHeight / 2)
        + random.random() * (box["height"] - paddingHeight),
    )
