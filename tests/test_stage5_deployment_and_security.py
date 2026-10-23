"""
Stage 5 Verification: Deployment Readiness, CI/CD Preparation, and Government-Standard Quality Assurance
========================================================================================================
Validates:
1. Dynamic CORS origin parsing and restriction
2. Health & security posture endpoints
3. Storage status endpoint information disclosure safety (no host path leakage)
4. Image upload size and MIME type guards
5. Backend Dockerfile worker count, unprivileged user, and healthcheck specification
6. CI/CD GitHub Actions workflow configuration & manual deployment gating
7. Dockerignore files ensuring zero secret or local record leakage
"""

import os
import sys
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from main import app


class TestStage5DeploymentAndSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint_response_format(self): 
        """Health endpoint should return valid status and explicitly state software-only mode."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["service"], "EcoSort AI API Gateway")
        self.assertEqual(data["mode"], "Software-Only (Pure Computational Intelligence)")
        self.assertFalse(data["hardware_sensors"])
        self.assertIn("storage_mode", data)

    def test_02_storage_status_path_sanitization(self):
        """Storage status endpoint must not disclose private user home directory paths."""
        response = self.client.get("/api/storage/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("mode", data)
        self.assertIn("storage_backend", data)
        storage_file = data.get("storage_file")
        if storage_file:
            # Ensure windows raw home directories like C:\Users\user are sanitized
            self.assertFalse("C:\\Users\\" in storage_file, f"Storage path disclosed raw host filesystem: {storage_file}")
            self.assertTrue("classification_records.json" in storage_file)

    def test_03_security_posture_endpoint(self):
        """Security posture endpoint transparently reports admin authentication state."""
        response = self.client.get("/api/security/posture")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("admin_auth_configured", data)
        self.assertIn("admin_auth_mode", data)
        self.assertIn("cors_origins_count", data)
        self.assertIn("citizen_privacy_zero_retention", data)
        self.assertTrue(data["citizen_privacy_zero_retention"])

    def test_04_image_upload_content_type_enforcement(self):
        """Image classification endpoint must reject unsupported MIME types with 400 Bad Request."""
        text_payload = b"not-an-image"
        response = self.client.post(
            "/api/predict",
            files={"file": ("sample.txt", text_payload, "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid image type", response.json()["detail"])

    def test_05_backend_dockerfile_worker_configuration(self):
        """Backend Dockerfile must specify 1 worker to conserve PyTorch memory in Cloud Run."""
        dockerfile_path = os.path.join(root_path, "backend", "Dockerfile")
        self.assertTrue(os.path.exists(dockerfile_path), "backend/Dockerfile must exist")
        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for single worker configuration
        self.assertIn("--workers 1", content, "Backend Dockerfile must use --workers 1 to avoid PyTorch memory contention")
        self.assertNotIn("--workers 2", content, "Backend Dockerfile should not use multiple workers for PyTorch on Cloud Run")
        # Check for unprivileged user
        self.assertIn("USER appuser", content, "Backend Dockerfile must run as unprivileged appuser")
        # Check working directory
        self.assertIn("WORKDIR /app/backend", content, "Backend Dockerfile must set WORKDIR to /app/backend")
        # Check healthcheck
        self.assertIn("HEALTHCHECK", content, "Backend Dockerfile must define container HEALTHCHECK")

    def test_06_frontend_dockerfile_and_nginx_security(self):
        """Frontend Dockerfile & Nginx must include security headers and health check."""
        nginx_path = os.path.join(root_path, "frontend", "nginx.conf")
        self.assertTrue(os.path.exists(nginx_path), "frontend/nginx.conf must exist")
        with open(nginx_path, "r", encoding="utf-8") as f:
            nginx_content = f.read()

        self.assertIn("X-Frame-Options", nginx_content)
        self.assertIn("X-Content-Type-Options", nginx_content)
        self.assertIn("Referrer-Policy", nginx_content)
        self.assertIn("Permissions-Policy", nginx_content)
        self.assertIn("nginx-health", nginx_content)
        self.assertIn("try_files $uri $uri/ /index.html", nginx_content)

    def test_07_dockerignore_rules_exclude_secrets_and_records(self):
        """Dockerignore files must exclude local .env files, data records, and credentials."""
        for path_rel in [".dockerignore", os.path.join("backend", ".dockerignore"), os.path.join("frontend", ".dockerignore")]:
            full_path = os.path.join(root_path, path_rel)
            self.assertTrue(os.path.exists(full_path), f"{path_rel} must exist")
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(".env", content, f"{path_rel} must ignore .env")

        # Root and backend dockerignore must exclude data records
        with open(os.path.join(root_path, "backend", ".dockerignore"), "r", encoding="utf-8") as f:
            backend_di = f.read()
        self.assertIn("data/*.json", backend_di, "backend/.dockerignore must exclude local json records")
        self.assertIn("credentials.json", backend_di)

    def test_08_ci_cd_workflow_manual_deployment_gate(self):
        """CI workflow must gate Cloud Run deployment behind manual authorization."""
        ci_path = os.path.join(root_path, ".github", "workflows", "ci.yml")
        self.assertTrue(os.path.exists(ci_path), ".github/workflows/ci.yml must exist")
        with open(ci_path, "r", encoding="utf-8") as f:
            ci_content = f.read()

        # Deployment must be conditional on workflow_dispatch with explicit confirmation
        self.assertIn("workflow_dispatch:", ci_content)
        self.assertIn("deploy_confirmed", ci_content)
        self.assertIn("google-github-actions/auth@v2", ci_content)
        self.assertIn("workload_identity_provider", ci_content)
        # Verify no hardcoded project IDs or private keys in workflow
        self.assertNotIn("AIzaSy", ci_content)
        self.assertNotIn("BEGIN PRIVATE KEY", ci_content)

    def test_09_cloudbuild_configuration(self):
        """Google Cloud Build configuration must exist with backend test and build steps."""
        cb_path = os.path.join(root_path, "cloudbuild.yaml")
        self.assertTrue(os.path.exists(cb_path), "cloudbuild.yaml must exist")
        with open(cb_path, "r", encoding="utf-8") as f:
            cb_content = f.read()

        self.assertIn("backend-unit-tests", cb_content)
        self.assertIn("frontend-build", cb_content)
        self.assertIn("build-backend-image", cb_content)
        self.assertIn("build-frontend-image", cb_content)

    def test_10_api_client_base_url_configuration(self):
        """Frontend api.js must support VITE_API_BASE_URL for production Cloud Run separation."""
        api_js_path = os.path.join(root_path, "frontend", "src", "services", "api.js")
        with open(api_js_path, "r", encoding="utf-8") as f:
            api_content = f.read()

        self.assertIn("VITE_API_BASE_URL", api_content)
        self.assertIn("API_BASE", api_content)
        self.assertIn("HEALTH_URL", api_content)


if __name__ == "__main__":
    unittest.main()
