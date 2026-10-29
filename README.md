# AI Legal Clue Finder ⚖️🔍

A complete, production-conscious web application designed for lawyers and legal professionals to analyze legal documents, detect internal inconsistencies, identify potentially important clues, extract foundational facts, surface unanswered questions, and generate verifiable, evidence-based investigation reports.

Powered by server-side **Groq AI** (`llama-3.3-70b-versatile`) and built with Next.js App Router, TypeScript, Tailwind CSS, `unpdf`, and `pdf-lib`.

---

## 🌟 Key Capabilities

1. **Potential Clue Detection**: Identifies subtle transactional details, qualification clauses, timeline anomalies, and critical facts requiring corroboration.
2. **Inconsistency Analysis**: Pinpoints internal contradictions between separate pages and clauses while presenting alternative benign explanations for objective evaluation.
3. **Important Fact Extraction**: Extracts core facts directly stated in the text, tied to exact 1-based page numbers.
4. **Verbatim Citation Verification**: Automated server-side algorithm checks every AI quotation against the extracted text of the cited page, badging verified source text and flagging discrepancies.
5. **Interactive Document Source Inspector**: Click any cited page to view the page text in a side drawer with the exact quotation highlighted.
6. **Downloadable PDF Investigation Reports**: Generates professional, multi-page PDF reports with executive summaries, findings, verbatim citations, analytical limitations, and legal disclaimers.
7. **Two Analysis Modes**:
   - **Quick Review**: Fast initial triage focusing on document summary, key facts, and high-level clues.
   - **Detailed Comprehensive Review**: Exhaustive inquiry covering inconsistencies, alternative explanations, information gaps, and strategic deposition questions.
8. **Privacy-Conscious Zero-Database Architecture**: No database is used. Files are processed strictly in ephemeral memory and discarded immediately after HTTP response delivery.

---

## 🛠️ Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide React icons.
- **Backend**: Next.js Route Handlers (`app/api/analyze`, `app/api/report`) on the Node.js runtime.
- **AI Engine**: Groq API using the official `groq-sdk` with structured JSON output and low-temperature inference.
- **PDF Extraction**: Serverless-compatible `unpdf` preserving 1-based page numbering.
- **PDF Report Generation**: `pdf-lib` for client-downloadable PDF reports without native binaries.
- **Validation**: Strict schema validation via `zod`.
- **Testing**: Automated test suite with `vitest`.

---

## 🔒 Security & Privacy Guarantees

- **No Permanent Storage**: No PostgreSQL, MongoDB, Prisma, Redis, or permanent file storage.
- **Server-Only API Key**: `GROQ_API_KEY` is loaded exclusively in server-side Route Handlers. Never exposed to browser bundles.
- **Content Security**: Security headers enforced (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).
- **Input Boundaries**: Max file size 8 MB; maximum page count 50 pages; magic byte header validation (`%PDF-`); scanned/image-only PDF detection.
- **No HTML Injection**: Extracted text and quotations are sanitized and rendered as pure text nodes to prevent XSS.

---

## ⚙️ Environment Variables

Create a `.env.local` file in the root directory (see `.env.example`):

```bash
# Groq API Key (Obtain from https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Groq Model (Optional, defaults to llama-3.3-70b-versatile)
GROQ_MODEL=llama-3.3-70b-versatile
```

Supported Groq models:
- `llama-3.3-70b-versatile` (Recommended default)
- `llama-3.1-70b-versatile`
- `llama3-70b-8192`
- `mixtral-8x7b-32768`

---

## 🚀 Local Development Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env.local` and add your Groq API key:
```bash
cp .env.example .env.local
```
Edit `.env.local` to insert your valid `GROQ_API_KEY`.

### 3. Generate Test Fixtures (Optional)
Generate fictional legal test PDFs:
```bash
node scripts/create-fixtures.js
```
Fixtures created in `fixtures/`:
- `short_text.pdf`: 1-page sample agreement
- `contradictory_statements.pdf`: 3-page lease with conflicting rents and dates
- `multipage_deposition.pdf`: 5-page witness deposition
- `scanned_image_only.pdf`: Scanned image test file for OCR rejection validation

### 4. Run Automated Tests
```bash
npm test
```
Runs 21 automated tests across 7 test suites:
- PDF signature and size validation
- Page count limits (50-page cap)
- Text extraction and 1-based page indexing
- AI response schema validation (Zod)
- Source quote verification & bounding
- API route handlers (`/api/analyze`, `/api/report`)
- PDF report generation

### 5. Start the Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 6. Build for Production
```bash
npm run build
npm start
```

---

## ☁️ Deployment to Vercel

The application is structured specifically for zero-configuration deployment on Vercel:

### Step 1: Push Repository to GitHub / GitLab
```bash
git add -A
git commit -m "Complete AI Legal Clue Finder application"
git push origin main
```

### Step 2: Import into Vercel
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New... > Project** and select your repository.
3. Keep default build preset: **Next.js**.

### Step 3: Configure Environment Variables in Vercel
In the Vercel project configuration under **Environment Variables**, add:
- `GROQ_API_KEY`: Your real Groq API key (`gsk_...`)
- `GROQ_MODEL`: `llama-3.3-70b-versatile` (or your preferred Groq model)

### Step 4: Deploy
Click **Deploy**. Vercel will run `npm run build` and launch the application on a global edge/serverless network.

### Step 5: Updating Environment Variables
If you change `GROQ_API_KEY` or `GROQ_MODEL` in Vercel project settings, trigger a **Redeploy** from the Vercel Deployments dashboard for the new environment variables to take effect.

---

## ⚖️ Legal & Analytical Disclaimer

This tool assists with preliminary document review. AI-generated findings may be incomplete or incorrect and must be verified against original documents. This software does not provide formal legal advice, does not establish guilt or fraud, does not replace professional legal judgment, and does not guarantee that a lawyer will win a case.

