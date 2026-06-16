"""
MarkItDown Converter — Streamlit App
Converts PDF, DOCX, XLSX, PPTX and other files to Markdown
using the markitdown library.
"""

import tempfile
import os
from pathlib import Path

import streamlit as st
from markitdown import MarkItDown

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarkItDown Converter",
    page_icon="📄",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; }
        .file-info-box {
            background: #f0f4ff;
            border-left: 4px solid #4f6ef7;
            border-radius: 6px;
            padding: 0.6rem 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }
        .stTextArea textarea { font-family: 'Courier New', monospace; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constants ─────────────────────────────────────────────────────────────────
SUPPORTED_TYPES = {
    ".pdf":  "PDF Document",
    ".docx": "Word Document",
    ".xlsx": "Excel Spreadsheet",
    ".xls":  "Excel Spreadsheet (legacy)",
    ".pptx": "PowerPoint Presentation",
    ".ppt":  "PowerPoint Presentation (legacy)",
    ".html": "HTML File",
    ".htm":  "HTML File",
    ".txt":  "Plain Text",
    ".csv":  "CSV File",
    ".md":   "Markdown File",
    ".xml":  "XML File",
    ".json": "JSON File",
}
MAX_FILE_SIZE_MB = 50


# ── Core conversion ───────────────────────────────────────────────────────────
def convert_to_markdown(uploaded_file) -> tuple[str, str | None]:
    """
    Convert an uploaded Streamlit file to Markdown text.

    Returns:
        (markdown_text, error_message) — one of which will be None.
    """
    suffix = Path(uploaded_file.name).suffix.lower()

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        md = MarkItDown()
        result = md.convert(tmp_path)
        return result.text_content, None

    except Exception as exc:  # noqa: BLE001
        return "", f"{type(exc).__name__}: {exc}"

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ── UI helpers ────────────────────────────────────────────────────────────────
def file_info_html(name: str, size_bytes: int, ext: str) -> str:
    kind = SUPPORTED_TYPES.get(ext, "Unknown file type")
    size_kb = size_bytes / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
    return (
        f'<div class="file-info-box">'
        f"📎 <strong>{name}</strong> &nbsp;·&nbsp; {kind} &nbsp;·&nbsp; {size_str}"
        f"</div>"
    )


def render_result(name: str, markdown: str):
    """Show preview / raw toggle and download button for one file."""
    st.markdown(f"### {name}")

    col_left, col_right = st.columns([8, 2])
    with col_right:
        view_mode = st.radio(
            "View",
            ["Preview", "Raw"],
            horizontal=True,
            key=f"view_{name}",
            label_visibility="collapsed",
        )

    if view_mode == "Preview":
        with st.container(border=True):
            st.markdown(markdown, unsafe_allow_html=False)
    else:
        st.text_area(
            "Markdown source",
            value=markdown,
            height=420,
            key=f"raw_{name}",
            label_visibility="collapsed",
        )

    st.download_button(
        label="⬇️ Download .md",
        data=markdown.encode("utf-8"),
        file_name=Path(name).stem + ".md",
        mime="text/markdown",
        key=f"dl_{name}",
    )
    st.divider()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.title("📄 MarkItDown Converter")
    st.caption(
        "Upload PDF, DOCX, XLSX, PPTX or other files — get clean Markdown back."
    )

    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        type=list({k.lstrip(".") for k in SUPPORTED_TYPES}),
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not uploaded_files:
        st.info(
            "Supported formats: "
            + ", ".join(f"`{k}`" for k in SUPPORTED_TYPES),
            icon="ℹ️",
        )
        return

    # Filter oversized files before processing
    valid, skipped = [], []
    for f in uploaded_files:
        if len(f.getvalue()) > MAX_FILE_SIZE_MB * 1024 * 1024:
            skipped.append(f.name)
        else:
            valid.append(f)

    if skipped:
        st.warning(
            f"Skipped (>{MAX_FILE_SIZE_MB} MB): " + ", ".join(skipped),
            icon="⚠️",
        )

    if not valid:
        return

    results: list[tuple[str, str]] = []

    with st.spinner(f"Converting {len(valid)} file(s)…"):
        for uf in valid:
            ext = Path(uf.name).suffix.lower()
            st.markdown(
                file_info_html(uf.name, len(uf.getvalue()), ext),
                unsafe_allow_html=True,
            )
            markdown, error = convert_to_markdown(uf)

            if error:
                st.error(f"**{uf.name}** could not be converted.\n\n`{error}`")
            elif not markdown.strip():
                st.warning(
                    f"**{uf.name}** converted but produced no text content.",
                    icon="⚠️",
                )
            else:
                results.append((uf.name, markdown))

    if not results:
        return

    st.success(
        f"✅ {len(results)} of {len(valid)} file(s) converted successfully."
    )
    st.divider()

    for name, markdown in results:
        render_result(name, markdown)


if __name__ == "__main__":
    main()