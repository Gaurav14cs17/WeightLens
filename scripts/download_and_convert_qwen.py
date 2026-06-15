#!/usr/bin/env python3
"""Download Qwen2.5-0.5B and convert to ONNX format for WeightLens testing."""

import os
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "src" / "test_models" / "qwen2.5-0.5b"
MODEL_ID = "Qwen/Qwen2.5-0.5B"

def main():
    print(f"[1/2] Downloading & converting {MODEL_ID} to ONNX...")
    print(f"      Output directory: {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    from optimum.exporters.onnx import main_export

    main_export(
        model_name_or_path=MODEL_ID,
        output=str(OUTPUT_DIR),
        task="text-generation",
        trust_remote_code=True,
    )

    print(f"\n[2/2] Listing output files...")
    for f in sorted(OUTPUT_DIR.iterdir()):
        if f.is_file():
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.name:40s} {size_mb:8.1f} MB")

    print(f"\n Done! ONNX model saved to: {OUTPUT_DIR}")
    print(f"  Open the .onnx file in WeightLens Architecture Viewer.")

if __name__ == "__main__":
    main()
