# Cross-Teammate Requests & Interface Log

Use this document to propose and confirm contract changes between DuroT (Backend) and Peace (Frontend).

| ID | From | To | Request Description | Status | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| REQ-01 | DuroT | Peace | Initial schema published in `docs/shared/02-api-contracts.md`. Please review field names. | APPROVED | Peace adopted TypeScript interfaces in Task P1. |
| REQ-02 | Peace | DuroT | Ensure `/api/sample/{dataset_id}` returns instantly without calling external APIs during live demo. | APPROVED | DuroT will store pre-computed JSON files in `backend/data/sample_trios/`. |
