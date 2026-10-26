# CampusRules AI — SSIT

## Run locally

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

6. In the app sidebar, paste your Google AI Studio API key, leave the default model ID as `gemma-4-26b-a4b-it` (or change it if your account uses a different model), and upload your college regulation PDFs.

## Notes

- The app extracts selectable PDF text with PyMuPDF. Scanned/image-only PDFs need OCR first.
- Answers are instructed to rely only on retrieved PDF excerpts and cite them as `[Source 1]`, etc.
- Click source links to jump to excerpts; use the download control to open the original PDF.
- PDF extraction is cached by file content, the GenAI client is reused for the same API key, and retrieval uses a lightweight local TF-IDF/BM25-inspired ranker.
- The knowledge map is rendered from the passages retrieved for each answer.

## Privacy and safety

Your Google AI Studio API key is entered into the running app session and used to make model requests. Do not share the key or commit it to source control. Verify important college decisions with the college office.
