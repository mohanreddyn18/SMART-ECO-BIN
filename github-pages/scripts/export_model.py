from pathlib import Path
import sys

import torch
import torch.nn as nn
from torchvision import models


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = ROOT / "ml" / "model" / "waste_model.pth"
OUTPUT = Path(__file__).resolve().parents[1] / "public" / "models" / "waste_classifier.onnx"
CLASS_NAMES = [
    "battery", "biological", "brown-glass", "cardboard", "clothes",
    "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass",
]


def main() -> None:
    if not CHECKPOINT.is_file():
        raise FileNotFoundError(f"Classifier checkpoint not found: {CHECKPOINT}")

    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2),
        nn.Linear(1280, 128),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(128, len(CLASS_NAMES)),
    )
    state_dict = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sample = torch.zeros(1, 3, 224, 224, dtype=torch.float32)
    with torch.inference_mode():
        torch.onnx.export(
            model,
            sample,
            str(OUTPUT),
            input_names=["image"],
            output_names=["logits"],
            opset_version=17,
            do_constant_folding=True,
            dynamo=False,
        )
        reference = model(sample).squeeze(0)

    try:
        import onnx
    except ImportError as error:
        raise RuntimeError("Install the ONNX package to validate the exported graph.") from error

    graph = onnx.load(str(OUTPUT))
    onnx.checker.check_model(graph)
    print(f"Exported ONNX model: {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    print(f"Classes ({len(CLASS_NAMES)}): {', '.join(CLASS_NAMES)}")
    print(f"PyTorch verification logits: {reference.tolist()}")
    if not torch.isfinite(reference).all():
        raise RuntimeError("The classifier produced non-finite logits for the export verification tensor.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Model export failed: {error}", file=sys.stderr)
        raise
