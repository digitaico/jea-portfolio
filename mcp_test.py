#!/usr/bin/env python3
"""
Minimal sanity-check script for OpenCV MCP.

The script will:
1. Generate a simple synthetic image with OpenCV (green rectangle on black).
2. Use the OpenCV MCP client (`from openai import opencv_client`) to call two
   sample tools exposed by the server:
   • `resize_image_tool` – downsizes the test image.
   • `detect_edges_tool` – runs Canny edge detection on the resized image.
3. Print the JSON responses returned by each tool so you can verify that the
   server is reachable and responding correctly.

Run it with:
    python mcp_test.py

Requirements:
    pip install opencv-mcp-server opencv-python openai pillow
Make sure that the OpenCV MCP server is already running (usually `uvx` or
`python -m opencv_mcp_server`).
"""
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from opencv_mcp_server import opencv_client  

# Instantiate the client (assumes the MCP server is available on default host/port)
client = opencv_client.OpenCVClient()


def create_test_image(path: Path) -> None:
    """Create a 256×256 PNG with a solid green rectangle on black background."""
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.rectangle(img, (0, 0), (256, 256), (0, 255, 0), thickness=-1)
    cv2.putText(img, "MCP", (60, 140), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.imwrite(str(path), img)


def pretty_print(response: dict, title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    for k, v in response.items():
        print(f"{k}: {v}")


def main() -> None:
    # Prepare a temporary directory to store intermediate files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_img = tmpdir_path / "test_input.png"

        # 1️⃣ Create a synthetic test image
        create_test_image(test_img)
        print(f"Created test image at {test_img}")

        # 2️⃣ Resize the image via MCP
        resize_resp = client.resize_image_tool(
            image_path=str(test_img), width=128, height=128
        )
        pretty_print(resize_resp, "Response from resize_image_tool")

        resized_path = resize_resp.get("output_path")
        if not resized_path or not os.path.exists(resized_path):
            print("❌ Resize failed or output file not found. Aborting further tests.")
            sys.exit(1)

        # 3️⃣ Detect edges via MCP using the resized image
        edges_resp = client.detect_edges_tool(
            image_path=resized_path, method="canny", threshold1=50, threshold2=150
        )
        pretty_print(edges_resp, "Response from detect_edges_tool")

        edges_path = edges_resp.get("output_path")
        if edges_path and os.path.exists(edges_path):
            print(f"✅ Edge-detected image saved at {edges_path}")
        else:
            print("⚠️  Edge-detected image file not found – check server logs for errors.")

        print("\nAll tests finished.")


if __name__ == "__main__":
    main() 