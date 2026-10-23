# ML Model Details — RJ 147

## Project
**RJ 147 — Smart Waste Segregation and Sanitation System**

## Model Overview

| Property | Value |
|---|---|
| Architecture | MobileNetV2 (Transfer Learning) |
| Framework | PyTorch |
| Model File | `ml/model/waste_model.pth` |
| Metadata File | `ml/metadata/model_metadata.json` |
| File Size | ~9.8 MB |
| Number of Classes | 12 |
| Input Size | 224 × 224 pixels |
| Color Space | RGB |

## Class Names (Label Mapping)

| Index | Class Name | Waste Category |
|---|---|---|
| 0 | battery | Hazardous |
| 1 | biological | Organic / Wet Waste |
| 2 | brown-glass | Recyclable / Dry Waste |
| 3 | cardboard | Recyclable / Dry Waste |
| 4 | clothes | Recyclable / Dry Waste |
| 5 | green-glass | Recyclable / Dry Waste |
| 6 | metal | Recyclable / Dry Waste |
| 7 | paper | Recyclable / Dry Waste |
| 8 | plastic | Recyclable / Dry Waste |
| 9 | shoes | Recyclable / Dry Waste |
| 10 | trash | Non-Recyclable |
| 11 | white-glass | Recyclable / Dry Waste |

## Preprocessing Pipeline

The model requires the following preprocessing (ImageNet normalization):

1. **Resize** the input image to 224 × 224 pixels
2. **Convert** to RGB if not already
3. **Convert** to tensor (values 0–1)
4. **Normalize** with ImageNet statistics:
   - Mean: `[0.485, 0.456, 0.406]`
   - Std: `[0.229, 0.224, 0.225]`

```python
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])
```

## Model Architecture

MobileNetV2 pretrained on ImageNet with the classifier head replaced for 12-class waste classification.

The model state dict is saved as a PyTorch `.pth` file. Loading requires:

```python
import torch
from torchvision import models

model = models.mobilenet_v2(weights=None)
model.classifier = torch.nn.Sequential(
    torch.nn.Dropout(p=0.2),
    torch.nn.Linear(1280, 128),
    torch.nn.ReLU(),
    torch.nn.Dropout(p=0.2),
    torch.nn.Linear(128, 12)
)
model.load_state_dict(torch.load("ml/model/waste_model.pth", map_location="cpu"))
model.eval()
```

## Inference

```python
from PIL import Image
import torch

image = Image.open("test_image.jpg").convert("RGB")
input_tensor = transform(image).unsqueeze(0)

with torch.no_grad():
    outputs = model(input_tensor)
    probabilities = torch.nn.functional.softmax(outputs, dim=1)
    confidence, predicted_idx = torch.max(probabilities, 1)

predicted_class = class_names[predicted_idx.item()]
confidence_pct = confidence.item() * 100
```

## Test Results

### Internal Test Set
| Metric | Value |
|---|---|
| Total Images | 1,552 |
| Accuracy | 95.75% |
| Precision | 95.77% |
| Recall | 95.75% |
| F1 Score | 95.73% |

### External Test Set
| Metric | Value |
|---|---|
| Total Images | 24 |
| Correct Predictions | 22 |
| Incorrect Predictions | 2 |
| Accuracy | 91.67% |

## Confusion Matrix

The confusion matrix is stored at `ml/metadata/RJ147_confusion_matrix.png`.

## Source

The model was trained in Google Colab and exported as part of the `RJ147_Antigravity_Package` ZIP file. The original ZIP is preserved in the workspace root.

## Important Notes

- Do NOT retrain this model
- Do NOT modify the model weights
- Do NOT replace this model with a different model
- The original Colab ZIP file must be preserved
- All inference must use this exact model with the exact preprocessing described above
