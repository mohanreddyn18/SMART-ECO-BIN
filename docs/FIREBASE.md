# RJ 147 — Firebase Architecture & Security Rules

**Application:** EcoSort AI  
**Cloud Engine:** Google Firebase  

---

## 1. Firebase Suite Integration

EcoSort AI utilizes Firebase for identity management, document persistence, and object storage:

### A. Firebase Authentication
- **Methods:** Email / Password authentication.
- **Roles:**
  - `user`: Standard researcher / campus user. Access to detection, history, analytics, WasteAI.
  - `admin`: Facility supervisor. Full access to administrative command, SanitationAI, user management, and rule tuning.

### B. Cloud Firestore
The database schema consists of three primary collections:

#### `users` Collection
```json
{
  "userId": "string (UUID / Auth UID)",
  "name": "string",
  "email": "string",
  "role": "string ('user' | 'admin')",
  "createdAt": "timestamp",
  "classificationsCount": "number"
}
```

#### `waste_records` Collection
```json
{
  "recordId": "string",
  "userId": "string",
  "imageUrl": "string (Firebase Storage URL)",
  "predictedClass": "string",
  "confidence": "number",
  "wasteType": "string",
  "recommendation": "string",
  "timestamp": "timestamp",
  "location": "string (optional department tag)"
}
```

#### `sanitation_reports` Collection
```json
{
  "reportId": "string",
  "userId": "string",
  "issueType": "string",
  "severity": "string ('Low' | 'Medium' | 'High')",
  "location": "string",
  "timestamp": "timestamp"
}
```

### C. Firebase Cloud Storage
- Stores uploaded waste sample images under `waste_images/{userId}/{timestamp}_{filename}`.
- Enforces strict image MIME types (`image/jpeg`, `image/png`, `image/webp`).

---

## 2. Firestore Security Rules

Deploy these rules in Firebase Console:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }

    function isAdmin() {
      return isAuthenticated() &&
        request.auth.token.role == 'admin' ||
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
    }

    // User profile rules
    match /users/{userId} {
      allow read: if isAuthenticated();
      allow write: if isAuthenticated() && (request.auth.uid == userId || isAdmin());
    }

    // Classification records rules
    match /waste_records/{recordId} {
      allow read: if isAuthenticated();
      allow create: if isAuthenticated();
      allow update, delete: if isAdmin();
    }

    // Sanitation reports rules
    match /sanitation_reports/{reportId} {
      allow read: if isAuthenticated();
      allow create: if isAuthenticated();
      allow update, delete: if isAdmin();
    }
  }
}
```
