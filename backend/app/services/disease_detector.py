"""Baseline leaf-health detector.

This is a colour-analysis heuristic (HSV thresholding), NOT a trained CNN/YOLO model.
It exists so the /api/disease/detect endpoint is genuinely functional today, without
requiring a labeled disease-image dataset (e.g. PlantVillage) or GPU training time.

It flags the fraction of leaf-surface pixels that fall in "unhealthy" colour bands
(yellow/brown/necrotic-dark) versus healthy green, and reports that as a severity score.

To upgrade: swap `analyze()`'s body for a real inference call (YOLOv8 / EfficientNet /
ResNet trained on PlantVillage or your own labeled data) — the FastAPI route and response
schema do not need to change.
"""
import io

import cv2
import numpy as np
from PIL import Image

# HSV ranges (OpenCV: H 0-179, S/V 0-255)
HEALTHY_GREEN = ((30, 40, 40), (90, 255, 255))
DISEASED_YELLOW_BROWN = ((10, 40, 40), (30, 255, 255))
DISEASED_DARK_NECROTIC = ((0, 0, 0), (180, 255, 60))


def _mask_fraction(hsv, lower, upper, leaf_mask):
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    mask = cv2.bitwise_and(mask, mask, mask=leaf_mask)
    leaf_pixels = int(np.count_nonzero(leaf_mask))
    if leaf_pixels == 0:
        return 0.0
    return float(np.count_nonzero(mask)) / leaf_pixels


def analyze(image_bytes: bytes) -> dict:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((512, 512))
    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Leaf mask = anything not near-white background, so background doesn't skew ratios.
    non_bg = cv2.inRange(hsv, np.array((0, 25, 25)), np.array((180, 255, 255)))
    leaf_pixels = int(np.count_nonzero(non_bg))
    if leaf_pixels < 500:
        return {
            "status": "unknown",
            "severity_percent": 0.0,
            "confidence": 0.0,
            "message": "Could not isolate a leaf in the image. Try a closer, well-lit photo.",
            "method": "opencv-hsv-heuristic-v1",
        }

    green_frac = _mask_fraction(hsv, *HEALTHY_GREEN, non_bg)
    yellow_brown_frac = _mask_fraction(hsv, *DISEASED_YELLOW_BROWN, non_bg)
    dark_frac = _mask_fraction(hsv, *DISEASED_DARK_NECROTIC, non_bg)

    severity = min(1.0, yellow_brown_frac + dark_frac) * 100
    confidence = min(0.95, 0.5 + green_frac * 0.4)

    if severity < 8:
        status = "healthy"
        message = "Leaf appears healthy — no significant discoloration or lesions detected."
    elif severity < 25:
        status = "early_stage_concern"
        message = "Minor discoloration detected. Monitor the plant over the next few days."
    else:
        status = "diseased"
        message = (
            "Significant discoloration/necrotic area detected — consistent with disease "
            "or nutrient stress. Recommend agronomist follow-up."
        )

    return {
        "status": status,
        "severity_percent": round(severity, 2),
        "confidence": round(confidence, 2),
        "message": message,
        "method": "opencv-hsv-heuristic-v1",
    }
