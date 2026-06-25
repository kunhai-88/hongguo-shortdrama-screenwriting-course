#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph, Spacer


BODY_FONT = "HongguoBalancedBody"
HEAD_FONT = "HongguoBalancedHead"


def register_fonts():
    font_specs = [
        (BODY_FONT, "/System/Library/Fonts/Supplemental/Songti.ttc", 6),
        (HEAD_FONT, "/System/Library/Fonts/STHeiti Medium.ttc", 0),
    ]
    for name, path, subfont in font_specs:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
                continue
            except Exception:
                pass
        pdfmetrics.registerFont(TTFont(name, "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"))


def esc(text: str) -> str:
    return html.escape(text.strip())


def clean(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text.strip()


def read_lesson_body(path: Path):
    records = []
    in_meta = True
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue
        if in_meta and line.startswith("- "):
            continue
        in_meta = False
        if line.startswith("## "):
            records.append(("h2", clean(line[3:])))
        elif line.startswith("### "):
            records.append(("h3", clean(line[4:])))
        elif line.startswith("> "):
            records.append(("quote", clean(line[2:])))
        elif line.startswith("- "):
            records.append(("bullet", clean(line[2:])))
        else:
            records.append(("p", clean(line)))
    return records


def styles():
    return {
        "course_title": ParagraphStyle(
            "course_title",
            fontName=HEAD_FONT,
            fontSize=13.2,
            leading=17,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=1.8 * mm,
            keepWithNext=True,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName=BODY_FONT,
            fontSize=7.4,
            leading=10.4,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#6b7280"),
            spaceAfter=3.0 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=HEAD_FONT,
            fontSize=10.8,
            leading=13.8,
            textColor=colors.HexColor("#111827"),
            spaceBefore=3.2 * mm,
            spaceAfter=1.1 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName=HEAD_FONT,
            fontSize=9.6,
            leading=12.4,
            textColor=colors.HexColor("#374151"),
            spaceBefore=2.0 * mm,
            spaceAfter=0.7 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=BODY_FONT,
            fontSize=9.15,
            leading=12.6,
            firstLineIndent=18.3,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#111111"),
            spaceAfter=1.15 * mm,
        ),
        "quote": ParagraphStyle(
            "quote",
            fontName=BODY_FONT,
            fontSize=8.95,
            leading=12.3,
            leftIndent=4 * mm,
            rightIndent=2 * mm,
            textColor=colors.HexColor("#374151"),
            spaceBefore=0.8 * mm,
            spaceAfter=1.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName=BODY_FONT,
            fontSize=8.95,
            leading=12.3,
            leftIndent=5 * mm,
            firstLineIndent=-2.5 * mm,
            textColor=colors.HexColor("#111111"),
            spaceAfter=0.9 * mm,
        ),
    }


class BalancedDoc(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal", topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="normal", frames=[frame], onPage=self.footer)])

    def footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(BODY_FONT, 7.2)
        canvas.setFillColor(colors.HexColor("#8a8f98"))
        canvas.drawCentredString(A4[0] / 2, 8.5 * mm, f"第 {doc.page} 页")
        canvas.restoreState()


def build(root: Path, output: Path):
    register_fonts()
    s = styles()
    metas = []
    for meta_path in sorted(root.glob("lesson-*/metadata.json")):
        metas.append(json.loads(meta_path.read_text(encoding="utf-8")))
    metas.sort(key=lambda m: int(m["lesson"]))

    story = []
    for index, meta in enumerate(metas):
        lesson = int(meta["lesson"])
        block = [
            Paragraph(esc(meta["title"]), s["course_title"]),
            Paragraph(
                f"{esc(meta['account'])} / {esc(meta['published_at'])}<br/>原文链接：{esc(meta['source_url'])}",
                s["meta"],
            ),
        ]
        if index:
            story.append(Spacer(1, 5.0 * mm))
        story.append(KeepTogether(block))
        for kind, text in read_lesson_body(root / f"lesson-{lesson:02d}" / "article-print.md"):
            if kind == "h2":
                story.append(Paragraph(esc(text), s["h2"]))
            elif kind == "h3":
                story.append(Paragraph(esc(text), s["h3"]))
            elif kind == "quote":
                story.append(Paragraph(esc(text), s["quote"]))
            elif kind == "bullet":
                story.append(Paragraph(f"• {esc(text)}", s["bullet"]))
            else:
                story.append(Paragraph(esc(text), s["body"]))

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BalancedDoc(
        str(output),
        pagesize=A4,
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=11 * mm,
        bottomMargin=13 * mm,
        title="红果短剧编剧第一课 01-10 平衡打印版",
        author="红果短剧创作服务平台",
    )
    doc.build(story)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(Path(args.root), Path(args.output))


if __name__ == "__main__":
    main()
