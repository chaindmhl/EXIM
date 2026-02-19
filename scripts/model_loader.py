import cv2
import os
from django.conf import settings

MODEL_DIR = os.path.join(settings.BASE_DIR, "models")

_net_original = None
_classes_original = None
_net_cropped = None
_classes_cropped = None


def get_original_model():
    global _net_original, _classes_original

    if _net_original is None:
        cfg = os.path.join(MODEL_DIR, "model1", "model1.cfg")
        weights = os.path.join(MODEL_DIR, "model1", "model1.weights")
        names = os.path.join(MODEL_DIR, "model1", "model1.names")

        _net_original = cv2.dnn.readNet(weights, cfg)

        with open(names) as f:
            _classes_original = [line.strip() for line in f]

    return _net_original, _classes_original


def get_cropped_model():
    global _net_cropped, _classes_cropped

    if _net_cropped is None:
        cfg = os.path.join(MODEL_DIR, "model2", "model2.cfg")
        weights = os.path.join(MODEL_DIR, "model2", "model2.weights")
        names = os.path.join(MODEL_DIR, "model2", "model2.names")

        _net_cropped = cv2.dnn.readNet(weights, cfg)

        with open(names) as f:
            _classes_cropped = [line.strip() for line in f]

    return _net_cropped, _classes_cropped
