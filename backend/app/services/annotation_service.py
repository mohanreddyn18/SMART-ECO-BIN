"""
SMART ECO BIN — Visual Annotation & Coordinate Scaling Service
==============================================================
Provides overlay drawing, coordinate conversion, and visual encoding
for multi-object waste detections.
"""

import io
import base64
import logging
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from app.models.schemas import ObjectDetectionItem, BoundingBox

logger = logging.getLogger("ecosort.annotation")

# Category color palette matching municipal standards
CATEGORY_COLORS = {
    "wet": "#10b981",          # Emerald Green
    "dry": "#2563eb",          # Royal Blue
    "hazardous": "#ef4444",    # Crimson Red
    "manual_review": "#f59e0b" # Amber
}


class AnnotationService:
    """
    Renders visual bounding-box overlays and converts coordinate systems.
    """

    @staticmethod
    def scale_bounding_box(
        bbox: BoundingBox,
        src_dimensions: Tuple[int, int],
        dest_dimensions: Tuple[int, int]
    ) -> BoundingBox:
        """
        Scales bounding-box coordinates from source (src_w, src_h) to destination (dest_w, dest_h).
        """
        src_w, src_h = src_dimensions
        dest_w, dest_h = dest_dimensions

        if src_w <= 0 or src_h <= 0:
            return bbox

        scale_x = dest_w / src_w
        scale_y = dest_h / src_h

        scaled_x1 = bbox.x1 * scale_x
        scaled_y1 = bbox.y1 * scale_y
        scaled_x2 = bbox.x2 * scale_x
        scaled_y2 = bbox.y2 * scale_y

        norm_x1 = scaled_x1 / dest_w if dest_w > 0 else 0.0
        norm_y1 = scaled_y1 / dest_h if dest_h > 0 else 0.0
        norm_x2 = scaled_x2 / dest_w if dest_w > 0 else 0.0
        norm_y2 = scaled_y2 / dest_h if dest_h > 0 else 0.0

        return BoundingBox(
            x1=round(scaled_x1, 1),
            y1=round(scaled_y1, 1),
            x2=round(scaled_x2, 1),
            y2=round(scaled_y2, 1),
            norm_x1=round(norm_x1, 4),
            norm_y1=round(norm_y1, 4),
            norm_x2=round(norm_x2, 4),
            norm_y2=round(norm_y2, 4)
        )

    @staticmethod
    def annotate_image(
        image: Image.Image,
        detections: List[ObjectDetectionItem],
        line_width: int = 3
    ) -> Image.Image:
        """
        Draws high-visibility color-coded bounding boxes and label badges onto a copy of the image.
        """
        annotated = image.copy().convert("RGB")
        draw = ImageDraw.Draw(annotated)

        for det in detections:
            bbox = det.bbox
            cat = det.disposal.category.lower() if det.disposal else "manual_review"
            hex_color = CATEGORY_COLORS.get(cat, "#f59e0b")

            # Draw outer rectangle
            draw.rectangle(
                [(bbox.x1, bbox.y1), (bbox.x2, bbox.y2)],
                outline=hex_color,
                width=line_width
            )

            # Construct label tag
            tag_text = f"{det.label.replace('_', ' ').title()} ({det.confidence:.0%}) [{det.disposal.category.upper()}]"

            # Draw label banner background
            text_bbox = draw.textbbox((bbox.x1, max(0, bbox.y1 - 18)), tag_text)
            draw.rectangle(text_bbox, fill=hex_color)
            # Draw label text
            draw.text((bbox.x1 + 2, max(0, bbox.y1 - 18)), tag_text, fill="white")

        return annotated

    @classmethod
    def generate_annotated_base64(
        cls,
        image_bytes: bytes,
        detections: List[ObjectDetectionItem]
    ) -> Optional[str]:
        """
        Annotates image and encodes result as a JPEG data URL.
        """
        if not image_bytes or not detections:
            return None

        try:
            image = Image.open(io.BytesIO(image_bytes))
            annotated = cls.annotate_image(image, detections)
            buffer = io.BytesIO()
            annotated.save(buffer, format="JPEG", quality=85)
            b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception as e:
            logger.warning(f"Failed to generate annotated image preview: {e}")
            return None


# Global annotation service singleton
annotation_service = AnnotationService()
