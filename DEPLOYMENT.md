# Deployment Guide

This variant replaces PaddleOCR with **Tesseract OCR**, an offline, lower-memory OCR engine. It is not equivalent in accuracy and does not guarantee the five-second target. The UI and API share a single public URL.

## GitHub update
Upload the **contents** of this folder to the root of your GitHub repository, replacing existing files where names overlap. In particular, add the new root-level `Dockerfile` and `render.yaml`, and replace `backend/app/ocr.py`, `backend/app/main.py`, `backend/requirements.txt`, and `frontend/src/App.tsx`.

## Render
1. Choose **New > Web Service**, select your GitHub repository.
2. Name: `ttb-label-verifier`; Language: **Docker**; Branch: `main`.
3. Root Directory: **leave blank**. Dockerfile Path: `./Dockerfile`.
4. Instance type: **Free**. Do not upgrade or enter payment details.
5. Deploy. Visit `https://<your-service>.onrender.com` when live.

Render free web services may spin down after inactivity, causing long cold starts. The 5-second goal is not guaranteed on free hosting. A free service can run out of memory on large images or batches. Test a small label first. No image data is persisted by this application. For large batches or stronger OCR, use local PaddleOCR deployment from the original project.

## Local Docker run
`docker build -t ttb-label-verifier .`
`docker run --rm -p 8080:10000 ttb-label-verifier`
Then open http://localhost:8080.

## Smoke tests
- Open `/api/health` and expect `{"status":"ok"}`.
- Upload a readable JPG/PNG of a sample label in the UI.
- Confirm OCR text, per-field results, and CSV export.
- Verify poor-quality labels return manual review rather than regulatory approval.

## Limitations
- Tesseract can misread curved, low-light or rotated labels; text formatting (bold, size, placement) requires manual review.
- 20 files per request is a free-hosting safety limit, not the stakeholder's 300-file stretch goal.
- No user accounts, database, production COLA integration, or formal regulatory approval.
- The code was statically checked; full Docker build and live Render deployment must be tested by the submitter.
