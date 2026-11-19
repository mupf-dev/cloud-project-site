#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 cloud-project contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Statischer Generator für die cloud-project-Website.

Nur Python-Standardbibliothek. Liest content/seiten/*.md und content/doku/*.md,
rendert eine kleine Markdown-Teilmenge nach HTML und schreibt nach docs/
(GitHub Pages: „Deploy from a branch“, main, /docs).

Aufruf:  python3 build.py            # baut nach docs/
         python3 build.py --out DIR  # anderes Zielverzeichnis
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"

SITE_TITLE = "cloud-project"

# Hauptnavigation: (Datei, Beschriftung)
NAV = [
    ("index.html", "Start"),
    ("funktionen.html", "Funktionen"),
    ("architektur.html", "Architektur"),
    ("doku/index.html", "Dokumentation"),
    ("roadmap.html", "Status & Roadmap"),
    ("mitmachen.html", "Mitmachen"),
]

GROUPS = [
    ("konzept", "Konzepte und Architekturentscheidungen"),
    ("prozess", "Prozesse"),
]


# --------------------------------------------------------------------------- Markdown

def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).lower()
    repl = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    for k, v in repl.items():
        text = text.replace(k, v)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "abschnitt"


_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])")


def inline(text: str, link_fix=None) -> str:
    """Inline-Markdown → HTML (Code, Links, fett, kursiv). Text wird escaped."""
    codes: list[str] = []

    def keep_code(m):
        codes.append("<code>" + html.escape(m.group(1), quote=False) + "</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = _INLINE_CODE.sub(keep_code, text)
    links: list[tuple[str, str]] = []

    def keep_link(m):
        links.append((m.group(1), m.group(2)))
        return f"\x01{len(links) - 1}\x01"

    text = _LINK.sub(keep_link, text)
    text = html.escape(text, quote=False)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)

    def put_link(m):
        label, href = links[int(m.group(1))]
        if link_fix:
            href = link_fix(href)
        ext = href.startswith("http")
        attrs = ' rel="noopener"' if ext else ""
        return f'<a href="{html.escape(href)}"{attrs}>{inline(label)}</a>'

    text = re.sub(r"\x01(\d+)\x01", put_link, text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)
    return text


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # Pipes in Inline-Code nicht trennen
    cells, cur, in_code = [], "", False
    for ch in line:
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def render_md(src: str, link_fix=None, toc: list | None = None) -> str:
    lines = src.split("\n")
    out: list[str] = []
    i = 0
    used_ids: set[str] = set()

    def il(t):
        return inline(t, link_fix)

    def is_block_start(ln: str) -> bool:
        s = ln.lstrip()
        return (
            s.startswith("#") or s.startswith("```") or s.startswith(">")
            or s.startswith("|") or s.startswith(":::")
            or re.match(r"^\s*([-*]|\d+\.)\s+", ln) is not None
        )

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        # Rohes HTML-Block (für Diagramme): ::: html … :::
        if s.startswith(":::html") or s == "::: html":
            i += 1
            buf = []
            while i < len(lines) and lines[i].strip() != ":::":
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("\n".join(buf))
            continue
        # Code-Block
        if s.startswith("```"):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            if lang == "mermaid":
                continue  # Mermaid wird nicht gerendert (kein externes JS)
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            label = f'<span class="code-lang">{html.escape(lang)}</span>' if lang else ""
            out.append(f"<pre>{label}<code{cls}>" + html.escape("\n".join(buf), quote=False) + "</code></pre>")
            continue
        # Überschrift
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            level = max(2, len(m.group(1)))
            title = m.group(2).strip()
            hid = slugify(title)
            base, n = hid, 2
            while hid in used_ids:
                hid = f"{base}-{n}"
                n += 1
            used_ids.add(hid)
            if toc is not None and level == 2:
                toc.append((hid, re.sub(r"<[^>]+>", "", il(title))))
            out.append(f'<h{level} id="{hid}">{il(title)}<a class="anchor" href="#{hid}" aria-label="Link zu diesem Abschnitt">#</a></h{level}>')
            i += 1
            continue
        # Trennlinie
        if re.match(r"^(-{3,}|\*{3,})$", s):
            i += 1
            continue
        # Zitat / Hinweis
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append('<blockquote>' + render_md("\n".join(buf), link_fix) + "</blockquote>")
            continue
        # Tabelle
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            head = split_row(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            t = ['<div class="table-wrap"><table><thead><tr>']
            t += [f"<th scope=\"col\">{il(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{il(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        # Listen (eine Verschachtelungsebene)
        lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if lm:
            ordered = lm.group(2)[0].isdigit()
            start = int(lm.group(2)[:-1]) if ordered else 1
            items: list[list] = []  # [text, [subitems], sub_ordered]
            base_indent = len(lm.group(1))
            while i < len(lines):
                cur = lines[i]
                cm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", cur)
                if cm and len(cm.group(1)) <= base_indent + 1:
                    items.append([cm.group(3), [], False])
                    i += 1
                elif cm and items:
                    items[-1][1].append(cm.group(3))
                    items[-1][2] = cm.group(2)[0].isdigit()
                    i += 1
                elif cur.strip() and cur.startswith(" ") and items:
                    # Fortsetzungszeile
                    if items[-1][1]:
                        items[-1][1][-1] += " " + cur.strip()
                    else:
                        items[-1][0] += " " + cur.strip()
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            h = [f'<ol start="{start}">' if ordered and start != 1 else f"<{tag}>"]
            for text, subs, sub_ord in items:
                h.append("<li>" + il(text))
                if subs:
                    st = "ol" if sub_ord else "ul"
                    h.append(f"<{st}>" + "".join(f"<li>{il(x)}</li>" for x in subs) + f"</{st}>")
                h.append("</li>")
            h.append(f"</{tag}>")
            out.append("".join(h))
            continue
        # Absatz
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not is_block_start(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + il(" ".join(buf)) + "</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------- Inhalte

def read_page(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta: dict = {}
    if "\n---" in raw:
        head, body = raw.split("\n---", 1)
        body = body.split("\n", 1)[1] if "\n" in body else ""
        for ln in head.splitlines():
            if ":" in ln and not ln.startswith("#"):
                k, v = ln.split(":", 1)
                meta[k.strip()] = v.split("  #")[0].strip()
    else:
        body = raw
    meta["body"] = body
    meta["slug"] = path.stem
    meta.setdefault("title", path.stem)
    meta.setdefault("summary", "")
    meta["order"] = int(meta.get("order", 999))
    return meta


def plain_text(html_src: str) -> str:
    t = re.sub(r"<(script|style|svg)[\s\S]*?</\1>", " ", html_src)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------------- Layout

def layout(*, title: str, body: str, prefix: str, active: str, description: str,
           toc: list | None = None, wide: bool = False) -> str:
    nav = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        nav.append(f'<li><a href="{prefix}{href}"{cur}>{label}</a></li>')
    toc_html = ""
    if toc:
        items = "".join(f'<li><a href="#{hid}">{t}</a></li>' for hid, t in toc)
        toc_html = (
            '<nav class="toc" aria-label="Inhalt dieser Seite"><p class="toc-title">Auf dieser Seite</p>'
            f"<ol>{items}</ol></nav>"
        )
    full_title = f"{title} · {SITE_TITLE}" if title != SITE_TITLE else SITE_TITLE
    main_cls = "with-toc" if toc else ("wide" if wide else "")
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="{prefix}assets/style.css">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
<header class="site-header">
  <div class="bar">
    <a class="brand" href="{prefix}index.html" aria-label="cloud-project – Startseite">
      <img src="{prefix}assets/favicon.svg" alt="" width="28" height="28"><span>cloud-project</span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="hauptnav">Menü</button>
    <nav id="hauptnav" class="mainnav" aria-label="Hauptnavigation"><ul>{"".join(nav)}</ul></nav>
    <form class="search" role="search" action="{prefix}suche.html" method="get">
      <label for="q" class="sr-only">Suche</label>
      <input id="q" name="q" type="search" placeholder="Suchen …" autocomplete="off">
    </form>
  </div>
</header>
<div class="page {main_cls}">
{toc_html}
<main id="inhalt" tabindex="-1">
{body}
</main>
</div>
<footer class="site-footer">
  <div class="bar">
    <p>cloud-project – quelloffene, dezentrale Cloud-Plattform. Dokumentation unter
    <a href="https://creativecommons.org/licenses/by/4.0/deed.de" rel="license noopener">CC BY 4.0</a>,
    Code unter AGPL-3.0-or-later. Keine Cookies, kein Tracking, keine externen Ressourcen.</p>
    <p><a href="{prefix}mitmachen.html#lizenz">Lizenz</a> · <a href="{prefix}mitmachen.html#sicherheit">Sicherheitslücke melden</a> · <a href="{prefix}suche.html">Suche</a> · <a href="{prefix}impressum.html">Impressum</a> · <a href="{prefix}datenschutz.html">Datenschutz</a></p>
  </div>
</footer>
<script src="{prefix}assets/site.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- Bauen

def build(out: Path) -> int:
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    (out / "doku").mkdir()
    for f in STATIC.iterdir():
        if f.is_file():
            shutil.copy2(f, out / "assets" / f.name)
    (out / ".nojekyll").write_text("")

    index_entries = []
    known_doku = {p.stem for p in (CONTENT / "doku").glob("*.md") if not p.name.startswith("_")}
    problems: list[str] = []

    # Doku-Seiten
    docs = [read_page(p) for p in sorted((CONTENT / "doku").glob("*.md")) if not p.name.startswith("_")]
    docs.sort(key=lambda d: (d.get("group", "konzept") != "konzept", d["order"], d["title"]))

    def fix_doku(href: str) -> str:
        if href.startswith(("http", "#", "mailto:")):
            return href
        target = href.split("#")[0]
        if target.endswith(".html") and "/" not in target and target[:-5] not in known_doku:
            problems.append(f"Toter Link: {href}")
        return href

    for idx, d in enumerate(docs):
        toc: list = []
        body_html = render_md(d["body"], fix_doku, toc)
        group = d.get("group", "konzept")
        crumbs = (
            '<nav class="crumbs" aria-label="Brotkrumen"><a href="../index.html">Start</a> › '
            '<a href="index.html">Dokumentation</a> › <span>' + html.escape(d["title"]) + "</span></nav>"
        )
        meta_line = ""
        if d.get("quelle"):
            meta_line = f'<p class="meta">Aufbereitet aus: {html.escape(d["quelle"])}</p>'
        same = [x for x in docs if x.get("group", "konzept") == group]
        pos = same.index(d)
        pager = '<nav class="pager" aria-label="Weitere Seiten">'
        if pos > 0:
            pager += f'<a rel="prev" href="{same[pos-1]["slug"]}.html">← {html.escape(same[pos-1]["title"])}</a>'
        else:
            pager += "<span></span>"
        if pos + 1 < len(same):
            pager += f'<a rel="next" href="{same[pos+1]["slug"]}.html">{html.escape(same[pos+1]["title"])} →</a>'
        pager += "</nav>"
        body = (
            f'{crumbs}<article class="doc"><h1>{html.escape(d["title"])}</h1>'
            f'<p class="lead">{inline(d["summary"])}</p>{meta_line}{body_html}</article>{pager}'
        )
        page = layout(title=d["title"], body=body, prefix="../", active="doku/index.html",
                      description=d["summary"], toc=toc)
        (out / "doku" / f"{d['slug']}.html").write_text(page, encoding="utf-8")
        index_entries.append({
            "t": d["title"], "u": f"doku/{d['slug']}.html", "s": d["summary"],
            "h": [t for _, t in toc], "x": plain_text(body_html)[:12000],
        })

    # Doku-Übersicht
    parts = ['<h1>Dokumentation</h1><p class="lead">Aufbereitete Fassungen der Konzepte, '
             'Architekturentscheidungen (ADRs) und Prozesse von cloud-project. Die Seiten fassen die '
             'Projektdokumente für ein öffentliches Publikum zusammen.</p>']
    for gkey, glabel in GROUPS:
        items = [d for d in docs if d.get("group", "konzept") == gkey]
        if not items:
            continue
        parts.append(f'<h2 id="{gkey}">{glabel}</h2><ul class="cards">')
        for d in items:
            parts.append(
                f'<li><a href="{d["slug"]}.html"><strong>{html.escape(d["title"])}</strong>'
                f'<span>{inline(d["summary"])}</span></a></li>'
            )
        parts.append("</ul>")
    (out / "doku" / "index.html").write_text(
        layout(title="Dokumentation", body="".join(parts), prefix="../", active="doku/index.html",
               description="Konzepte, Architekturentscheidungen und Prozesse von cloud-project.", wide=True),
        encoding="utf-8")
    index_entries.append({"t": "Dokumentation", "u": "doku/index.html",
                          "s": "Übersicht aller Konzepte und Prozesse", "h": [], "x": ""})

    # Einzelseiten (Start, Funktionen, …)
    for p in sorted((CONTENT / "seiten").glob("*.md")):
        d = read_page(p)
        toc: list = [] if d.get("toc") == "ja" else None
        body_html = render_md(d["body"], fix_doku_root(known_doku, problems), toc)
        fname = f"{d['slug']}.html"
        hero = d.get("hero") == "ja"
        body = body_html if hero else f'<article class="doc"><h1>{html.escape(d["title"])}</h1><p class="lead">{inline(d["summary"])}</p>{body_html}</article>'
        title = SITE_TITLE if d["slug"] == "index" else d["title"]
        (out / fname).write_text(
            layout(title=title, body=body, prefix="", active=fname, description=d["summary"],
                   toc=toc, wide=hero), encoding="utf-8")
        if d.get("noindex") == "ja":  # Impressum/Datenschutz: nicht in die Suche
            continue
        index_entries.append({"t": d["title"], "u": fname, "s": d["summary"],
                              "h": [t for _, t in (toc or [])], "x": plain_text(body_html)[:12000]})

    # Suche
    search_body = (
        '<h1>Suche</h1><form class="bigsearch" role="search" action="suche.html" method="get">'
        '<label for="sq">Suchbegriff</label><input id="sq" name="q" type="search" autocomplete="off">'
        '<button type="submit">Suchen</button></form>'
        '<p id="search-status" role="status" aria-live="polite"></p><ol id="search-results" class="results"></ol>'
        '<noscript><p>Die Suche benötigt JavaScript. Alternativ: <a href="doku/index.html">Dokumentationsübersicht</a>.</p></noscript>'
    )
    (out / "suche.html").write_text(
        layout(title="Suche", body=search_body, prefix="", active="", description="Volltextsuche"),
        encoding="utf-8")
    (out / "suche-index.json").write_text(json.dumps(index_entries, ensure_ascii=False), encoding="utf-8")

    # 404
    (out / "404.html").write_text(layout(
        title="Seite nicht gefunden", prefix="", active="", description="404",
        body='<h1>Seite nicht gefunden</h1><p>Diese Seite gibt es nicht (mehr). Weiter zur '
             '<a href="index.html">Startseite</a> oder zur <a href="suche.html">Suche</a>.</p>'),
        encoding="utf-8")

    if problems:
        for pr in sorted(set(problems)):
            print("WARNUNG:", pr, file=sys.stderr)
        return 1
    n = len(list(out.rglob("*.html")))
    print(f"OK: {n} HTML-Seiten nach {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


def fix_doku_root(known: set, problems: list):
    def fix(href: str) -> str:
        if href.startswith(("http", "#", "mailto:")):
            return href
        target = href.split("#")[0]
        if target.startswith("doku/") and target[5:-5] not in known and target != "doku/index.html":
            problems.append(f"Toter Link: {href}")
        return href
    return fix


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "docs"))
    a = ap.parse_args()
    return build(Path(a.out).resolve())


if __name__ == "__main__":
    sys.exit(main())
