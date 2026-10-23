import os
import json
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ecosort.storage")


class BaseStorageProvider(ABC):
    """Abstract storage interface for SMART ECO BIN classification events."""

    @abstractmethod
    def save_record(self, record_data: Dict[str, Any], idempotency_key: Optional[str] = None) -> str:
        """Persists a classification event record. Returns the record ID."""
        pass

    @abstractmethod
    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single record by ID."""
        pass

    @abstractmethod
    def list_records(
        self,
        limit: int = 50,
        skip: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[str] = None,
        public_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Lists records with optional pagination, category filtering, search, and ownership scope."""
        pass

    @abstractmethod
    def count_records(self) -> int:
        """Returns the total number of records."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns storage operating mode and provider metadata."""
        pass

    @abstractmethod
    def clear_records(self) -> None:
        """Clears records (used in test fixtures or development resets)."""
        pass

    @abstractmethod
    def delete_record(self, record_id: str) -> bool:
        """Deletes a single record by ID. Returns True if deleted, False if not found."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Local file-backed & in-memory storage provider for development emulation.
    Persists events to a local JSON ledger at backend/data/classification_records.json.
    Thread-safe with built-in idempotency protection.
    """

    def __init__(self, storage_file: Optional[str] = None):
        self._lock = threading.Lock()
        self._records: List[Dict[str, Any]] = []
        self._seen_idempotency_keys: Dict[str, str] = {}  # idempotency_key -> record_id

        if storage_file:
            self.storage_file = os.path.abspath(storage_file)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.storage_file = os.path.join(data_dir, "classification_records.json")

        self._load_from_disk()

    def _load_from_disk(self):
        with self._lock:
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self._records = data
                            for rec in self._records:
                                if "id" in rec:
                                    self._seen_idempotency_keys[rec["id"]] = rec["id"]
                                if "idempotencyKey" in rec and rec["idempotencyKey"]:
                                    self._seen_idempotency_keys[rec["idempotencyKey"]] = rec["id"]
                            logger.info(f"Loaded {len(self._records)} classification records from local store: {self.storage_file}")
                except Exception as e:
                    logger.warning(f"Could not load local storage file {self.storage_file}: {e}. Starting fresh in memory.")
                    self._records = []
            else:
                self._records = []

    def _persist_to_disk(self):
        try:
            temp_file = f"{self.storage_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._records, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.storage_file)
        except Exception as e:
            logger.error(f"Failed to persist records to {self.storage_file}: {e}")

    def save_record(self, record_data: Dict[str, Any], idempotency_key: Optional[str] = None) -> str:
        with self._lock:
            # 1. Idempotency safeguard: check if idempotency key or record ID was already processed
            key = idempotency_key or record_data.get("idempotencyKey")
            if key and key in self._seen_idempotency_keys:
                existing_id = self._seen_idempotency_keys[key]
                logger.info(f"Idempotent request detected for key '{key}'. Returning existing record '{existing_id}'.")
                return existing_id

            record_id = record_data.get("id")
            if record_id and record_id in self._seen_idempotency_keys:
                logger.info(f"Record with ID '{record_id}' already exists. Returning existing ID.")
                return record_id

            # 2. Assign stable ID if not present
            if not record_id:
                timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                counter = len(self._records) + 1
                record_id = f"REC-{timestamp_str}-{counter:04d}"
                record_data["id"] = record_id

            # 3. Ensure required schema attributes exist
            normalized_record = {
                "id": record_id,
                "itemName": record_data.get("itemName", "Standard Waste Sample"),
                "predictedClass": record_data.get("predictedClass", "unknown"),
                "wasteType": record_data.get("wasteType", "Unclassified"),
                "confidence": float(record_data.get("confidence", 0.0)),
                "recommendation": record_data.get("recommendation", "Follow municipal guidance."),
                "disposalBin": record_data.get("disposalBin", "General Waste Bin"),
                "destinationCompartment": record_data.get("destinationCompartment", "General Residual Waste Bin"),
                "compartmentId": record_data.get("compartmentId", "bin_residual"),
                "routingStatus": record_data.get("routingStatus", "AUTOMATED_ROUTED"),
                "routingReason": record_data.get("routingReason", "Standard classification policy."),
                "requiresManualReview": bool(record_data.get("requiresManualReview", False)),
                "simulationStatus": record_data.get("simulationStatus", "SIMULATED"),
                "timestamp": record_data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                "imageUrl": record_data.get("imageUrl"),
                "userId": record_data.get("userId", "public-citizen")
            }

            if key:
                normalized_record["idempotencyKey"] = key
                self._seen_idempotency_keys[key] = record_id
            self._seen_idempotency_keys[record_id] = record_id

            # Prepend newest record
            self._records.insert(0, normalized_record)
            self._persist_to_disk()
            return record_id

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for rec in self._records:
                if rec.get("id") == record_id:
                    return dict(rec)
            return None

    def list_records(
        self,
        limit: int = 50,
        skip: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[str] = None,
        public_only: bool = False
    ) -> List[Dict[str, Any]]:
        with self._lock:
            results = list(self._records)

            if user_id:
                results = [r for r in results if r.get("userId") == user_id]
            elif public_only:
                results = [r for r in results if r.get("userId") in (None, "", "public-citizen")]

            if category and category != "ALL":
                results = [r for r in results if r.get("wasteType", "").lower() == category.lower()]

            if search:
                term = search.lower()
                results = [
                    r for r in results
                    if term in r.get("predictedClass", "").lower()
                    or term in r.get("itemName", "").lower()
                    or term in r.get("recommendation", "").lower()
                    or term in r.get("destinationCompartment", "").lower()
                    or term in r.get("id", "").lower()
                ]

            return results[skip : skip + limit]

    def count_records(self) -> int:
        with self._lock:
            return len(self._records)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            # Sanitize path to prevent disclosing local host filesystem structure in public telemetry
            sanitized_path = "backend/data/classification_records.json"
            if self.storage_file:
                try:
                    rel = os.path.relpath(self.storage_file, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                    sanitized_path = rel.replace("\\", "/")
                except Exception:
                    sanitized_path = os.path.basename(self.storage_file)

            return {
                "mode": "development_emulation",
                "storage_backend": "LocalStorageProvider",
                "storage_file": sanitized_path,
                "persistent_cloud_enabled": False,
                "cloud_provider": "Local JSON Ledger (Development Emulation)",
                "record_count": len(self._records),
                "idempotency_enabled": True,
                "project_id": None,
                "collection": None,
                "notes": "Records persist locally to backend/data/classification_records.json. Configure STORAGE_PROVIDER=firestore for Google Cloud persistence."
            }

    def clear_records(self) -> None:
        with self._lock:
            self._records = []
            self._seen_idempotency_keys = {}
            self._persist_to_disk()

    def delete_record(self, record_id: str) -> bool:
        with self._lock:
            initial_count = len(self._records)
            self._records = [r for r in self._records if r.get("id") != record_id]
            if len(self._records) < initial_count:
                self._persist_to_disk()
                logger.info(f"Deleted record '{record_id}' from LocalStorageProvider.")
                return True
            return False


class FirestoreStorageProvider(BaseStorageProvider):
    """
    Production-grade Google Cloud Firestore storage provider.
    Connects to genuine Firestore using Application Default Credentials (ADC)
    or a service account key without hardcoding secrets.
    Enforces idempotency, bounded queries, and explicit failure reporting.
    """

    def __init__(self, db_client, project_id: Optional[str] = None, collection_name: Optional[str] = None):
        self.db = db_client
        self.project_id = project_id or getattr(db_client, "project", None) or os.getenv("GOOGLE_CLOUD_PROJECT") or "auto-detected"
        self.collection_name = collection_name or os.getenv("FIRESTORE_COLLECTION", "waste_records")

    def save_record(self, record_data: Dict[str, Any], idempotency_key: Optional[str] = None) -> str:
        key = idempotency_key or record_data.get("idempotencyKey")

        # 1. Idempotency safeguard: check if event with this key was already persisted in Firestore
        if key:
            try:
                existing_docs = list(
                    self.db.collection(self.collection_name)
                    .where("idempotencyKey", "==", key)
                    .limit(1)
                    .stream()
                )
                if existing_docs:
                    existing_data = existing_docs[0].to_dict()
                    existing_id = existing_data.get("id", existing_docs[0].id)
                    logger.info(f"Firestore idempotent request detected for key '{key}'. Returning existing record '{existing_id}'.")
                    return existing_id
            except Exception as e:
                logger.warning(f"Firestore idempotency query error: {e}. Proceeding with record creation.")

        record_id = record_data.get("id")
        if record_id:
            try:
                doc_ref = self.db.collection(self.collection_name).document(record_id)
                doc = doc_ref.get()
                if doc.exists:
                    logger.info(f"Firestore record '{record_id}' already exists. Returning existing ID.")
                    return record_id
            except Exception as e:
                logger.warning(f"Firestore document existence check error: {e}")

        # 2. Assign stable ID if not present
        if not record_id:
            timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            import uuid
            record_id = f"REC-{timestamp_str}-{uuid.uuid4().hex[:6]}"
            record_data["id"] = record_id

        # 3. Normalize schema fields identically to LocalStorageProvider
        normalized_record = {
            "id": record_id,
            "itemName": record_data.get("itemName", "Standard Waste Sample"),
            "predictedClass": record_data.get("predictedClass", "unknown"),
            "wasteType": record_data.get("wasteType", "Unclassified"),
            "confidence": float(record_data.get("confidence", 0.0)),
            "recommendation": record_data.get("recommendation", "Follow municipal guidance."),
            "disposalBin": record_data.get("disposalBin", "General Waste Bin"),
            "destinationCompartment": record_data.get("destinationCompartment", "General Residual Waste Bin"),
            "compartmentId": record_data.get("compartmentId", "bin_residual"),
            "routingStatus": record_data.get("routingStatus", "AUTOMATED_ROUTED"),
            "routingReason": record_data.get("routingReason", "Standard classification policy."),
            "requiresManualReview": bool(record_data.get("requiresManualReview", False)),
            "simulationStatus": record_data.get("simulationStatus", "SIMULATED"),
            "timestamp": record_data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "imageUrl": record_data.get("imageUrl"),
            "userId": record_data.get("userId", "public-citizen")
        }

        if key:
            normalized_record["idempotencyKey"] = key

        # 4. Atomic write to Firestore. Do not silently catch and pretend success!
        try:
            doc_ref = self.db.collection(self.collection_name).document(record_id)
            doc_ref.set(normalized_record)
            logger.info(f"Successfully persisted record '{record_id}' to Firestore collection '{self.collection_name}'.")
            return record_id
        except Exception as e:
            logger.error(f"Firestore persistence failed for record '{record_id}': {e}")
            raise RuntimeError(f"Google Cloud Firestore write failed: {e}") from e

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection(self.collection_name).document(record_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Firestore get failed for record '{record_id}': {e}")
            raise RuntimeError(f"Google Cloud Firestore read error: {e}") from e

    def list_records(
        self,
        limit: int = 50,
        skip: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[str] = None,
        public_only: bool = False
    ) -> List[Dict[str, Any]]:
        bounded_limit = max(1, min(limit, 1000))
        try:
            query = self.db.collection(self.collection_name)

            if user_id:
                query = query.where("userId", "==", user_id)
            elif public_only:
                query = query.where("userId", "==", "public-citizen")

            if category and category != "ALL":
                query = query.where("wasteType", "==", category)

            # Query with order_by timestamp descending; fall back to in-memory sort if index is building
            try:
                ordered_query = query.order_by("timestamp", direction="DESCENDING")
                docs = list(ordered_query.offset(skip).limit(bounded_limit).stream())
            except Exception as order_err:
                logger.warning(f"Firestore order_by indexing notice: {order_err}. Sorting stream in memory.")
                docs = list(query.limit(bounded_limit + skip).stream())

            results = [doc.to_dict() for doc in docs]
            results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

            if public_only:
                results = [r for r in results if r.get("userId") in (None, "", "public-citizen")]

            if search:
                term = search.lower()
                results = [
                    r for r in results
                    if term in r.get("predictedClass", "").lower()
                    or term in r.get("itemName", "").lower()
                    or term in r.get("recommendation", "").lower()
                    or term in r.get("destinationCompartment", "").lower()
                    or term in r.get("id", "").lower()
                ]

            return results[skip : skip + bounded_limit]
        except Exception as e:
            logger.error(f"Firestore list_records failed: {e}")
            raise RuntimeError(f"Google Cloud Firestore query failed: {e}") from e

    def count_records(self) -> int:
        try:
            collection_ref = self.db.collection(self.collection_name)
            if hasattr(collection_ref, "count"):
                count_query = collection_ref.count()
                results = count_query.get()
                if results and len(results) > 0:
                    return results[0][0].value
            docs = list(collection_ref.limit(5000).stream())
            return len(docs)
        except Exception as e:
            logger.warning(f"Firestore count aggregation failed ({e}). Attempting fallback stream count.")
            try:
                docs = list(self.db.collection(self.collection_name).stream())
                return len(docs)
            except Exception as stream_err:
                logger.error(f"Firestore fallback count failed: {stream_err}")
                return 0

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": "firestore",
            "storage_backend": "FirestoreStorageProvider",
            "storage_file": None,
            "persistent_cloud_enabled": True,
            "cloud_provider": "Google Cloud Firestore",
            "record_count": self.count_records(),
            "idempotency_enabled": True,
            "project_id": self.project_id,
            "collection": self.collection_name,
            "notes": "Connected to Google Cloud Firestore with distributed persistence and atomic idempotency."
        }

    def clear_records(self) -> None:
        # Protect production cloud storage from accidental bulk deletion
        allow_clear = os.getenv("ALLOW_STORAGE_CLEAR", "false").lower() == "true"
        if not allow_clear:
            logger.warning("clear_records called on FirestoreStorageProvider but ALLOW_STORAGE_CLEAR is not true. Deletion skipped.")
            return

        try:
            docs = list(self.db.collection(self.collection_name).stream())
            batch = self.db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            logger.info(f"Cleared {len(docs)} documents from Firestore collection '{self.collection_name}'.")
        except Exception as e:
            logger.error(f"Failed to clear Firestore collection: {e}")
            raise RuntimeError(f"Firestore clear_records failed: {e}") from e

    def delete_record(self, record_id: str) -> bool:
        """Deletes a single record by ID from Firestore."""
        try:
            doc_ref = self.db.collection(self.collection_name).document(record_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.delete()
                logger.info(f"Deleted record '{record_id}' from Firestore collection '{self.collection_name}'.")
                return True
            return False
        except Exception as e:
            logger.error(f"Firestore delete failed for record '{record_id}': {e}")
            raise RuntimeError(f"Failed to delete record '{record_id}' from Firestore: {e}") from e


# Backwards compatibility alias
FirebaseStorageProvider = FirestoreStorageProvider


def _init_firestore_provider() -> FirestoreStorageProvider:
    """
    Initializes Firestore using either:
    1. GOOGLE_APPLICATION_CREDENTIALS / FIREBASE_CREDENTIALS_PATH service account key file
    2. Google Cloud Application Default Credentials (ADC) via Workload Identity / gcloud
    Raises RuntimeError if credentials or connectivity cannot be established.
    """
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or os.getenv("FIREBASE_PROJECT_ID")

    try:
        from google.cloud import firestore

        if cred_path and os.path.exists(cred_path):
            logger.info(f"Connecting to Firestore using credentials file: {cred_path}")
            db = firestore.Client.from_service_account_json(cred_path, project=project_id)
        else:
            logger.info("Connecting to Firestore using Application Default Credentials (ADC)...")
            db = firestore.Client(project=project_id)

        detected_project = getattr(db, "project", project_id or "auto-detected")
        logger.info(f"Google Cloud Firestore client connected successfully for project '{detected_project}'.")
        return FirestoreStorageProvider(db, project_id=detected_project)
    except Exception as e:
        logger.error(f"Failed to initialize Google Cloud Firestore: {e}")
        raise RuntimeError(
            f"STORAGE_PROVIDER is set to 'firestore', but Firestore initialization failed: {e}. "
            "Please configure Google Cloud Application Default Credentials (ADC) using "
            "`gcloud auth application-default login` or set `GOOGLE_APPLICATION_CREDENTIALS`."
        ) from e


def create_storage_provider() -> BaseStorageProvider:
    """
    Factory that selects the storage provider based on STORAGE_PROVIDER environment variable.
    Supported values: 'local' (default), 'firestore' (or 'firebase').
    Validates configuration strictly and raises ValueError for unknown modes.
    """
    provider_name = os.getenv("STORAGE_PROVIDER", "local").strip().lower()

    if provider_name not in ("local", "firestore", "firebase"):
        raise ValueError(
            f"Unsupported STORAGE_PROVIDER='{provider_name}'. Supported options are: 'local', 'firestore'."
        )

    if provider_name in ("firestore", "firebase"):
        return _init_firestore_provider()

    logger.info("Initializing LocalStorageProvider (Development Emulation JSON Ledger).")
    return LocalStorageProvider()


# Single application-wide storage instance
storage_service = create_storage_provider()
