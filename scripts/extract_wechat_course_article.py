#!/usr/bin/env python3
import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


BLOCK_TAGS = {"p", "h1", "h2", "h3", "li"}


def js_unescape(value: str) -> str:
    if "\\" in value:
        value = value.encode("utf-8").decode("unicode_escape")
    return html.unescape(value)


def extract_regex(pattern: str, source: str, default: str = "") -> str:
    match = re.search(pattern, source, re.S)
    return js_unescape(match.group(1)) if match else default


class WechatContentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_content = False
        self.depth = 0
        self.block_tag = None
        self.block_parts = []
        self.records = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if not self.in_content and attr.get("id") == "js_content":
            self.in_content = True
            self.depth = 1
            return

        if not self.in_content:
            return

        self.depth += 1
        if tag in BLOCK_TAGS and self.block_tag is None:
            self.block_tag = tag
            self.block_parts = []
        elif tag == "br" and self.block_tag is not None:
            self.block_parts.append("\n")
        elif tag == "img":
            src = attr.get("data-src") or attr.get("src")
            if src:
                self.images.append(src)
                self.records.append({"type": "image", "src": src})

    def handle_endtag(self, tag):
        if not self.in_content:
            return

        if tag == self.block_tag:
            text = normalize_text("".join(self.block_parts))
            if text:
                self.records.append({"type": "text", "text": text})
            self.block_tag = None
            self.block_parts = []

        self.depth -= 1
        if self.depth <= 0:
            self.in_content = False

    def handle_data(self, data):
        if self.in_content and self.block_tag is not None:
            self.block_parts.append(data)


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"[\t\r\f\v ]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    return text.strip()


def image_ext(src: str, fallback: str = "jpg") -> str:
    parsed = urlparse(src)
    query = parse_qs(parsed.query)
    fmt = (query.get("wx_fmt") or query.get("tp") or [fallback])[0].lower()
    fmt = re.sub(r"[^a-z0-9]", "", fmt)
    if fmt in {"jpeg", "jpg"}:
        return "jpg"
    if fmt in {"png", "gif", "webp"}:
        return fmt
    return fallback


def download_images(urls, assets_dir: Path, referer: str):
    assets_dir.mkdir(parents=True, exist_ok=True)
    local_map = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Referer": referer,
    }
    seen = []
    for src in urls:
        if src not in seen:
            seen.append(src)
    for index, src in enumerate(seen, 1):
        ext = image_ext(src)
        out = assets_dir / f"image-{index:02d}.{ext}"
        try:
            req = Request(src, headers=headers)
            with urlopen(req, timeout=30) as response:
                out.write_bytes(response.read())
            local_map[src] = out.name
        except Exception as exc:
            local_map[src] = ""
            print(f"image download failed: {src} ({exc})")
    return local_map


def postprocess_records(records, image_map):
    processed = []
    i = 0
    while i < len(records):
        rec = records[i]
        if rec["type"] == "image":
            filename = image_map.get(rec["src"], "")
            processed.append({"type": "image", "path": f"assets/{filename}" if filename else "", "src": rec["src"]})
            i += 1
            continue

        text = rec["text"]
        if re.fullmatch(r"(导语|结语)#?", text):
            processed.append({"type": "heading", "level": 2, "text": text.rstrip("#")})
            i += 1
            continue

        number = re.fullmatch(r"(\d{2})#?", text)
        if number:
            title = ""
            if i + 1 < len(records) and records[i + 1]["type"] == "text":
                title = records[i + 1]["text"]
                i += 1
            processed.append({"type": "heading", "level": 2, "text": f"{number.group(1)} {title}".strip()})
            i += 1
            continue

        if text == "下期预告":
            processed.append({"type": "heading", "level": 2, "text": text})
            i += 1
            continue

        if text == "Next in Series":
            processed.append({"type": "note", "text": text})
            i += 1
            continue

        processed.append({"type": "paragraph", "text": text})
        i += 1
    return processed


def md_escape(text: str) -> str:
    return text.replace("\n", "  \n")


def write_markdown(path: Path, metadata, records, include_images: bool):
    lines = [
        f"# {metadata['title']}",
        "",
        f"- 公众号：{metadata['account']}",
        f"- 发布时间：{metadata['published_at']}",
        f"- 原文链接：{metadata['source_url']}",
        "",
    ]
    for rec in records:
        if rec["type"] == "heading":
            lines.extend([f"{'#' * rec['level']} {rec['text']}", ""])
        elif rec["type"] == "paragraph":
            lines.extend([md_escape(rec["text"]), ""])
        elif rec["type"] == "note":
            lines.extend([f"> {md_escape(rec['text'])}", ""])
        elif rec["type"] == "image" and include_images:
            alt = f"图 {len([r for r in records[:records.index(rec) + 1] if r['type'] == 'image']):02d}"
            if rec["path"]:
                lines.extend([f"![{alt}]({rec['path']})", ""])
            else:
                lines.extend([f"[{alt}]({rec['src']})", ""])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_print_html(path: Path, metadata, records, include_images: bool):
    css = """
@page { size: A4; margin: 14mm 13mm 16mm; }
body {
  color: #111;
  font-family: "Songti SC", "STSong", "Noto Serif CJK SC", serif;
  font-size: 10.2pt;
  line-height: 1.56;
}
main { max-width: 760px; margin: 0 auto; }
h1 {
  font-family: "Heiti SC", "PingFang SC", sans-serif;
  font-size: 20pt;
  line-height: 1.25;
  margin: 0 0 7mm;
  text-align: center;
}
.meta {
  color: #555;
  font-size: 8.6pt;
  line-height: 1.45;
  margin: 0 0 8mm;
  text-align: center;
}
h2 {
  break-after: avoid;
  font-family: "Heiti SC", "PingFang SC", sans-serif;
  font-size: 13pt;
  line-height: 1.35;
  margin: 7mm 0 2mm;
  border-bottom: 0.4pt solid #999;
  padding-bottom: 1mm;
}
p { margin: 0 0 3.2mm; text-align: justify; }
blockquote { color: #444; margin: 0 0 3mm 0; font-size: 9pt; }
img { display: block; max-width: 100%; margin: 4mm auto; break-inside: avoid; }
.source { color: #666; font-size: 8pt; margin-top: 8mm; }
""".strip()
    parts = [
        "<!doctype html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{html.escape(metadata['title'])}</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body><main>",
        f"<h1>{html.escape(metadata['title'])}</h1>",
        '<div class="meta">',
        f"{html.escape(metadata['account'])}<br>",
        f"{html.escape(metadata['published_at'])}",
        "</div>",
    ]
    for rec in records:
        if rec["type"] == "heading":
            parts.append(f"<h{rec['level']}>{html.escape(rec['text'])}</h{rec['level']}>")
        elif rec["type"] == "paragraph":
            parts.append(f"<p>{html.escape(rec['text']).replace(chr(10), '<br>')}</p>")
        elif rec["type"] == "note":
            parts.append(f"<blockquote>{html.escape(rec['text'])}</blockquote>")
        elif rec["type"] == "image" and include_images and rec["path"]:
            parts.append(f'<img src="{html.escape(rec["path"])}" alt="">')
    parts.extend([
        f'<p class="source">原文链接：{html.escape(metadata["source_url"])}</p>',
        "</main></body></html>",
    ])
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-html", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--lesson", required=True)
    args = parser.parse_args()

    input_html = Path(args.input_html).resolve()
    output_dir = Path(args.output_dir).resolve()
    lesson_dir = output_dir / f"lesson-{int(args.lesson):02d}"
    assets_dir = lesson_dir / "assets"
    lesson_dir.mkdir(parents=True, exist_ok=True)

    source = input_html.read_text(encoding="utf-8", errors="ignore")
    parser_obj = WechatContentParser()
    parser_obj.feed(source)

    title = extract_regex(r"var msg_title = '(.+?)'\.html", source)
    account = extract_regex(r'var nickname = htmlDecode\("(.+?)"\);', source)
    description = extract_regex(r'var msg_desc = htmlDecode\("(.+?)"\);', source)
    timestamp_raw = extract_regex(r'var ct = "(\d+)";', source)
    published_at = ""
    if timestamp_raw:
        published_at = dt.datetime.fromtimestamp(int(timestamp_raw)).strftime("%Y-%m-%d %H:%M:%S")

    image_map = download_images(parser_obj.images, assets_dir, args.source_url)
    records = postprocess_records(parser_obj.records, image_map)
    text_chars = sum(len(rec.get("text", "")) for rec in records if rec["type"] in {"heading", "paragraph", "note"})

    metadata = {
        "lesson": int(args.lesson),
        "title": title,
        "account": account,
        "description": description,
        "published_at": published_at,
        "source_url": args.source_url,
        "text_chars": text_chars,
        "image_count": len([name for name in image_map.values() if name]),
    }

    shutil.copy2(input_html, lesson_dir / "original.html")
    (lesson_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(lesson_dir / "article.md", metadata, records, include_images=True)
    write_markdown(lesson_dir / "article-print.md", metadata, records, include_images=False)
    write_print_html(lesson_dir / "printable.html", metadata, records, include_images=False)
    write_print_html(lesson_dir / "printable-with-images.html", metadata, records, include_images=True)

    index = output_dir / "course-index.md"
    if not index.exists():
        index.write_text(
            "# 红果短剧创作服务平台｜短剧编剧第一课系列\n\n"
            "| 课次 | 标题 | 公众号 | 发布时间 | 本地目录 | 原文链接 |\n"
            "| --- | --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )
    row = f"| {int(args.lesson):02d} | {title} | {account} | {published_at} | lesson-{int(args.lesson):02d} | {args.source_url} |\n"
    existing = index.read_text(encoding="utf-8")
    existing = re.sub(rf"^\| {int(args.lesson):02d} \|.*\n", "", existing, flags=re.M)
    index.write_text(existing.rstrip() + "\n" + row, encoding="utf-8")

    readme = output_dir / "README.md"
    readme.write_text(
        "# 红果官方编辑课整理\n\n"
        "这个目录用于持续收集「红果短剧创作服务平台」的短剧编剧课程文章。\n\n"
        "第 01 期正文中写明「短剧编剧第一课」系列课程计划 10 期访谈，后续建议继续按 `lesson-02` 到 `lesson-10` 追加。\n\n"
        "## 目录结构\n\n"
        "- `course-index.md`：系列索引，后续课程继续追加到这里。\n"
        "- `lesson-XX/original.html`：微信原始页面源码存档。\n"
        "- `lesson-XX/article.md`：带本地图片引用的整理版 Markdown。\n"
        "- `lesson-XX/article-print.md`：正文优先的打印源 Markdown。\n"
        "- `lesson-XX/printable.html`：正文优先的 A4 打印 HTML。\n"
        "- `lesson-XX/printable-with-images.html`：带本地图片的打印 HTML。\n"
        "- `lesson-XX/printable.pdf`：A4 紧凑打印 PDF，如果已生成。\n\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "lesson_dir": str(lesson_dir), **metadata}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
