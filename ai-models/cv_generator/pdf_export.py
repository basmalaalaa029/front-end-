"""Markdown-to-PDF export using ReportLab + optional Mistune."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from cv_agent.app.config import _MISTUNE_AVAILABLE, _REPORTLAB_AVAILABLE


def md_to_rl(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    return text


def _require_reportlab() -> None:
    if not _REPORTLAB_AVAILABLE:
        raise ImportError("PDF export requires reportlab: pip install reportlab")


def _build_pdf_styles() -> Dict[str, Any]:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    c_ink = colors.HexColor("#1e293b")
    c_name = colors.HexColor("#0f172a")
    c_blue = colors.HexColor("#2563eb")
    c_rule = colors.HexColor("#cbd5e1")
    c_gray = colors.HexColor("#475569")
    base = getSampleStyleSheet()["Normal"]
    return {
        "name": ParagraphStyle(
            "s_name", parent=base, fontName="Helvetica-Bold", fontSize=26,
            leading=30, textColor=c_name, spaceAfter=4, alignment=1,
        ),
        "contact": ParagraphStyle(
            "s_contact", parent=base, fontName="Helvetica", fontSize=10,
            leading=14, textColor=c_gray, spaceAfter=12, alignment=1,
        ),
        "section": ParagraphStyle(
            "s_section", parent=base, fontName="Helvetica-Bold", fontSize=14,
            leading=18, textColor=c_blue, spaceBefore=14, spaceAfter=4,
        ),
        "sub": ParagraphStyle(
            "s_sub", parent=base, fontName="Helvetica-Bold", fontSize=11.5,
            leading=16, textColor=c_name, spaceBefore=8, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "s_body", parent=base, fontName="Helvetica", fontSize=10,
            leading=14, textColor=c_ink, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "s_bullet", parent=base, fontName="Helvetica", fontSize=10,
            leading=14, textColor=c_ink, leftIndent=15, firstLineIndent=-10, spaceAfter=3,
        ),
        "_C_BLUE": c_blue,
        "_C_RULE": c_rule,
    }


def _story_from_mistune(md_text: str, styles: Dict[str, Any]) -> list:
    import mistune
    from reportlab.platypus import HRFlowable, Paragraph, Spacer

    c_blue, c_rule = styles["_C_BLUE"], styles["_C_RULE"]
    md = mistune.create_markdown(renderer="ast")
    ast = md(md_text)
    story: list = []
    after_name = False

    def _inline_to_text(children):
        out = ""
        for child in children:
            raw = child.get("raw", "")
            ch = child.get("children", [])
            t = child.get("type", "")
            if t == "strong":
                out += f"<b>{_inline_to_text(ch)}</b>"
            elif t == "emphasis":
                out += f"<i>{_inline_to_text(ch)}</i>"
            elif t == "codespan":
                out += f"<font name='Courier'>{md_to_rl(raw)}</font>"
            else:
                out += md_to_rl(raw or "".join(c.get("raw", "") for c in ch))
        return out

    def _token_to_flowables(token):
        nonlocal after_name
        t = token.get("type", "")
        ch = token.get("children", [])
        if t == "heading":
            level = token.get("attrs", {}).get("level", 2)
            text = _inline_to_text(ch)
            if level == 1:
                story.append(Paragraph(text, styles["name"]))
                story.append(Spacer(1, 6))
                after_name = True
            elif level == 2:
                story.append(Spacer(1, 6))
                story.append(Paragraph(text.upper(), styles["section"]))
                story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))
                after_name = False
            else:
                story.append(Spacer(1, 4))
                story.append(Paragraph(text, styles["sub"]))
                after_name = False
        elif t == "paragraph":
            text = _inline_to_text(ch)
            if text.strip():
                if after_name:
                    story.append(Paragraph(text, styles["contact"]))
                    after_name = False
                else:
                    story.append(Paragraph(text, styles["body"]))
            else:
                story.append(Spacer(1, 3))
        elif t == "list":
            after_name = False
            for item in ch:
                for sub in item.get("children", []):
                    item_text = _inline_to_text(sub.get("children", []))
                    if item_text.strip():
                        story.append(Paragraph(f"• {item_text}", styles["bullet"]))
        elif t == "block_code":
            after_name = False
            story.append(Paragraph(md_to_rl(token.get("raw", "")), styles["body"]))
        elif t == "thematic_break":
            after_name = False
            story.append(HRFlowable(width="100%", thickness=0.5, color=c_rule, spaceAfter=3))
        elif t == "blank_line":
            story.append(Spacer(1, 3))
        else:
            for child in ch:
                _token_to_flowables(child)

    for token in ast:
        _token_to_flowables(token)
    return story


def _story_from_lines(md_text: str, styles: Dict[str, Any]) -> list:
    from reportlab.platypus import HRFlowable, Paragraph, Spacer

    c_blue, c_rule = styles["_C_BLUE"], styles["_C_RULE"]
    story: list = []
    after_name = False
    for line in md_text.splitlines():
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 3))
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(md_to_rl(stripped[2:]), styles["name"]))
            story.append(Spacer(1, 6))
            after_name = True
        elif stripped.startswith("## "):
            after_name = False
            story.append(Spacer(1, 6))
            story.append(Paragraph(md_to_rl(stripped[3:]).upper(), styles["section"]))
            story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceAfter=6))
        elif stripped.startswith("### "):
            after_name = False
            story.append(Spacer(1, 4))
            story.append(Paragraph(md_to_rl(stripped[4:]), styles["sub"]))
        elif stripped.startswith(("- ", "• ", "* ")):
            after_name = False
            story.append(Paragraph(f"• {md_to_rl(stripped[2:])}", styles["bullet"]))
        elif re.match(r"^\d+\.", stripped):
            after_name = False
            num_text = md_to_rl(re.sub(r"^\d+\.", "", stripped).strip())
            story.append(Paragraph(f"• {num_text}", styles["bullet"]))
        elif stripped.startswith("---"):
            after_name = False
            story.append(HRFlowable(width="100%", thickness=0.5, color=c_rule, spaceAfter=3))
        elif after_name:
            story.append(Paragraph(md_to_rl(stripped), styles["contact"]))
            after_name = False
        else:
            story.append(Paragraph(md_to_rl(stripped), styles["body"]))
    return story


def export_pdf_bytes(md_text: str, candidate_name: str = "CV") -> bytes:
    _require_reportlab()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    styles = _build_pdf_styles()
    story = _story_from_mistune(md_text, styles) if _MISTUNE_AVAILABLE else _story_from_lines(md_text, styles)
    doc.build(story)
    return buf.getvalue()


def export_pdf_file(md_text: str, candidate_name: str, out_path: str) -> None:
    pdf_bytes = export_pdf_bytes(md_text, candidate_name)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(pdf_bytes)
