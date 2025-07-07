import argparse
import os
from pathlib import Path
from typing import List

import torch
from PIL import Image, ImageDraw, ImageFont
from torchvision.transforms import functional as F

from object_detection.utils import get_model, load_model


COCO_INSTANCE_CATEGORY_NAMES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag',
    'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite',
    'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana',
    'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table',
    'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
    'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]


def parse_args():
    parser = argparse.ArgumentParser(description="Run inference on images using a trained object detector")
    parser.add_argument("--model-path", type=str, required=True, help="Path to trained .pth model file")
    parser.add_argument("--images", type=str, nargs="+", required=True, help="Image files or directory to process")
    parser.add_argument("--score-threshold", type=float, default=0.5, help="Confidence threshold for predictions")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="inference_output",
        help="Directory to write annotated images",
    )
    return parser.parse_args()


def load_images(paths: List[str]):
    image_files: List[str] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            image_files.extend([str(fp) for fp in path.glob("*.jpg")])
            image_files.extend([str(fp) for fp in path.glob("*.png")])
        elif path.is_file():
            image_files.append(str(path))
    return image_files


def draw_predictions(img: Image.Image, boxes, labels, scores, threshold: float):
    draw = ImageDraw.Draw(img)
    font = None
    try:
        font = ImageFont.load_default()
    except Exception:
        pass
    for box, label, score in zip(boxes, labels, scores):
        if score < threshold:
            continue
        x1, y1, x2, y2 = box
        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2)
        text = f"{COCO_INSTANCE_CATEGORY_NAMES[label]}: {score:.2f}"
        text_size = draw.textbbox((0, 0), text, font=font)
        draw.rectangle([(x1, y1 - (text_size[3] - text_size[1]) - 4), (x1 + (text_size[2] - text_size[0]), y1)], fill="red")
        draw.text((x1, y1 - (text_size[3] - text_size[1]) - 2), text, fill="white", font=font)


def main():
    args = parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running inference on {device}")

    # Initialize model with correct number of classes and load weights
    num_classes = 91  # matching training
    model = get_model(num_classes)
    load_model(model, args.model_path, device)

    image_paths = load_images(args.images)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_path in image_paths:
        img = Image.open(img_path).convert("RGB")
        img_tensor = F.to_tensor(img).to(device)

        with torch.no_grad():
            preds = model([img_tensor])[0]

        boxes = preds["boxes"].cpu().numpy()
        labels = preds["labels"].cpu().numpy()
        scores = preds["scores"].cpu().numpy()

        draw_predictions(img, boxes, labels, scores, args.score_threshold)

        save_path = output_dir / Path(img_path).name
        img.save(save_path)
        print(f"Saved result to {save_path}")


if __name__ == "__main__":
    main() 