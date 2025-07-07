import argparse
import os
from datetime import datetime
from pathlib import Path

import torch
import torch.utils.data
import torchvision
from tqdm import tqdm
from torchvision.datasets import CocoDetection
import torchvision.transforms as T
from torch.utils.data import DataLoader

from object_detection.utils import (
    CocoDetectionDataset,
    collate_fn,
    get_model,
    get_transform,
    save_model,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Train Faster R-CNN on COCO with PyTorch")
    parser.add_argument("--dataset-root", type=str, required=True, help="Path to COCO root directory (e.g., /data/coco)")
    parser.add_argument(
        "--year",
        type=str,
        default="2017",
        choices=["2017", "2014"],
        help="COCO dataset year sub-folder (default: 2017)",
    )
    parser.add_argument(
        "--epochs", type=int, default=10, help="Number of training epochs (default: 10)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=2, help="Batch size for DataLoader (default: 2)"
    )
    parser.add_argument(
        "--lr", type=float, default=0.005, help="Initial learning rate (default: 0.005)"
    )
    parser.add_argument(
        "--num-workers", type=int, default=4, help="DataLoader workers (default: 4)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="training_output",
        help="Directory to save models and logs",
    )
    return parser.parse_args()


def create_dataloaders(root: str, year: str, batch_size: int, num_workers: int):
    train_images = os.path.join(root, f"train{year}")
    val_images = os.path.join(root, f"val{year}")
    train_ann = os.path.join(root, "annotations", f"instances_train{year}.json")
    val_ann = os.path.join(root, "annotations", f"instances_val{year}.json")

    train_dataset = CocoDetection(
        root / f"train{year}",
        root / "annotations" / f"instances_train{year}.json",
        transform=get_transform(train=True),
    )
    val_dataset = CocoDetection(
        root / f"val{year}",
        root / "annotations" / f"instances_val{year}.json",
        transform=get_transform(train=False),
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        collate_fn=collate_fn,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=1,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=collate_fn,
    )
    return train_loader, val_loader


def coco_to_frcnn(targets):
    new_targets = []
    for anns in targets:
        boxes   = torch.as_tensor([ [x, y, x+w, y+h] for x, y, w, h in
                                    (ann['bbox'] for ann in anns) ], dtype=torch.float32)
        labels  = torch.as_tensor([ann['category_id'] for ann in anns], dtype=torch.int64)
        areas   = torch.as_tensor([ann['area'] for ann in anns], dtype=torch.float32)
        iscrowd = torch.as_tensor([ann.get('iscrowd', 0) for ann in anns], dtype=torch.int64)
        new_targets.append({
            "boxes": boxes,
            "labels": labels,
            "area": areas,
            "iscrowd": iscrowd,
        })
    return new_targets


def train_one_epoch(model, optimizer, data_loader, device, epoch):
    model.train()
    lr_scheduler = None
    # Warm-up LR scheduler
    if epoch == 0:
        warmup_factor = 1.0 / 1000
        warmup_iters = min(1000, len(data_loader) - 1)

        lr_scheduler = torch.optim.lr_scheduler.LinearLR(
            optimizer, start_factor=warmup_factor, total_iters=warmup_iters
        )

    running_loss = 0.0
    pbar = tqdm(data_loader, desc=f"Train Epoch {epoch}")
    for images, raw_targets in pbar:
        images = [img.to(device) for img in images]
        targets = coco_to_frcnn(raw_targets)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())

        optimizer.zero_grad()
        losses.backward()
        optimizer.step()

        if lr_scheduler is not None:
            lr_scheduler.step()

        running_loss += losses.item()
        pbar.set_postfix({"loss": losses.item()})

    return running_loss / len(data_loader)


def evaluate(model, data_loader, device):
    model.eval()
    running_loss = 0.0
    with torch.no_grad():
        for images, targets in tqdm(data_loader, desc="Validation"):
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())
            running_loss += losses.item()
    return running_loss / len(data_loader)


def main():
    args = parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    num_classes = 91  # COCO has 80 classes + background (technically 91 in ids)
    model = get_model(num_classes=num_classes)
    model.to(device)

    train_loader, val_loader = create_dataloaders(
        args.dataset_root, args.year, args.batch_size, args.num_workers
    )

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=args.lr, momentum=0.9, weight_decay=0.0005)
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

    # Create output directory
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        train_loss = train_one_epoch(model, optimizer, train_loader, device, epoch)
        val_loss = evaluate(model, val_loader, device)
        lr_scheduler.step()

        print(
            f"Epoch {epoch}: Train Loss {train_loss:.4f}, Val Loss {val_loss:.4f}, LR {lr_scheduler.get_last_lr()[0]:.6f}"
        )

        # Save checkpoint
        ckpt_path = out_dir / f"model_{epoch:03d}.pth"
        save_model(model, str(ckpt_path))
        print(f"Saved checkpoint to {ckpt_path}")

    # Save final model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = out_dir / f"model_final_{timestamp}.pth"
    save_model(model, str(final_path))
    print(f"Training complete. Final model saved to {final_path}")


if __name__ == "__main__":
    main() 