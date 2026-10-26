import html

import streamlit as st
import streamlit.components.v1 as components


def render_knowledge_map(question, passages, max_nodes=5):
    """Render an animated, responsive map connecting a question to PDF evidence."""
    passages = list(passages or [])[:max_nodes]
    if not passages:
        return

    def fields(passage):
        if isinstance(passage, dict):
            text = passage.get("text") or passage.get("content") or passage.get("page_content") or ""
            page = passage.get("page") or passage.get("page_number") or "?"
            filename = passage.get("filename") or passage.get("source") or "Regulations PDF"
        else:
            text, page, filename = str(passage), "?", "Regulations PDF"
        filename = str(filename).replace("\\", "/").split("/")[-1]
        return str(text), str(page), filename

    positions = [(345, 65), (545, 125), (535, 260), (345, 310), (150, 220)]
    safe_question = html.escape(str(question)[:66])
    edges, nodes = [], []

    for index, passage in enumerate(passages):
        excerpt, page, filename = fields(passage)
        x, y = positions[index]
        safe_name = html.escape(filename[:22])
        safe_page = html.escape(f"PAGE {page}")
        safe_excerpt = html.escape(excerpt[:220])
        dx, dy = x - 345, y - 185
        curve = f"M345 185 Q{345 + dx * .5:.1f} {185 + dy * .35:.1f} {x} {y}"

        edges.append(
            f"""
<path class="edge" d="{curve}"/>
<circle class="particle" r="3.5">
  <animateMotion dur="{3 + index * .45}s" repeatCount="indefinite" path="{curve}"/>
</circle>
"""
        )
        nodes.append(
            f"""
<g class="source-node" tabindex="0" role="group" aria-label="{safe_name}, page {safe_page}">
  <circle class="halo" cx="{x}" cy="{y}" r="29"/>
  <circle class="node" cx="{x}" cy="{y}" r="21"/>
  <path class="doc" d="M{x-7} {y-10} h10 l5 5 v16 h-15 z M{x+3} {y-10} v5 h5 M{x-4} {y+1} h9 M{x-4} {y+5} h9"/>
  <text class="filename" x="{x}" y="{y+41}" text-anchor="middle">{safe_name}</text>
  <text class="page" x="{x}" y="{y+54}" text-anchor="middle">{safe_page}</text>
  <title>{safe_excerpt}</title>
</g>
"""
        )

    svg = f"""
<svg viewBox="0 0 690 365" role="img" aria-label="Question linked to retrieved regulation evidence">
  <defs>
    <pattern id="campus-grid" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="1" cy="1" r="1" fill="#9bb4d0" opacity=".32"/>
    </pattern>
    <radialGradient id="campus-glow">
      <stop stop-color="#6f95bd" stop-opacity=".20"/>
      <stop offset="1" stop-color="#6f95bd" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="690" height="365" fill="url(#campus-grid)"/>
  <circle cx="345" cy="185" r="100" fill="url(#campus-glow)"/>
  {''.join(edges)}
  <circle class="ring ring1" cx="345" cy="185" r="48"/>
  <circle class="ring ring2" cx="345" cy="185" r="39"/>
  <circle class="core" cx="345" cy="185" r="31"/>
  <text class="qicon" x="345" y="192" text-anchor="middle">?</text>
  <text class="qtitle" x="345" y="249" text-anchor="middle">YOUR QUESTION</text>
  <text class="qtext" x="345" y="266" text-anchor="middle">{safe_question}</text>
  {''.join(nodes)}
</svg>
"""

    css = """
<style>
html,body{margin:0;padding:0;background:transparent;font-family:system-ui,sans-serif}
.panel{border:1px solid #e1e8f0;border-radius:15px;overflow:hidden;background:linear-gradient(145deg,#fff,#f5f8fc)}
.heading{padding:13px 17px 0;display:flex;justify-content:space-between;gap:8px;color:#29496e;font-size:13px;font-weight:750}
.heading small{color:#718096;font-size:11px;font-weight:600}
svg{display:block;width:100%;height:auto}
.edge{fill:none;stroke:#7c9fc4;stroke-width:1.6;stroke-dasharray:5 7;animation:dash 10s linear infinite;opacity:.75}
.particle{fill:#b58a48}
.ring{fill:none;stroke:#7195bb;stroke-dasharray:4 6;transform-origin:345px 185px}
.ring1{animation:spin 10s linear infinite}
.ring2{animation:spin 14s linear infinite reverse;opacity:.55}
.core{fill:#fff;stroke:#547ca8;stroke-width:2}
.qicon{fill:#315b91;font-size:27px;font-weight:800}
.qtitle{fill:#52779f;font-size:9px;font-weight:800;letter-spacing:2px}
.qtext{fill:#263f5d;font-size:10px;font-weight:650}
.halo{fill:#dce8f533;stroke:#a8bfd688;animation:pulse 3s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.node{fill:#fff;stroke:#b7cadd;stroke-width:1.5}
.doc{fill:none;stroke:#547ca8;stroke-width:1.5;stroke-linejoin:round}
.filename{fill:#29496e;font-size:10px;font-weight:700}
.page{fill:#718096;font-size:9px;letter-spacing:1px}
.source-node{cursor:help;outline:none}
.source-node:hover .node,.source-node:focus .node{stroke:#b58a48;stroke-width:3}
.source-node:hover .halo,.source-node:focus .halo{stroke:#b58a48}
@keyframes dash{to{stroke-dashoffset:-150}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{transform:scale(.92);opacity:.6}50%{transform:scale(1.12);opacity:1}}
@media(max-width:520px){.heading{font-size:12px} .filename{font-size:9px} .page{font-size:8px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
</style>
"""

    st.markdown(
        f'<div class="panel"><div class="heading">'
        f'<span>Knowledge map</span>'
        f'<small>{len(passages)} evidence connections</small></div></div>',
        unsafe_allow_html=True,
    )
    components.html(css + svg, height=385, scrolling=False)

    with st.expander("Inspect retrieved evidence"):
        for index, passage in enumerate(passages, 1):
            excerpt, page, filename = fields(passage)
            st.markdown(f"**{index}. {filename} — page {page}**")
            st.caption(excerpt[:500])
