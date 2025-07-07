import os
from typing import Tuple, List, Dict

import torch
from torch.utils.data import Dataset
from PIL import Image
from pycocotools.coco import COCO
import torchvision.transforms as T
import torchvision


def get_transform(train: bool = True):
    """Returns the transformation pipeline for images.

    Args:
        train (bool): If True, applies training augmentations.

    Returns:
        torchvision.transforms.Compose: Transformation pipeline.
    """
    transforms: List[torchvision.transforms.Compose] = []
    # Convert PIL image to Tensor and normalize to [0, 1]
    transforms.append(T.ToTensor())

    if train:
        # Add data augmentations if needed, e.g., random horizontal flip
        transforms.append(T.RandomHorizontalFlip(0.5))

    return T.Compose(transforms)


class CocoDetectionDataset(Dataset):
    """COCO dataset wrapper that returns data in torchvision detection format."""

    def __init__(self, images_dir: str, annotation_file: str, transforms=None):
        self.root = images_dir
        self.coco = COCO(annotation_file)
        self.ids: List[int] = list(sorted(self.coco.imgs.keys()))
        self.transforms = transforms if transforms is not None else get_transform(train=False)

    def __getitem__(self, index: int):
        coco = self.coco
        img_id = self.ids[index]
        ann_ids = coco.getAnnIds(imgIds=img_id)
        annotations = coco.loadAnns(ann_ids)

        img_info = coco.loadImgs(img_id)[0]
        img_path = os.path.join(self.root, img_info["file_name"])
        img = Image.open(img_path).convert("RGB")

        boxes = []
        labels = []
        areas = []
        iscrowd = []

        for obj in annotations:
            # COCO format is [x, y, width, height]
            x, y, w, h = obj["bbox"]
            boxes.append([x, y, x + w, y + h])
            labels.append(obj["category_id"])
            areas.append(obj["area"])
            iscrowd.append(obj.get("iscrowd", 0))

        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        areas = torch.as_tensor(areas, dtype=torch.float32)
        iscrowd = torch.as_tensor(iscrowd, dtype=torch.int64)

        target: Dict[str, torch.Tensor] = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([img_id]),
            "area": areas,
            "iscrowd": iscrowd,
        }

        if self.transforms is not None:
            img = self.transforms(img)

        return img, target

    def __len__(self) -> int:
        return len(self.ids)


def collate_fn(batch: List[Tuple[torch.Tensor, Dict[str, torch.Tensor]]]):
    """Custom collate function needed for batching variable-sized targets."""
    images, targets = list(zip(*batch))
    return list(images), list(targets)


def get_model(num_classes: int):
    """Returns a Faster R-CNN model pre-trained on COCO with a custom head."""
    # Load a model pre-trained on COCO
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights="DEFAULT")

    # Replace the classifier with a new one, that has num_classes which is user-defined
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(
        in_features, num_classes
    )
    return model


def save_model(model: torch.nn.Module, path: str):
    torch.save(model.state_dict(), path)


def load_model(model: torch.nn.Module, path: str, device: torch.device):
    model.load_state_dict(torch.load(path, map_location=device))
    model.to(device)
    model.eval()
    return model 