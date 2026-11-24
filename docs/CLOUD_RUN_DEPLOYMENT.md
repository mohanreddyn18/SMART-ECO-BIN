# Backend deployment

The original SMART ECO BIN frontend is hosted by Vercel. Only the FastAPI
backend and its model weights are deployed to Google Cloud Run.

Use the maintained [Vercel + Cloud Run deployment guide](VERCEL_CLOUD_RUN_DEPLOYMENT.md)
for the complete setup, including Firebase Authentication, Firestore, CORS,
environment variables, model files, Cloud Run IAM, and health verification.

The earlier version of this document described hosting both frontend and
backend on Cloud Run and included incomplete authentication and deployment
commands. Do not follow those older instructions; the architecture above and
the linked guide are authoritative.
