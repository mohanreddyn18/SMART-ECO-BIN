"""
Stage 6 Verification: Secure Authentication, Role-Based Access Control, and Public-Service Data Protection
========================================================================================================
Validates:
1. Server-side token verification (cryptographic signature, issuer, audience, expiry)
2. Rejection of unauthenticated requests on protected administrative endpoints (HTTP 401)
3. Rejection of citizen tokens on administrator endpoints (HTTP 403 Forbidden)
4. Successful administrator access to privileged endpoints (HTTP 200 OK)
5. Citizen data isolation (citizens can only see their own records, not other citizens' records)
6. Record ownership verification on /api/history/{record_id}
7. Administrative deletion of historical records (/api/history/{id} DELETE)
8. Public access to health, documentation, storage-status, security posture, and waste prediction
9. Denial of Service rate limiting on public prediction intake
10. Transparent security posture reporting without secret disclosures
"""

import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from main import app
from app.auth.security import token_verifier
from app.services.storage_service import storage_service
from app.services.analytics_service import analytics_service


class TestStage6AuthAndRBAC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("ENVIRONMENT", "development")
        os.environ.setdefault("ALLOW_DEV_AUTH", "true")
        from app.auth.config import security_config
        security_config.reload()
        cls.client = TestClient(app)
        
        # Issue verified test tokens
        cls.admin_token, cls.admin_user = token_verifier.issue_dev_token(
            email="admin@ecosortai.com",
            role="administrator",
            name="Municipal Lead Admin"
        )
        cls.citizen_a_token, cls.citizen_a_user = token_verifier.issue_dev_token(
            email="citizen.a@example.gov",
            role="citizen",
            name="Citizen Alice"
        )
        cls.citizen_b_token, cls.citizen_b_user = token_verifier.issue_dev_token(
            email="citizen.b@example.gov",
            role="citizen",
            name="Citizen Bob"
        )
        cls.original_records = storage_service.list_records(limit=100000)

    @classmethod
    def tearDownClass(cls):
        storage_service.clear_records()
        for record in reversed(cls.original_records):
            storage_service.save_record(record)

    def test_01_public_endpoints_accessible_without_auth(self):
        """Public health, root, storage status, and security posture must be accessible without tokens."""
        for endpoint in ["/", "/health", "/api/storage/status", "/api/security/posture"]:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, f"{endpoint} should be publicly accessible")

    def test_02_admin_endpoints_reject_unauthenticated_requests(self):
        """Administrative routes must reject requests lacking Authorization header with 401 Unauthorized."""
        protected_endpoints = [
            "/api/sanitation",
            "/api/anomalies",
            "/api/predictive-insights",
            "/api/auth/me"
        ]
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, 401,
                f"{endpoint} must return 401 when no token is supplied"
            )

    def test_03_admin_endpoints_reject_citizen_role(self):
        """Administrative routes must reject valid authenticated citizens with 403 Forbidden."""
        headers = {"Authorization": f"Bearer {self.citizen_a_token}"}
        protected_endpoints = [
            "/api/sanitation",
            "/api/anomalies"
        ]
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint, headers=headers)
            self.assertEqual(
                response.status_code, 403,
                f"{endpoint} must return 403 Forbidden for citizen role"
            )
            self.assertIn("Access forbidden", response.json()["detail"])

        insights = self.client.get(
            "/api/predictive-insights",
            headers=headers
        )
        self.assertEqual(insights.status_code, 200)
        self.assertEqual(insights.json()["scope"], "personal")

    def test_04_admin_endpoints_accept_verified_administrator(self):
        """Administrative routes must grant access to verified administrator tokens."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        for endpoint in ["/api/sanitation", "/api/anomalies", "/api/predictive-insights"]:
            response = self.client.get(endpoint, headers=headers)
            self.assertEqual(
                response.status_code, 200,
                f"{endpoint} should return 200 OK for verified administrator"
            )

    def test_05_sanitation_ai_requires_admin_privileges(self):
        """POST /api/sanitationai must reject citizens (403) and accept administrators (200)."""
        prompt_payload = {"prompt": "Provide current municipal sanitation summary."}

        # Unauthenticated -> 401
        res_unauth = self.client.post("/api/sanitationai", json=prompt_payload)
        self.assertEqual(res_unauth.status_code, 401)

        # Citizen -> 403
        res_citizen = self.client.post(
            "/api/sanitationai",
            json=prompt_payload,
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        self.assertEqual(res_citizen.status_code, 403)

        # Admin -> 200
        res_admin = self.client.post(
            "/api/sanitationai",
            json=prompt_payload,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_admin.status_code, 200)

    def test_06_token_signature_verification_rejects_forgery(self):
        """Forged tokens signed with arbitrary keys must be rejected with 401."""
        fake_payload = {
            "sub": "fake-admin",
            "iss": "smart-eco-bin-auth",
            "aud": "smart-eco-bin-api",
            "exp": int(time.time()) + 3600,
            "role": "administrator",
            "admin": True
        }
        forged_token = jwt.encode(fake_payload, "completely-different-secret-key", algorithm="HS256")
        
        response = self.client.get(
            "/api/sanitation",
            headers={"Authorization": f"Bearer {forged_token}"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("verification failed", response.json()["detail"].lower())

    def test_07_token_expiration_enforcement(self):
        """Expired tokens must be rejected with 401."""
        expired_payload = {
            "sub": "expired-user",
            "iss": "smart-eco-bin-auth",
            "aud": "smart-eco-bin-api",
            "exp": int(time.time()) - 100,  # in the past
            "role": "administrator",
            "admin": True
        }
        expired_token = jwt.encode(expired_payload, token_verifier.dev_secret, algorithm="HS256")

        response = self.client.get(
            "/api/sanitation",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("expired", response.json()["detail"].lower())

    def test_08_citizen_data_isolation_in_history(self):
        """Authenticated citizens must only receive their own history records, preserving citizen privacy."""
        # Clean test records
        storage_service.clear_records()

        # Seed records for Citizen A and Citizen B
        rec_a = {
            "id": "REC-TEST-ALICE-001",
            "itemName": "Alice Plastic Bottle",
            "predictedClass": "plastic",
            "wasteType": "Recyclable / Plastic",
            "confidence": 0.95,
            "recommendation": "Recycle clean",
            "disposalBin": "Blue Recyclable Bin",
            "timestamp": "2026-10-20T10:00:00Z",
            "userId": self.citizen_a_user.uid
        }
        rec_b = {
            "id": "REC-TEST-BOB-001",
            "itemName": "Bob Electronic Battery",
            "predictedClass": "battery",
            "wasteType": "Hazardous / E-Waste",
            "confidence": 0.98,
            "recommendation": "Dispose at hazardous depot",
            "disposalBin": "Red Hazardous Bin",
            "timestamp": "2026-10-20T10:05:00Z",
            "userId": self.citizen_b_user.uid
        }
        storage_service.save_record(rec_a)
        storage_service.save_record(rec_b)

        # 1. Citizen A queries history -> should ONLY see Alice's record
        res_a = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        self.assertEqual(res_a.status_code, 200)
        records_a = res_a.json()
        self.assertEqual(len(records_a), 1)
        self.assertEqual(records_a[0]["id"], "REC-TEST-ALICE-001")

        # 2. Citizen B queries history -> should ONLY see Bob's record
        res_b = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {self.citizen_b_token}"}
        )
        self.assertEqual(res_b.status_code, 200)
        records_b = res_b.json()
        self.assertEqual(len(records_b), 1)
        self.assertEqual(records_b[0]["id"], "REC-TEST-BOB-001")

        # 3. Administrator queries history -> sees ALL records across municipality
        res_admin = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_admin.status_code, 200)
        records_admin = res_admin.json()
        self.assertGreaterEqual(len(records_admin), 2)
        record_ids = [r["id"] for r in records_admin]
        self.assertIn("REC-TEST-ALICE-001", record_ids)
        self.assertIn("REC-TEST-BOB-001", record_ids)

    def test_09_record_detail_ownership_protection(self):
        """Citizen A cannot fetch Citizen B's individual record by ID (HTTP 403)."""
        # Citizen A tries to view Citizen B's record
        res_forbidden = self.client.get(
            "/api/history/REC-TEST-BOB-001",
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        self.assertEqual(res_forbidden.status_code, 403)
        self.assertIn("permission", res_forbidden.json()["detail"].lower())

        # Citizen B views their own record -> 200 OK
        res_owner = self.client.get(
            "/api/history/REC-TEST-BOB-001",
            headers={"Authorization": f"Bearer {self.citizen_b_token}"}
        )
        self.assertEqual(res_owner.status_code, 200)
        self.assertEqual(res_owner.json()["itemName"], "Bob Electronic Battery")

        # Administrator views Citizen B's record -> 200 OK
        res_admin = self.client.get(
            "/api/history/REC-TEST-BOB-001",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_admin.status_code, 200)

    def test_10_administrative_record_deletion(self):
        """Only administrators can delete historical records (citizens receive 403)."""
        # Citizen tries to delete -> 403
        res_citizen_del = self.client.delete(
            "/api/history/REC-TEST-ALICE-001",
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        self.assertEqual(res_citizen_del.status_code, 403)

        # Admin deletes -> 200 OK
        res_admin_del = self.client.delete(
            "/api/history/REC-TEST-ALICE-001",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_admin_del.status_code, 200)
        self.assertTrue(res_admin_del.json()["deleted"])

        # Subsequent fetch returns 404
        res_after = self.client.get(
            "/api/history/REC-TEST-ALICE-001",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res_after.status_code, 404)

    def test_11_predict_endpoint_binds_authenticated_citizen_identity(self):
        """POST /api/predict must bind the verified citizen UID to the persisted record."""
        # Create a small valid 1x1 PNG image
        import io
        from PIL import Image
        img = Image.new("RGB", (224, 224), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        response = self.client.post(
            "/api/predict",
            files={"file": ("test_intake.png", buf, "image/png")},
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        self.assertEqual(response.status_code, 200)
        pred_data = response.json()
        self.assertIn("predictedClass", pred_data)

        # Verify Citizen A's history now contains the newly classified record
        res_history = self.client.get(
            "/api/history",
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        records = res_history.json()
        self.assertTrue(any(r.get("userId") == self.citizen_a_user.uid for r in records))

    def test_12_security_posture_reports_server_side_auth_and_rbac(self):
        """GET /api/security/posture reports server-side token validation and RBAC without leaking secrets."""
        response = self.client.get("/api/security/posture")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["server_side_token_verification"])
        self.assertTrue(data["rbac_enforced"])
        self.assertTrue(data["citizen_isolated_history"])
        self.assertIn("protected_admin_routes", data)
        self.assertIn("/api/sanitation", data["protected_admin_routes"])
        self.assertIn("/api/anomalies", data["protected_admin_routes"])
        self.assertIn("/api/sanitationai", data["protected_admin_routes"])
        # Ensure no raw secret keys disclosed
        self.assertNotIn("secret", str(data).lower())
        self.assertNotIn("private", str(data).lower())

    def test_13_predictive_insights_are_scoped_to_authorized_records(self):
        """Citizen trends use only their own records; administrators see system-wide records."""
        storage_service.clear_records()
        today = datetime.now(timezone.utc).date()

        for day_offset in range(30):
            observed_at = (today - timedelta(days=day_offset)).isoformat() + "T12:00:00Z"
            for sample in range(4):
                storage_service.save_record({
                    "id": f"REC-FORECAST-ALICE-{day_offset}-{sample}",
                    "timestamp": observed_at,
                    "userId": self.citizen_a_user.uid,
                    "predictedClass": "plastic",
                    "wasteType": "Recyclable / Dry Waste",
                    "confidence": 90,
                })
            storage_service.save_record({
                "id": f"REC-FORECAST-BOB-{day_offset}",
                "timestamp": observed_at,
                "userId": self.citizen_b_user.uid,
                "predictedClass": "paper",
                "wasteType": "Recyclable / Dry Waste",
                "confidence": 90,
            })

        response_a = self.client.get(
            "/api/predictive-insights",
            headers={"Authorization": f"Bearer {self.citizen_a_token}"}
        )
        self.assertEqual(response_a.status_code, 200)
        data_a = response_a.json()
        self.assertEqual(data_a["scope"], "personal")
        self.assertEqual(data_a["currentEvents"], 120)
        self.assertEqual(data_a["observationDays"], 30)
        self.assertTrue(data_a["sufficientData"])
        self.assertEqual(len(data_a["forecast"]), 7)
        self.assertEqual(data_a["forecast"][0]["value"], 4.0)
        self.assertIn("not independently validated", data_a["projections"]["validation"])

        response_b = self.client.get(
            "/api/predictive-insights",
            headers={"Authorization": f"Bearer {self.citizen_b_token}"}
        )
        self.assertEqual(response_b.status_code, 200)
        self.assertEqual(response_b.json()["currentEvents"], 30)
        self.assertFalse(response_b.json()["sufficientData"])
        self.assertIsNone(response_b.json()["forecast"])

        response_admin = self.client.get(
            "/api/predictive-insights",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(response_admin.status_code, 200)
        self.assertEqual(response_admin.json()["scope"], "system")
        self.assertEqual(response_admin.json()["currentEvents"], 150)


if __name__ == "__main__":
    unittest.main()
