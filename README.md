# LabelVerify — Alcohol Label Verification Prototype

A standalone, human-in-the-loop TTB label review assistant built with **React + TypeScript**, **FastAPI**, and **Tesseract OCR** (local CPU inference). No hosted AI service or API key is required.

> **Prototype only.** This application does **not** issue COLA approvals or certify legal compliance. The user must review original artwork, particularly the government warning typography, placement, and minimum size.

## Features

- Upload a single image or a batch of up to 20 images (PNG/JPEG/WEBP, 12 MB each).
- OCR label artwork using locally executed Tesseract OCR.
- Compare declared brand, class/type, ABV/proof, net contents, producer/address and country of origin.
- Handle case/punctuation differences and ABV/proof equivalence; normalize volume units.
- Check government warning wording, flag typographic requirements for manual review.
- Display field-by-field evidence, raw OCR lines, errors, elapsed time, and export CSV.
- No database: files are processed in memory, with no intentional persistent storage.

## Quick start (Docker)

Requirements: Docker Engine with Compose plugin, sufficient disk space for Docker images and a working Docker installation.

```bash
docker compose up --build
```

Open **http://localhost:8080**. FastAPI Swagger documentation: **http://localhost:8000/docs**.

**Note:** Tesseract OCR runs locally in the container and does not require an external OCR API. Processing speed depends on the host and image quality.

## Development without Docker

Backend (Python 3.10 recommended):

```bash
cd backend
python3.10 -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173**. Vite proxies `/api` to FastAPI.

## Tests

```bash
cd backend
pip install -r requirements-test.txt
pytest -q
```

Frontend build check:

```bash
cd frontend
npm install
npm run build
```

## API

`POST /api/verify` — multipart form: `files` (one or more image files) and `application` (JSON string). Example:

```bash
curl -X POST http://localhost:8000/api/verify \
  -F 'files=@sample-label.png' \
  -F 'application={"brand":"OLD TOM DISTILLERY","class_type":"Kentucky Straight Bourbon Whiskey","abv":"45%","net_contents":"750 mL"}'
```

`GET /api/health` — simple readiness response (does not warm OCR models).

## Architecture

Browser → nginx static React site → `/api/verify` → FastAPI → Pillow preprocessing → Tesseract OCR → deterministic validation → JSON results. The application processes batch items sequentially to control memory usage. OCR is performed locally using the Tesseract binary.

## Design decisions and limitations

1. **Human review:** OCR misses, uncertainty, and incomplete warning verification are marked `manual_review`, not approved. `mismatch` means an observed numerical value differs; an agent must still confirm that the detected text belongs to the correct label field.
2. **Government warning:** Wording is normalized for OCR comparison, so punctuation/case changes in the body are **not** conclusively checked. Boldface, exact heading capitalization, size, contrast and location cannot be reliably proven by plain OCR and always require human review. Refer to current TTB rules before making a regulatory decision.
3. **Context:** Numerical matching is regex-based and can confuse multiple percentages or quantities in complex artwork. A production solution should detect field regions and use more advanced entity extraction with provenance.
4. **Batch:** Up to 20 files are accepted but processed sequentially within one HTTP request. Large batches can take minutes and may time out on some reverse proxies. A production implementation needs an async job queue, progress tracking, and cancel/retry controls.
5. **Performance:** The stakeholder target is approximately **5 seconds per label**. This is a performance target, **not a demonstrated guarantee**. Hardware, resolution, and cold starts and limited CPU resources affect latency. Each response reports measured processing time. Benchmark on target hardware before claiming the SLO is met.
6. **Security:** Prototype uses no authentication, persistent file storage, malware scanning, or formal retention policies. Add identity, access control, logging redaction, encryption, limits, security review, and appropriate authorization before any federal production use.
7. **Network:** No inference requests leave the application at runtime . Build-time Python/npm package installation require network access.
8. **OCR trade-off:** Tesseract is lighter than PaddleOCR, but may be less accurate on stylized, rotated, or low-quality labels.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker and Render deployment instructions. Public hosting is optional for local development; a public HTTPS URL is required for the take-home submission.

## Suggested evaluation test cases

- Correct bourbon label with matching brand, 45% ABV / 90 proof and 750 mL.
- Case/punctuation variation: `STONE'S THROW` vs `Stone's Throw`.
- Mismatch: application 45% vs label 40%.
- Warning omitted, incomplete, or heading in title case → manual review.
- Blurry/rotated image → uncertain extraction/manual review.
- Multi-image batch; invalid image; oversized file.

## Assumptions

- The same application data applies to all images in a batch. Production import batches should support per-image application metadata.
- Optional fields are not checked if blank.
- Warning statement is required on all alcohol beverage labels, but this tool does not determine beverage-specific exemptions or the complete regulatory compliance matrix.
- No integration with COLA or other federal systems.

## License

Prototype demonstration code; review licensing of Tesseract and other dependencies independently before distribution.
