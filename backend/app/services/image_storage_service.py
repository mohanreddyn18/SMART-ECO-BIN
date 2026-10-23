import os
import logging
from typing import Optional, Tuple
from datetime import timedelta

logger = logging.getLogger("ecosort.image_storage")


class GoogleCloudImageStorageService:
    """
    Architectural abstraction for optional, private Google Cloud Storage (GCS)
    image archival.
    
    Security & Privacy Principles:
    - Default Posture: DISABLED (`GCS_IMAGE_STORAGE_ENABLED=false`).
      Classification images are evaluated in-memory and immediately discarded,
      strictly adhering to citizen data privacy and zero-retention standards.
    - If enabled by enterprise policy:
      - Private, backend-only uploads to a dedicated private bucket.
      - Never allows public read access (`allUsers` permissions strictly forbidden).
      - Strict content type and size validation (max 10MB, JPEG/PNG/WEBP).
      - Access via short-lived V4 signed URLs (default: 15-minute validity).
    """

    ALLOWED_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(self, bucket_name: Optional[str] = None, client=None):
        self.enabled = os.getenv("GCS_IMAGE_STORAGE_ENABLED", "false").lower() == "true"
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "smart-eco-bin-audit-images")
        self._client = client

    @property
    def client(self):
        if self._client is None and self.enabled:
            try:
                from google.cloud import storage
                self._client = storage.Client()
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
                self._client = None
        return self._client

    def validate_image_payload(self, image_bytes: bytes, content_type: str) -> Tuple[bool, Optional[str]]:
        """Strictly validates binary size and MIME type before any storage operation."""
        if not image_bytes or len(image_bytes) == 0:
            return False, "Image payload is empty."

        if len(image_bytes) > self.MAX_FILE_SIZE_BYTES:
            return False, f"Image payload exceeds maximum limit of {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."

        if content_type.lower() not in self.ALLOWED_MIME_TYPES:
            return False, f"Unsupported MIME type '{content_type}'. Allowed types: {', '.join(self.ALLOWED_MIME_TYPES)}."

        return True, None

    def upload_audit_image(
        self,
        record_id: str,
        image_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Uploads image binary to private GCS object if enabled.
        Returns the GCS object URI (e.g. gs://bucket/path) or None if disabled.
        """
        if not self.enabled:
            logger.debug("Image storage is disabled (zero-retention privacy posture active). Skipping upload.")
            return None

        is_valid, err = self.validate_image_payload(image_bytes, content_type)
        if not is_valid:
            logger.error(f"Image validation rejected for record '{record_id}': {err}")
            raise ValueError(f"Image validation failed: {err}")

        if not self.client:
            logger.error("GCS client unavailable. Cannot upload image.")
            raise RuntimeError("Google Cloud Storage client not configured.")

        try:
            ext = "jpg" if "jpeg" in content_type.lower() else content_type.split("/")[-1].lower()
            object_name = f"audit_events/{record_id[:8]}/{record_id}.{ext}"
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(object_name)

            blob.upload_from_string(image_bytes, content_type=content_type)
            logger.info(f"Audit image securely archived for record '{record_id}' at gs://{self.bucket_name}/{object_name}.")
            return f"gs://{self.bucket_name}/{object_name}"
        except Exception as e:
            logger.error(f"Failed to upload image for record '{record_id}' to GCS: {e}")
            raise RuntimeError(f"GCS image upload failed: {e}") from e

    def generate_signed_access_url(
        self,
        gcs_uri: str,
        expiration_minutes: int = 15
    ) -> Optional[str]:
        """
        Generates a short-lived V4 signed URL for authorized viewing.
        Never grants public bucket access.
        """
        if not self.enabled or not gcs_uri or not gcs_uri.startswith("gs://"):
            return None

        if not self.client:
            return None

        try:
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            bucket_name, blob_name = parts[0], parts[1]
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
            return url
        except Exception as e:
            logger.warning(f"Could not generate signed URL for '{gcs_uri}': {e}")
            return None


image_storage_service = GoogleCloudImageStorageService()
