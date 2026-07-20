# API Design — Social Support AI

## Base URL
```
/api/v1
```

## Authentication
All endpoints except `/auth/*` and `/health` require:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Authentication
```
POST   /auth/login          # Returns JWT access + refresh tokens
POST   /auth/refresh        # Refresh expired access token
GET    /auth/me             # Current user profile and permissions
```

### Applications
```
POST   /applications                             # Submit new application
GET    /applications                              # List user's applications (paginated)
GET    /applications/{application_id}             # Get full application details
DELETE /applications/{application_id}             # Cancel/withdraw application

POST   /applications/{application_id}/documents   # Upload a document (multipart)
DELETE /applications/{application_id}/documents/{document_id}

GET    /applications/{application_id}/status      # Get processing status + current step
POST   /applications/{application_id}/submit      # Change status from draft → submitted
```

### Processing (Workflow control)
```
POST   /applications/{application_id}/process     # Trigger/retry workflow execution
POST   /applications/{application_id}/resume      # Resume from human-in-the-loop checkpoint
GET    /applications/{application_id}/workflow     # Get workflow graph state
```

### Human-in-the-loop
```
GET    /applications/pending-review               # List apps needing human review
GET    /applications/{application_id}/flags        # Get inconsistency flags
POST   /applications/{application_id}/resolve-flag # Resolve an inconsistency flag
POST   /applications/{application_id}/approve      # Human approves
POST   /applications/{application_id}/decline      # Human declines (requires reason)
```

### Assessment & Decisions
```
GET    /applications/{application_id}/assessment   # ML score + LLM rationale
GET    /applications/{application_id}/features     # Feature importance (SHAP)
GET    /applications/{application_id}/recommendations  # Economic enablement suggestions
```

### Chat
```
POST   /chat                          # Send message (with application_id context)
GET    /chat/{session_id}/history     # Get chat history
DELETE /chat/{session_id}             # Clear session
```

### Knowledge Base (RAG)
```
GET    /policies?query=...&limit=10   # Search government policies
GET    /programs?query=...&limit=10   # Search training/job programs
```

### Admin
```
GET    /admin/dashboard               # Aggregated stats (total apps, avg time, approval rate)
GET    /admin/applications             # All applications (with filters: status, date range)
GET    /admin/applications/{id}/audit  # Full audit trail
GET    /admin/metrics                  # System metrics (latency, error rates, token usage)
```

### Health
```
GET    /health                        # Service health + DB connectivity checks
```

## Request/Response Examples

### Submit Application
```json
POST /api/v1/applications
{
  "applicant": {
    "full_name": "Ahmed Al Mansouri",
    "emirates_id": "784-1990-1234567-1",
    "passport_number": "A12345678",
    "date_of_birth": "1990-05-15",
    "nationality": "UAE",
    "phone": "+971501234567",
    "email": "ahmed@example.com",
    "address": {
      "street": "Al Reem Island",
      "city": "Abu Dhabi",
      "emirate": "Abu Dhabi",
      "po_box": "12345"
    }
  },
  "metadata": {
    "application_type": "financial_support",
    "support_category": "monthly_stipend",
    "notes": ""
  }
}

Response: 201
{
  "application_id": "a1b2c3d4-...",
  "status": "draft",
  "created_at": "2026-07-20T10:00:00Z",
  "upload_urls": {
    "documents": "/api/v1/applications/a1b2c3d4-.../documents"
  }
}
```

### Upload Document
```
POST /api/v1/applications/{id}/documents
Content-Type: multipart/form-data

file: <binary>
document_type: "bank_statement"

Response: 201
{
  "document_id": "d1e2f3a4-...",
  "document_type": "bank_statement",
  "file_name": "statement.pdf",
  "file_size": 245760,
  "status": "pending"
}
```

### Get Assessment
```json
GET /api/v1/applications/{id}/assessment

Response: 200
{
  "application_id": "a1b2c3d4-...",
  "ml_score": 0.72,
  "ml_confidence": 0.89,
  "feature_importance": {
    "monthly_income": 0.35,
    "family_size": 0.25,
    "employment_stability": 0.18,
    "total_assets": 0.12,
    "credit_score": 0.10
  },
  "llm_rationale": "The applicant's monthly income of AED 4,200 is below the threshold of AED 5,000 for single applicants, but with a family size of 4 dependents, the per-capita income falls within the moderate support bracket. Employment history shows 3 years of stable government employment. The ML model score of 0.72 supports approval with economic enablement recommendations.",
  "decision": "approved",
  "recommendations": [
    {
      "category": "training",
      "title": "UAE Digital Skills Program",
      "description": "Free 6-month online program covering digital literacy and basic coding",
      "relevance_score": 0.85
    },
    {
      "category": "job",
      "title": "Government Administrative Assistant - Abu Dhabi",
      "description": "Entry-level position at Ministry of Community Development",
      "relevance_score": 0.78
    }
  ],
  "audit_trail_url": "/api/v1/admin/applications/a1b2c3d4-.../audit"
}
```

### Chat
```json
POST /api/v1/chat
{
  "application_id": "a1b2c3d4-...",
  "session_id": null,
  "message": "Why was my application approved but with training recommendations?"
}

Response: 200
{
  "session_id": "s1e2f3a4-...",
  "reply": "Your application was approved for monthly financial support of AED 3,500. The training recommendations were added because the ML model identified that upskilling could increase your long-term earning potential by an estimated 40%. The Economic Enablement Program is optional and does not affect your current support amount.",
  "sources": [
    {"type": "policy", "title": "Social Support Program Guidelines 2026", "relevance": 0.92},
    {"type": "ml_feature", "name": "income_growth_potential", "value": 0.4}
  ]
}
```
