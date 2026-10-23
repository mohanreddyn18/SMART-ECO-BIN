import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ecosort.firebase")

class FirebaseService:
    def __init__(self):
        self.initialized = False
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if cred_path and os.path.exists(cred_path):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore, storage
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'ecosort-ai.appspot.com')
                })
                self.db = firestore.client()
                self.initialized = True
                logger.info("Firebase Admin SDK successfully connected.")
            except Exception as e:
                logger.warning(f"Could not initialize Firebase Admin SDK: {e}. Running in local session mode.")
                self.db = None
        else:
            logger.info("No FIREBASE_CREDENTIALS_PATH found. Running Firebase service in development emulation mode.")
            self.db = None

    def save_waste_record(self, record_data: Dict[str, Any]) -> str:
        if self.initialized and self.db:
            try:
                doc_ref = self.db.collection('waste_records').document(record_data.get('id', ''))
                doc_ref.set(record_data)
                return doc_ref.id
            except Exception as e:
                logger.error(f"Failed to persist to Firestore: {e}")
        return record_data.get('id', 'REC-LOCAL')

firebase_service = FirebaseService()
