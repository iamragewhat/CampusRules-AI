import hashlib
import html
import math
import re
from collections import Counter
from functools import lru_cache

import fitz
import streamlit as st
from google import genai
from google.genai import types

from knowledge_map import render_knowledge_map


st.set_page_config(
    page_title="CampusRules AI | SSIT",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Requested default model ID. It remains editable in the sidebar.
MODEL_DEFAULT = "gemma-4-26b-a4b-it"
CHUNK_WORDS = 220
OVERLAP_WORDS = 40
RETRIEVAL_LIMIT = 5


# ------------------------------ Visual design ------------------------------
st.markdown(
    r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');
:root {
  --ink:#17243b; --navy:#172b4d; --muted:#64748b; --line:#e5eaf1;
  --paper:#fbfaf7; --white:#ffffff; --blue:#315b91; --blue-soft:#edf4fc;
  --gold:#b58a48; --shadow:0 8px 26px rgba(25,42,67,.07);
}
* { box-sizing:border-box; }
html, body, [class*="css"] { font-family:'DM Sans',system-ui,sans-serif; }
.stApp { background:linear-gradient(180deg,#fbfaf7 0%,#f5f7fa 100%); color:var(--ink); }
.block-container { max-width:1320px; padding-top:1.1rem; padding-bottom:2.8rem; }
[data-testid="stHeader"] { background:rgba(251,250,247,.92); }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
[data-testid="stSidebar"] > div { padding-top:1.2rem; }
h1,h2,h3,h4 { color:var(--navy)!important; font-family:'Manrope','DM Sans',sans-serif!important; font-weight:800!important; letter-spacing:-.025em; }
p,li,label,span,div { }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color:#26364d; line-height:1.72; }
[data-testid="stCaptionContainer"] p { color:#64748b!important; }
.topbar { display:flex; align-items:center; justify-content:space-between; gap:12px;
  padding:12px 17px; margin:0 0 19px; border:1px solid #e8edf3; border-radius:14px;
  background:rgba(255,255,255,.88); box-shadow:0 3px 14px rgba(25,42,67,.04); color:#34445b; }
.brand { font-family:'Manrope',sans-serif; color:#1d3557; font-weight:800; letter-spacing:.01em; font-size:17px; }
.topbar small { color:#718096; font-size:11px; }
.hero { position:relative; overflow:hidden; background:linear-gradient(115deg,#fff 0%,#f1f6fc 100%);
  border:1px solid #dfe8f2; border-radius:20px; padding:27px 30px; margin:0 auto 25px;
  max-width:1080px; box-shadow:var(--shadow); }
.hero:after { content:""; position:absolute; right:-65px; top:-110px; width:290px; height:290px;
  border-radius:50%; background:radial-gradient(circle,rgba(181,138,72,.13),transparent 68%); }
.hero .eyebrow { font-size:10px; letter-spacing:.17em; font-weight:800; color:#98733d; }
.hero h1 { color:#193454!important; font-size:clamp(1.9rem,4vw,3rem)!important; line-height:1.12; margin:10px 0; }
.hero p { color:#43536a!important; font-size:14px; line-height:1.75; max-width:760px; margin:0; }
.section-title { font-family:'Manrope',sans-serif; font-size:22px; font-weight:800; color:#1d3557; margin:0 0 3px; }
.section-subtitle { font-size:12px; color:#718096; margin:0 0 15px; }
.paper-card { background:#fff; border:1px solid #e2e9f1; border-radius:15px; padding:17px 19px;
  color:#26364d; box-shadow:var(--shadow); margin:10px 0 14px; }
.paper-card * { color:#26364d!important; }
.paper-card .muted { color:#64748b!important; font-size:13px; line-height:1.7; }
.badge { display:inline-block; padding:5px 9px; border-radius:999px; background:#edf4fc;
  color:#315b91; font-size:10px; font-weight:800; letter-spacing:.08em; border:1px solid #d8e6f5; }
.doc-card { background:#fff; border:1px solid #e2e9f1; border-radius:12px; padding:13px 15px;
  margin:9px 0; box-shadow:0 4px 14px rgba(25,42,67,.04); overflow-wrap:anywhere; }
.doc-card b { color:#203a5c!important; font-size:13px; }
.doc-card p { font-size:11px; color:#64748b!important; margin:5px 0 0; }
.stButton > button { border:1px solid #d4dfeb!important; border-radius:10px!important;
  background:linear-gradient(180deg,#fff,#f4f7fb)!important; color:#203a5c!important;
  font-weight:700!important; min-height:40px; transition:transform .16s ease,box-shadow .16s ease!important; }
.stButton > button:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(25,42,67,.10)!important; border-color:#9db8d7!important; }
.stTextInput input,.stTextArea textarea { background:#fff!important; color:#17243b!important;
  border:1px solid #d8e1eb!important; border-radius:9px!important; }
.stTextInput input:focus,.stTextArea textarea:focus { border-color:#6d91bb!important; box-shadow:0 0 0 2px #dce9f7!important; }
[data-testid="stFileUploader"] { background:#fff; border:1px dashed #b9cadd; border-radius:12px; padding:9px; }
[data-testid="stFileUploader"] * { color:#26364d!important; }
[data-testid="stChatMessage"] { background:#fff!important; border:1px solid #e3eaf2!important;
  border-radius:14px!important; padding:14px!important; margin-bottom:12px!important;
  box-shadow:0 4px 16px rgba(25,42,67,.045); }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] li { line-height:1.78; color:#26364d!important; }
[data-testid="stChatInput"] { background:#fff!important; border:1px solid #d5e0eb!important; border-radius:13px!important; }
[data-testid="stChatInput"] textarea { color:#17243b!important; -webkit-text-fill-color:#17243b!important; }
[data-testid="stChatInput"] textarea::placeholder { color:#8190a3!important; -webkit-text-fill-color:#8190a3!important; }
[data-testid="stExpander"] { border:1px solid #e1e8f0!important; border-radius:11px!important; background:#fff!important; }
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p { color:#243b5a!important; font-weight:700!important; }
.citation { background:#f8fbff; border:1px solid #d9e6f3; border-radius:10px; padding:12px;
  margin:8px 0; color:#26364d; scroll-margin-top:80px; }
.citation h4 { font-family:'DM Sans',sans-serif!important; font-size:13px; color:#24476f!important; margin:0 0 7px; }
.citation p { font-size:12px; color:#35465d!important; line-height:1.75; margin:0; white-space:pre-wrap; }
.cite-link { display:inline-block; border:1px solid #cbdced; border-radius:7px; padding:5px 8px;
  margin:3px 5px 3px 0; background:#f3f8fd; color:#28517f!important; font-size:11px; font-weight:800; text-decoration:none!important; }
.cite-link:hover { background:#e7f1fb; border-color:#8eafd1; }
.status { font-size:12px; color:#536780; padding:7px 0; }
.stProgress > div > div > div { background:linear-gradient(90deg,#527eae,#9ab9d9); }
hr { border-color:#e5eaf1!important; }
@keyframes fadeUp { from {opacity:0;transform:translateY(7px)} to {opacity:1;transform:translateY(0)} }
@media(max-width:800px) {
  .block-container { padding:.55rem .75rem 2rem; }
  .hero { padding:19px 17px; border-radius:15px; margin-bottom:17px; }
  .hero p { font-size:13px; }
  .topbar { padding:9px 11px; gap:7px; flex-wrap:wrap; }
  .brand { font-size:14px; }
  .section-title { font-size:19px; }
  .paper-card { padding:14px; }
}
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none!important; transition:none!important; } }
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------ PDF pipeline -------------------------------
@st.cache_data(show_spinner=False, max_entries=12)
def extract_pages_cached(file_payloads):
    """Parse PDF bytes once per unique upload set; keep only text and page metadata."""
    pages = []
    for filename, data in file_payloads:
        try:
            with fitz.open(stream=data, filetype="pdf") as document:
                for page_number, page in enumerate(document, start=1):
                    page_text = page.get_text("text").strip()
                    if page_text:
                        pages.append({
                            "source": filename,
                            "page": page_number,
                            "text": page_text,
                        })
        except Exception as exc:
            pages.append({
                "source": filename,
                "page": 0,
                "text": "",
                "error": str(exc),
            })
    return pages


def make_chunks(pages):
    chunks = []
    step = max(1, CHUNK_WORDS - OVERLAP_WORDS)
    for page in pages:
        words = page["text"].split()
        for start in range(0, len(words), step):
            excerpt = " ".join(words[start:start + CHUNK_WORDS])
            if not excerpt:
                continue
            tokens = tokenize(excerpt)
            chunks.append({
                "source": page["source"],
                "page": page["page"],
                "text": excerpt,
                "_terms": dict(Counter(tokens)),
            })
            if start + CHUNK_WORDS >= len(words):
                break
    return chunks


def tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def retrieve(question, chunks, limit=RETRIEVAL_LIMIT):
    """Lightweight TF-IDF/BM25-inspired ranking; no embeddings or extra dependency."""
    query_terms = Counter(tokenize(question))
    if not query_terms or not chunks:
        return []

    doc_count = len(chunks)
    document_frequency = Counter()
    for chunk in chunks:
        terms = chunk.get("_terms") or dict(Counter(tokenize(chunk["text"])))
        document_frequency.update(terms.keys())

    scored = []
    query_phrase = " ".join(tokenize(question))
    for chunk in chunks:
        terms = chunk.get("_terms") or dict(Counter(tokenize(chunk["text"])))
        doc_length = max(sum(terms.values()), 1)
        score = 0.0
        matched = 0
        for term, q_count in query_terms.items():
            tf = terms.get(term, 0)
            if tf:
                matched += 1
                idf = math.log(1 + (doc_count - document_frequency[term] + 0.5) /
                               (document_frequency[term] + 0.5))
                norm_tf = (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * doc_length / 220))
                score += idf * norm_tf * min(q_count, 2)
        coverage = matched / max(len(query_terms), 1)
        if query_phrase and query_phrase in " ".join(tokenize(chunk["text"])):
            score += 1.2
        score *= (0.65 + 0.35 * coverage)
        if score > 0:
            scored.append((chunk, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]


# ------------------------------- Gemini API --------------------------------
@st.cache_resource(show_spinner=False, max_entries=4)
def get_genai_client(api_key):
    """Reuse the Google GenAI client for the same key during this app session."""
    return genai.Client(api_key=api_key)


def stream_gemma(question, results, api_key, model):
    if not results:
        yield (
            "I couldn't find a matching passage in the uploaded PDFs. "
            "Try using wording from the regulation document, or upload a more relevant PDF."
        )
        return

    evidence = "\n\n".join(
        f"[Source {i}: {chunk['source']}, page {chunk['page']}]\n{chunk['text']}"
        for i, (chunk, _score) in enumerate(results, 1)
    )
    prompt = f"""You are CampusRules AI, a careful college-regulations assistant.
Answer the student's question using ONLY the source excerpts below.
Be clear, student-friendly, and concise. If the excerpts do not establish the answer, say so.
Do not invent policies, deadlines, fees, exceptions, or eligibility requirements.
Cite supporting evidence inline using [Source 1], [Source 2], etc.
If sources conflict or are incomplete, explicitly point that out.

SOURCE EXCERPTS:
{evidence}

STUDENT QUESTION:
{question}
"""
    client = get_genai_client(api_key)
    response_stream = client.models.generate_content_stream(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
    temperature=0.2,
    max_output_tokens=400,
    thinking_config=types.ThinkingConfig(
        thinking_level="minimal"
    ),
),
    )
    for response_chunk in response_stream:
        output = getattr(response_chunk, "text", None)
        if output:
            yield output


def citation_html(sources, message_id):
    links = []
    for index, source in enumerate(sources, 1):
        anchor = f"evidence-{message_id}-{index}"
        label = f"{source['source']} · p. {source['page']}"
        links.append(
            f'<a class="cite-link" href="#{anchor}">'
            f'Source {index}: {html.escape(label)}</a>'
        )
    return " ".join(links)


# ------------------------------- Session state ------------------------------
defaults = {
    "messages": [],
    "chunks": [],
    "signature": None,
    "pdfs": {},
    "pending_question": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------- Header -----------------------------------
st.markdown(
    """
<div class="topbar">
  <div><span class="brand">SSIT</span> &nbsp; <small>Student regulations assistant</small></div>
  <div style="text-align:right"><span class="brand">CampusRules</span><br><small>A digital assistant for SSIT</small></div>
  <div><small>AI-powered · Evidence first</small></div>
</div>
<div class="hero">
  <div class="eyebrow">YOUR DIGITAL CAMPUS COMPANION</div>
  <h1>Campus clarity.<br>Without the confusion.</h1>
  <p>Ask in plain language. Get student-friendly answers grounded in your uploaded college regulations, with clickable source references so you can verify the original document.</p>
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------------- Sidebar -----------------------------------
with st.sidebar:
    st.markdown("## CampusRules")
    st.caption("Your college handbook, made easier to understand.")
    st.markdown("### AI connection")
    api_key = st.text_input(
        "Google AI Studio API key",
        type="password",
        help="Your key is used by this app to make model requests. Do not share it.",
    )
    model = st.text_input("Model ID", value=MODEL_DEFAULT)
    st.divider()
    st.markdown("### Knowledge base")
    uploaded_files = st.file_uploader(
        "Upload college regulation PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Text-based PDFs work best. Scanned PDFs need OCR first.",
    )

    if uploaded_files:
        payloads = [(file.name, file.getvalue()) for file in uploaded_files]
        signature = tuple(
            (name, len(data), hashlib.sha256(data).hexdigest())
            for name, data in payloads
        )
        if signature != st.session_state.signature:
            with st.spinner("Reading and indexing your PDFs…"):
                pages = extract_pages_cached(tuple(payloads))
                valid_pages = [page for page in pages if page["text"]]
                st.session_state.chunks = make_chunks(valid_pages)
                st.session_state.signature = signature
                st.session_state.messages = []
                st.session_state.pdfs = {name: data for name, data in payloads}
            errors = [page for page in pages if page.get("error")]
            if st.session_state.chunks:
                st.success(
                    f"Indexed {len(valid_pages)} pages and "
                    f"{len(st.session_state.chunks)} passages."
                )
            else:
                st.error("No selectable text found. This PDF may need OCR.")
            for error_page in errors:
                st.warning(f"Could not read {error_page['source']}: {error_page['error']}")
        else:
            st.success(f"{len(st.session_state.chunks)} passages ready.")

    st.divider()
    st.markdown("### Suggested questions")
    suggestions = [
        "What is the minimum attendance requirement?",
        "What are the exam eligibility rules?",
        "What is the revaluation procedure?",
        "What is the late-fee deadline?",
    ]
    for index, suggestion in enumerate(suggestions):
        if st.button(suggestion, key=f"suggestion_{index}", use_container_width=True):
            st.session_state.pending_question = suggestion

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("PDF retrieval · Streaming answers · Verifiable sources")


# -------------------------------- Main panel --------------------------------
st.markdown(
    '<div class="section-title">Ask CampusRules</div>'
    '<div class="section-subtitle">Answers are grounded in your uploaded documents.</div>',
    unsafe_allow_html=True,
)

if not st.session_state.chunks:
    st.markdown(
        """
<div class="paper-card">
  <span class="badge">GET STARTED</span>
  <h3 style="margin-top:12px">Your campus handbook, made searchable.</h3>
  <p class="muted">Upload a college regulations PDF from the sidebar. Then ask about attendance, examinations, fees, revaluation, or any rule described in that document.</p>
</div>
""",
        unsafe_allow_html=True,
    )


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            message_id = message.get("id", "source")
            st.markdown(
                "**Sources:** " + citation_html(message["sources"], message_id),
                unsafe_allow_html=True,
            )
            with st.expander("Open source excerpts and original PDFs", expanded=True):
                for index, source in enumerate(message["sources"], 1):
                    anchor = f"evidence-{message_id}-{index}"
                    st.markdown(
                        f'<div class="citation" id="{anchor}">'
                        f'<h4>Source {index} · {html.escape(source["source"])} · '
                        f'Page {source["page"]}</h4>'
                        f'<p>{html.escape(source["text"])}</p></div>',
                        unsafe_allow_html=True,
                    )
                    pdf_data = st.session_state.pdfs.get(source["source"])
                    if pdf_data:
                        st.download_button(
                            f"Download original PDF: {source['source']}",
                            data=pdf_data,
                            file_name=source["source"],
                            mime="application/pdf",
                            key=f"download_{message_id}_{index}",
                        )

            if message.get("question"):
                render_knowledge_map(message["question"], message["sources"])


question = st.chat_input("Ask about attendance, exams, fees or revaluation…")
pending_question = st.session_state.pending_question
st.session_state.pending_question = None
active_question = question or pending_question

if active_question:
    if not st.session_state.chunks:
        st.warning("Upload a college regulation PDF first.")
    elif not api_key.strip():
        st.warning("Enter your Google AI Studio API key in the sidebar.")
    elif not model.strip():
        st.warning("Enter a model ID in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": active_question})
        with st.chat_message("user"):
            st.markdown(active_question)

        with st.chat_message("assistant"):
            status = st.empty()
            progress = st.progress(5)
            status.markdown(
                '<div class="status">Searching your college documents…</div>',
                unsafe_allow_html=True,
            )
            results = retrieve(active_question, st.session_state.chunks)
            progress.progress(25)

            source_list = [
                {
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "text": chunk["text"],
                }
                for chunk, _score in results
            ]

            status.markdown(
                '<div class="status">Collecting matching source passages…</div>',
                unsafe_allow_html=True,
            )
            progress.progress(40)
            status.markdown(
                '<div class="status">Generating your answer…</div>',
                unsafe_allow_html=True,
            )

            try:
                answer = st.write_stream(
                    stream_gemma(
                        active_question,
                        results,
                        api_key.strip(),
                        model.strip(),
                    )
                )
                answer = answer.strip() if isinstance(answer, str) else ""

                if not answer:
                    answer = "The model returned an empty answer."

            except Exception as exc:
                answer = (
                    "**I couldn't connect to the AI model.**\\n\\n"
                    f"Details: `{html.escape(str(exc))}`\\n\\n"
                    "Check the API key and Model ID in the sidebar, then try again."
                )
                st.markdown(answer)

            progress.progress(100)
            status.empty()

        message_id = hashlib.sha256(
            (active_question + answer).encode("utf-8")
        ).hexdigest()[:12]
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": source_list,
                "question": active_question,
                "id": message_id,
            }
        )
        st.rerun()


with st.expander("How to use CampusRules"):
    st.markdown(
        """
1. **Connect the AI:** Add your Google AI Studio API key in the sidebar and check the model ID.
2. **Upload documents:** Add one or more text-based college regulation PDFs.
3. **Ask a question:** Use the chat box or choose a suggested question.
4. **Check the evidence:** Select a source link to jump to its excerpt. Download the original PDF to verify the full page and context.
5. **Read the knowledge map:** See which retrieved passages were used as evidence for the answer.

**Tip:** Ask one clear question at a time. If a PDF is a scanned image, it may need OCR before its text can be searched.
"""
    )

st.markdown(
    '<p style="text-align:center;color:#718096;font-size:11px;margin-top:25px">'
    'CampusRules AI is a student project prototype, not an official college authority. '
    'Verify important decisions with your college office.</p>',
    unsafe_allow_html=True,
)
