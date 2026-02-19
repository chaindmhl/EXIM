import cv2
import os
from django.conf import settings

# Paths to the models baked into Docker image
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")

# Load model 1 (original)
net_original = cv2.dnn.readNet(
    os.path.join(MODEL_DIR, "model1", "model1.weights"),
    os.path.join(MODEL_DIR, "model1", "model1.cfg")
)
with open(os.path.join(MODEL_DIR, "model1", "model1.names")) as f:
    classes_original = [line.strip() for line in f]

# Load model 2 (cropped)
net_cropped = cv2.dnn.readNet(
    os.path.join(MODEL_DIR, "model2", "model2.weights"),
    os.path.join(MODEL_DIR, "model2", "model2.cfg")
)
with open(os.path.join(MODEL_DIR, "model2", "model2.names")) as f:
    classes_cropped = [line.strip() for line in f]
