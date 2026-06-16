"""
MarkItDown Converter — Streamlit App
Converts PDF, DOCX, XLSX, PPTX and other files to Markdown.
Includes a note editor that renders notes as Markdown live.
"""

import tempfile
import os
from pathlib import Path

import streamlit as st
from markitdown import MarkItDown

st.set_page_config(page_title="MarkItDown Converter", page_icon="📄", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .file-meta {
        background: #f0f4ff;
        border-left: 4px solid #4f6ef7;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

SUPPORTED = {
    ".pdf": "PDF", ".docx": "Word", ".xlsx": "Excel", ".xls": "Excel (legacy)",
    ".pptx": "PowerPoint", ".ppt": "PowerPoint (legacy)", ".html": "HTML",
    ".htm": "HTML", ".txt": "Text", ".csv": "CSV", ".md": "Markdown",
    ".xml": "XML", ".json": "JSON", ".epub": "ePub", ".zip": "ZIP",
}
MAX_MB = 50


def convert(uploaded_file) -> tuple[str, str | None]:
    suffix = Path(uploaded_file.name).suffix.lower()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        result = MarkItDown().convert(tmp_path)
        return result.text_content, None
    except Exception as e:
        return "", f"{type(e).__name__}: {e}"
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def render_result(name: str, markdown: str):
    st.markdown(f"#### 📄 {name}")

    tab1, tab2, tab3 = st.tabs(["📖 Önizleme", "📋 Ham Markdown", "📝 Notlarım"])

    with tab1:
        with st.container(border=True):
            st.markdown(markdown)

    with tab2:
        st.text_area(
            "Ham Markdown",
            value=markdown,
            height=500,
            key=f"raw_{name}",
            label_visibility="collapsed",
        )

    with tab3:
        col_left, col_right = st.columns(2)

        with col_left:
            st.caption("✏️ Notunu yaz (Markdown destekler)")
            note = st.text_area(
                "Not",
                height=420,
                key=f"note_{name}",
                placeholder="## Başlık\n\n- madde 1\n- madde 2\n\n**kalın**, *italik*, `kod`",
                label_visibility="collapsed",
            )

        with col_right:
            st.caption("👁️ Markdown önizleme")
            with st.container(border=True, height=420):
                if note:
                    st.markdown(note)
                else:
                    st.markdown("*Solda not yazmaya başla…*")

        if note:
            st.download_button(
                "⬇️ Notu .md olarak indir",
                data=note.encode("utf-8"),
                file_name=Path(name).stem + "_not.md",
                mime="text/markdown",
                key=f"dl_note_{name}",
            )

    st.download_button(
        "⬇️ Dönüştürülen dosyayı .md olarak indir",
        data=markdown.encode("utf-8"),
        file_name=Path(name).stem + ".md",
        mime="text/markdown",
        key=f"dl_{name}",
    )
    st.divider()


def main():
    st.title("📄 MarkItDown Converter")
    st.caption("PDF, DOCX, XLSX, PPTX ve diğer dosyaları Markdown'a çevir.")

    files = st.file_uploader(
        "Dosya yükle",
        type=[k.lstrip(".") for k in SUPPORTED],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not files:
        st.info("Desteklenen formatlar: " + " · ".join(f"`{k}`" for k in SUPPORTED), icon="ℹ️")
        return

    valid, skipped = [], []
    for f in files:
        if len(f.getvalue()) > MAX_MB * 1024 * 1024:
            skipped.append(f.name)
        else:
            valid.append(f)

    if skipped:
        st.warning(f"Boyut aşımı (>{MAX_MB} MB), atlandı: " + ", ".join(skipped))

    results = []
    with st.spinner(f"{len(valid)} dosya dönüştürülüyor…"):
        for uf in valid:
            ext = Path(uf.name).suffix.lower()
            size_kb = len(uf.getvalue()) / 1024
            size_str = f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            st.markdown(
                f'<div class="file-meta">📎 <b>{uf.name}</b> &nbsp;·&nbsp; '
                f'{SUPPORTED.get(ext, "Dosya")} &nbsp;·&nbsp; {size_str}</div>',
                unsafe_allow_html=True,
            )
            md, err = convert(uf)
            if err:
                st.error(f"**{uf.name}** dönüştürülemedi: `{err}`")
            elif not md.strip():
                st.warning(f"**{uf.name}** dönüştürüldü fakat içerik boş.")
            else:
                results.append((uf.name, md))

    if results:
        st.success(f"✅ {len(results)}/{len(valid)} dosya başarıyla dönüştürüldü.")
        st.divider()
        for name, md in results:
            render_result(name, md)


if __name__ == "__main__":
    main()
