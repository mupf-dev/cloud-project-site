#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 site-kit contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""site-kit – gemeinsamer statischer Generator der Projekt-Websites, zweisprachig (DE an der Wurzel, EN unter en/).

NICHT in den Website-Repos bearbeiten: Quelle ist das Repo site-kit, sync.py kopiert diese Datei nach kit/.
Nur Python-Standardbibliothek (ab 3.9). Die Website liefert ihre Angaben in build.py und ruft run() auf:

  content/seiten/*.md     -> docs/<slug>.html          content/en/seiten/*.md -> docs/en/<slug>.html
  content/doku/*.md       -> docs/doku/<slug>.html     content/en/doku/*.md   -> docs/en/docs/<slug>.html

Englische Seiten nennen ihre deutsche Entsprechung im Kopf (`de: <slug>`); daraus entstehen
Sprachumschalter und hreflang-Links. Jede Sprache bekommt einen eigenen Suchindex. Nach dem
Bauen werden alle internen Links und Sprungmarken geprüft (Abbruch bei toten Links).

Assets: docs/assets/style.css = kit/style.css (Umbruchstellen der Kopfzeile eingesetzt) + kit/theme.css,
docs/assets/site.js = kit/site.js, dazu alles aus static/ der Website (Icon, Bilder).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

KIT = Path(__file__).resolve().parent

# Angaben der Website – werden von configure() gesetzt (siehe build.py der Website und template/build.py)
ROOT = CONTENT = STATIC = None
SITE_NAME = SITE_SHORT = ""
STAGE = "alpha"         # Zusatz in der Kopfzeile („BYOC · alpha“); leer = ohne
SITE_URL = ""           # öffentliche Adresse; gesetzt -> Open-Graph-Angaben
OG_IMAGE = ""           # Pfad relativ zu SITE_URL, z. B. "assets/img/ui/x.webp"
BASE_PATH = "/"         # Pfad auf dem Server (nur für die 404-Seite mit <base>)
NAV_BREAKPOINTS = (1180, 1060, 1000)  # Kopfzeile kompakt / enger / Menü-Schalter (px), je nach Länge der Navigation
LANGS: dict = {}
LOGO_SVG = ""
ASSETS: dict = {}       # Dateiname -> Inhalt (bytes) der Kern-Assets
ASSET_V: dict = {}

_REQUIRED = ("root", "site_name", "site_short", "langs", "logo_svg")


def configure(**cfg) -> None:
    """Setzt die Angaben der Website. Pflicht: root, site_name, site_short, langs, logo_svg.
    Optional: stage, site_url, og_image, base_path, nav_breakpoints."""
    missing = [k for k in _REQUIRED if k not in cfg]
    if missing:
        raise SystemExit(f"FEHLER: configure() ohne {', '.join(missing)}")
    g = globals()
    for k, v in cfg.items():
        name = k.upper()
        if name not in g or name in ("KIT", "ASSETS", "ASSET_V", "CONTENT", "STATIC"):
            raise SystemExit(f"FEHLER: unbekannte Angabe configure({k}=…)")
        g[name] = v
    g["ROOT"] = Path(cfg["root"]).resolve()
    g["CONTENT"] = ROOT / "content"
    g["STATIC"] = ROOT / "static"
    for lg, L in LANGS.items():
        L.setdefault("content", CONTENT if not L["dir"] else CONTENT / L["dir"].strip("/"))
    g["ASSETS"] = _core_assets()
    g["ASSET_V"] = {n: hashlib.sha256(b).hexdigest()[:10] for n, b in ASSETS.items()}


def _core_assets() -> dict:
    """Kern-Assets aus kit/: Stylesheet (mit Umbruchstellen und Theme) und Skript."""
    theme = KIT / "theme.css"
    if not theme.exists():
        raise SystemExit("FEHLER: kit/theme.css fehlt (python3 <site-kit>/sync.py ausführen)")
    css = (KIT / "style.css").read_text(encoding="utf-8")
    for key, px in zip(("nav_compact", "nav_tight", "nav_menu"), NAV_BREAKPOINTS):
        css = css.replace("{{" + key + "}}", str(int(px)))
    if "{{" in css:
        raise SystemExit("FEHLER: Platzhalter in kit/style.css nicht ersetzt (NAV_BREAKPOINTS prüfen)")
    css = css.rstrip("\n") + "\n\n/* ------------------------------------------------------------------ Akzent (kit/theme.css) */\n"
    css += theme.read_text(encoding="utf-8")
    clash = [n for n in ("style.css", "site.js") if (STATIC / n).exists()]
    if clash:
        raise SystemExit(f"FEHLER: static/{clash[0]} überschreibt den Kern – Anpassungen gehören ins Theme bzw. nach site-kit")
    return {"style.css": css.encode("utf-8"), "site.js": (KIT / "site.js").read_bytes()}


def og_title(t: dict) -> str:
    return t.get("og_title") or f"{SITE_NAME} ({SITE_SHORT})"


def _og_meta(full_title: str, description: str, lang: str) -> str:
    if not SITE_URL:
        return ""
    img = f'<meta property="og:image" content="{SITE_URL}{OG_IMAGE}">\n' if OG_IMAGE else ""
    return (f'<meta property="og:type" content="website">\n'
            f'<meta property="og:site_name" content="{SITE_NAME}">\n'
            f'<meta property="og:title" content="{html.escape(full_title)}">\n'
            f'<meta property="og:description" content="{html.escape(description)}">\n'
            f'{img}<meta property="og:locale" content="{"de_DE" if lang == "de" else "en_US"}">\n')


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


def render_md(src: str, link_fix=None, toc: list | None = None, anchor_label: str = "Link zu diesem Abschnitt") -> str:
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
            em = re.search(r"\s*\{#([a-z0-9-]+)\}$", title)
            if em:
                title = title[:em.start()].rstrip()
            hid = em.group(1) if em else slugify(title)
            base, n = hid, 2
            while hid in used_ids:
                hid = f"{base}-{n}"
                n += 1
            used_ids.add(hid)
            if toc is not None and level == 2:
                toc.append((hid, re.sub(r"<[^>]+>", "", il(title))))
            out.append(f'<h{level} id="{hid}">{il(title)}<a class="anchor" href="#{hid}" aria-label="{anchor_label}">#</a></h{level}>')
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
            out.append('<blockquote>' + render_md("\n".join(buf), link_fix, anchor_label=anchor_label) + "</blockquote>")
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


def flag(meta: dict, key: str) -> bool:
    return meta.get(key, "").lower() in ("ja", "yes", "true")


def plain_text(html_src: str) -> str:
    t = re.sub(r"<(script|style|svg)[\s\S]*?</\1>", " ", html_src)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def rel(target: str, here: str) -> str:
    """Relativer Link von Seite `here` auf `target` (beide relativ zur Website-Wurzel)."""
    r = posixpath.relpath(target, posixpath.dirname(here) or ".")
    return r


# --------------------------------------------------------------------------- Layout

def layout(*, lang: str, path: str, title: str, body: str, description: str, active: str = "",
           head: str = "", toc: list | None = None, alt: str | None = None, kind: str = "page",
           base: str | None = None) -> str:
    """Seitengerüst. `path` und `alt` sind relativ zur Website-Wurzel (z. B. "en/docs/dns.html")."""
    L = LANGS[lang]
    t = L["t"]
    other = "en" if lang == "de" else "de"
    root = "" if base else "../" * path.count("/")
    lroot = root + L["dir"]
    nav = []
    for href, label in L["nav"]:
        cur = ' aria-current="page"' if href == active else ""
        nav.append(f'<li><a href="{lroot}{href}"{cur}>{label}</a></li>')
    toc_html = ""
    if toc:
        items = "".join(f'<li><a href="#{hid}">{tt}</a></li>' for hid, tt in toc)
        toc_html = (f'<nav class="toc" aria-label="{t["toc_label"]}"><p class="toc-title">{t["toc_title"]}</p>'
                    f"<ol>{items}</ol></nav>")
    full_title = f"{title} · {SITE_NAME}" if title != SITE_NAME else og_title(t)
    alt_target = alt or (LANGS[other]["dir"] + "index.html")
    switch = (f'<a class="lang-switch" href="{root}{alt_target}" hreflang="{other}" lang="{other}" '
              f'aria-label="{t["switch_label"]}"><span aria-hidden="true">{t["switch_short"]}</span>'
              f'<span class="lang-long" aria-hidden="true">{t["switch"]}</span></a>')
    alternates = ""
    if alt and not base:
        pairs = {lang: path, other: alt}
        alternates = "".join(
            f'<link rel="alternate" hreflang="{lg}" href="{root}{p}">\n' for lg, p in sorted(pairs.items()))
        alternates += f'<link rel="alternate" hreflang="x-default" href="{root}{pairs["de"]}">\n'
    canonical = "" if base else f'<link rel="canonical" href="{root}{path}">\n'
    base_tag = f'<base href="{base}">\n' if base else ""
    foot_links = " · ".join(f'<a href="{h if h.startswith("http") else lroot + h}"{" rel=\"noopener\"" if h.startswith("http") else ""}>{lbl}</a>' for h, lbl in t["foot_links"])
    if kind == "hero":
        inner = body
    else:
        cls = "page with-toc" if toc else "page"
        inner = f'{head}<div class="{cls}">{toc_html}<div class="content">{body}</div></div>'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{base_tag}<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="color-scheme" content="light dark">
{_og_meta(full_title, description, lang)}<meta name="theme-color" content="#0e1115">
{canonical}{alternates}<link rel="stylesheet" href="{root}assets/style.css?v={ASSET_V['style.css']}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
</head>
<body class="k-{kind}">
<a class="skip" href="#inhalt">{t["skip"]}</a>
<header class="site-header">
  <div class="bar">
    <a class="brand" href="{lroot}index.html" aria-label="{SITE_NAME} ({SITE_SHORT}) – {t["home_label"]}">
      {LOGO_SVG}<span class="brand-text"><span class="brand-name">{SITE_NAME}</span><span class="brand-sub">{SITE_SHORT}{" · " + STAGE if STAGE else ""}</span></span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="hauptnav">{t["menu"]}</button>
    <nav id="hauptnav" class="mainnav" aria-label="{t["mainnav"]}"><ul>{"".join(nav)}</ul></nav>
    <div class="tools">
      <form class="search" role="search" action="{lroot}{L["search"]}" method="get">
        <label for="q" class="sr-only">{t["search"]}</label>
        <input id="q" name="q" type="search" placeholder="{t["search_ph"]}" autocomplete="off">
      </form>
      {switch}
    </div>
  </div>
</header>
<main id="inhalt" tabindex="-1">
{inner}
</main>
<footer class="site-footer">
  <div class="bar">
    <div class="foot-brand">{LOGO_SVG}<p><strong>{SITE_NAME}</strong> ({SITE_SHORT}) – {t["tagline"]} {t["prefix_note"]}</p></div>
    <p>{t["foot_license"]}</p>
    <nav aria-label="{t["foot_nav"]}"><p>{foot_links}</p></nav>
  </div>
</footer>
<script src="{root}assets/site.js?v={ASSET_V['site.js']}" defer></script>
</body>
</html>
"""


def page_head(*, crumbs: str = "", eyebrow: str = "", title: str, lead: str = "", meta: str = "") -> str:
    eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
    ld = f'<p class="lead">{lead}</p>' if lead else ""
    return (f'<header class="page-head"><div class="wrap">{crumbs}{eb}<h1>{html.escape(title)}</h1>'
            f'{ld}{meta}</div></header>')


# --------------------------------------------------------------------------- Bauen

def build(out: Path) -> int:
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    for n, data in ASSETS.items():
        (out / "assets" / n).write_bytes(data)
    for f in sorted(STATIC.iterdir()) if STATIC.exists() else []:
        if f.is_file():
            shutil.copy2(f, out / "assets" / f.name)
        elif f.is_dir():  # z. B. static/img/ -> assets/img/ (Bilder, siehe check-leaks.py: Formate, Metadaten)
            shutil.copytree(f, out / "assets" / f.name)
    (out / ".nojekyll").write_text("")
    problems: list[str] = []

    # Seiten beider Sprachen einlesen
    pages = {lg: [read_page(p) for p in sorted((L["content"] / "seiten").glob("*.md"))] for lg, L in LANGS.items()}
    docs = {}
    for lg, L in LANGS.items():
        ds = [read_page(p) for p in sorted((L["content"] / "doku").glob("*.md")) if not p.name.startswith("_")]
        ds.sort(key=lambda d: (d.get("group", "konzept") != "konzept", d["order"], d["title"]))
        docs[lg] = ds

    # Zuordnung DE <-> EN über das Kopffeld `de:` der englischen Seiten (Pfade relativ zur Wurzel)
    def out_path(lg: str, kind: str, slug: str) -> str:
        L = LANGS[lg]
        return L["dir"] + (f'{L["docs"]}/{slug}.html' if kind == "doc" else f"{slug}.html")

    alt: dict[str, str] = {}
    for kind, coll in (("page", pages), ("doc", docs)):
        de_slugs = {d["slug"] for d in coll["de"]}
        for d in coll["en"]:
            src = d.get("de")
            if not src or src not in de_slugs:
                problems.append(f"Englische Seite ohne gültige deutsche Entsprechung: {kind} {d['slug']} (de: {src})")
                continue
            a, b = out_path("de", kind, src), out_path("en", kind, d["slug"])
            alt[a], alt[b] = b, a
        en_src = {d.get("de") for d in coll["en"]}
        for d in coll["de"]:
            if d["slug"] not in en_src:
                problems.append(f"Deutsche Seite ohne englische Fassung: {kind} {d['slug']}")
    for a, b in (("doku/index.html", "en/docs/index.html"), ("suche.html", "en/search.html")):
        alt[a], alt[b] = b, a

    for lg, L in LANGS.items():
        t = L["t"]
        d_dir = L["docs"]
        index_entries = []
        groups = dict(L["groups"])

        # Doku-Seiten
        for d in docs[lg]:
            path = out_path(lg, "doc", d["slug"])
            toc: list = []
            body_html = render_md(d["body"], None, toc, t["anchor"])
            group = d.get("group", "konzept")
            crumbs = (f'<nav class="crumbs" aria-label="{t["crumbs"]}"><ol><li><a href="../index.html">{t["start"]}</a></li>'
                      f'<li><a href="index.html">{t["docs"]}</a></li><li><span aria-current="page">{html.escape(d["title"])}</span></li></ol></nav>')
            meta_line = f'<p class="meta">{t["source"]}: {html.escape(d["quelle"])}</p>' if d.get("quelle") else ""
            same = [x for x in docs[lg] if x.get("group", "konzept") == group]
            pos = same.index(d)
            pager = f'<nav class="pager" aria-label="{t["pager"]}">'
            pager += (f'<a rel="prev" href="{same[pos-1]["slug"]}.html"><span aria-hidden="true">←</span> {html.escape(same[pos-1]["title"])}</a>'
                      if pos > 0 else "<span></span>")
            if pos + 1 < len(same):
                pager += f'<a rel="next" href="{same[pos+1]["slug"]}.html">{html.escape(same[pos+1]["title"])} <span aria-hidden="true">→</span></a>'
            pager += "</nav>"
            head = page_head(crumbs=crumbs, eyebrow=html.escape(groups.get(group, "")), title=d["title"],
                             lead=inline(d["summary"]), meta=meta_line)
            (out / path).parent.mkdir(parents=True, exist_ok=True)
            (out / path).write_text(layout(
                lang=lg, path=path, title=d["title"], body=f'<article class="doc">{body_html}</article>{pager}',
                head=head, description=d["summary"], toc=toc, active=f"{d_dir}/index.html", alt=alt.get(path),
                kind="doc"), encoding="utf-8")
            index_entries.append({"t": d["title"], "u": f"{d_dir}/{d['slug']}.html", "s": d["summary"],
                                  "h": [x for _, x in toc], "x": plain_text(body_html)[:12000]})

        # Doku-Übersicht
        parts = []
        for gkey, glabel in L["groups"]:
            items = [d for d in docs[lg] if d.get("group", "konzept") == gkey]
            if not items:
                continue
            parts.append(f'<h2 id="{gkey}">{glabel} <span class="count">{len(items)} {t["pages"]}</span></h2><ul class="cards doc-cards">')
            for d in items:
                parts.append(f'<li><a href="{d["slug"]}.html"><strong>{html.escape(d["title"])}</strong>'
                             f'<span>{inline(d["summary"])}</span></a></li>')
            parts.append("</ul>")
        path = f'{L["dir"]}{d_dir}/index.html'
        crumbs = f'<nav class="crumbs" aria-label="{t["crumbs"]}"><ol><li><a href="../index.html">{t["start"]}</a></li><li><span aria-current="page">{t["docs"]}</span></li></ol></nav>'
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_text(layout(
            lang=lg, path=path, title=t["docs"], body="".join(parts),
            head=page_head(crumbs=crumbs, eyebrow=f"{SITE_SHORT} · {t['docs']}", title=t["docs"], lead=t["docs_lead"]),
            active=f"{d_dir}/index.html", description=t["docs_desc"], alt=alt.get(path), kind="docs-index"),
            encoding="utf-8")
        index_entries.append({"t": t["docs"], "u": f"{d_dir}/index.html", "s": t["docs_index_s"], "h": [], "x": ""})

        # Einzelseiten
        for d in pages[lg]:
            path = out_path(lg, "page", d["slug"])
            toc = [] if flag(d, "toc") else None
            body_html = render_md(d["body"], None, toc, t["anchor"])
            fname = f"{d['slug']}.html"
            if flag(d, "hero"):
                html_page = layout(lang=lg, path=path, title=SITE_NAME, body=body_html, description=d["summary"],
                                   active=fname, alt=alt.get(path), kind="hero")
            else:
                head = page_head(eyebrow=SITE_SHORT, title=d["title"], lead=inline(d["summary"]))
                html_page = layout(lang=lg, path=path, title=d["title"], body=f'<article class="doc">{body_html}</article>',
                                   head=head, description=d["summary"], toc=toc, active=fname, alt=alt.get(path),
                                   kind="wide" if flag(d, "wide") else "page")
            (out / path).write_text(html_page, encoding="utf-8")
            if flag(d, "noindex"):  # Impressum/Datenschutz bzw. Legal notice/Privacy: nicht in die Suche
                continue
            index_entries.append({"t": d["title"] if not flag(d, "hero") else og_title(t),
                                  "u": fname, "s": d["summary"], "h": [x for _, x in (toc or [])],
                                  "x": plain_text(body_html)[:12000]})

        # Suche
        path = L["dir"] + L["search"]
        search_body = (
            f'<form class="bigsearch" role="search" action="{L["search"]}" method="get">'
            f'<label for="sq">{t["search_label"]}</label><input id="sq" name="q" type="search" autocomplete="off">'
            f'<button type="submit">{t["search_btn"]}</button></form>'
            f'<p id="search-status" role="status" aria-live="polite"></p>'
            f'<ol id="search-results" class="results" data-index="{L["index_json"]}"></ol>'
            f'<noscript><p>{t["search_noscript"]}</p></noscript>'
        )
        (out / path).write_text(layout(lang=lg, path=path, title=t["search"], body=search_body,
                                       head=page_head(eyebrow=SITE_SHORT, title=t["search"]),
                                       description=t["search_desc"], alt=alt.get(path)), encoding="utf-8")
        (out / (L["dir"] + L["index_json"])).write_text(json.dumps(index_entries, ensure_ascii=False), encoding="utf-8")

    # 404 (zweisprachig; GitHub Pages liefert sie unter beliebigen Pfaden aus, daher <base>)
    base = BASE_PATH
    nf_body = (
        '<p>Diese Seite gibt es nicht (mehr). Weiter zur <a href="index.html">Startseite</a>, zur '
        '<a href="doku/index.html">Dokumentation</a> oder zur <a href="suche.html">Suche</a>.</p>'
        '<div lang="en"><h2 id="page-not-found">Page not found</h2><p>This page does not exist (anymore). Continue to the '
        '<a href="en/index.html">English home page</a>, the <a href="en/docs/index.html">documentation</a> or '
        '<a href="en/search.html">search</a>.</p></div>'
    )
    (out / "404.html").write_text(layout(
        lang="de", path="404.html", title=LANGS["de"]["t"]["nf_title"], body=nf_body,
        head=page_head(eyebrow="404", title="Seite nicht gefunden"), description="404", base=base),
        encoding="utf-8")

    problems += check_links(out)
    if problems:
        for pr in sorted(set(problems)):
            print("FEHLER:", pr, file=sys.stderr)
        return 1
    n = len(list(out.rglob("*.html")))
    print(f"OK: {n} HTML-Seiten nach {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}, Links und Sprungmarken geprüft")
    return 0


# --------------------------------------------------------------------------- Linkprüfung

class _Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.refs: list[str] = []
        self.base: str | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "base":
            self.base = a.get("href")
        if tag == "a" and a.get("href"):
            self.refs.append(a["href"])
        if tag in ("link", "script", "img") and (a.get("href") or a.get("src")):
            self.refs.append(a.get("href") or a.get("src"))
        if tag in ("img", "source") and a.get("srcset"):
            self.refs += [c.strip().split()[0] for c in a["srcset"].split(",") if c.strip()]
        if tag == "form" and a.get("action"):
            self.refs.append(a["action"])


def check_links(out: Path) -> list[str]:
    parsed: dict[str, _Collector] = {}
    for f in out.rglob("*.html"):
        c = _Collector()
        c.feed(f.read_text(encoding="utf-8"))
        parsed[f.relative_to(out).as_posix()] = c
    problems = []
    for here, c in parsed.items():
        for ref in c.refs:
            if ref.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, frag = ref.partition("#")
            target = target.partition("?")[0]  # Cache-Busting-Parameter (?v=…) ignorieren
            if not target:
                tpath = here
            else:
                basedir = "" if c.base else posixpath.dirname(here)
                tpath = posixpath.normpath(posixpath.join(basedir, target))
                if target.endswith("/"):
                    tpath += "/index.html"
            if tpath.startswith(".."):
                problems.append(f"{here}: Link verlässt die Website: {ref}")
                continue
            if not (out / tpath).exists():
                problems.append(f"{here}: toter Link: {ref}")
                continue
            if frag and tpath.endswith(".html") and frag not in parsed[tpath].ids:
                problems.append(f"{here}: unbekannte Sprungmarke: {ref}")
    return problems


def run(argv: list[str] | None = None) -> int:
    """Kommandozeile der Website: python3 build.py [--out DIR]"""
    if ROOT is None:
        raise SystemExit("FEHLER: zuerst sitekit.configure(...) aufrufen")
    ap = argparse.ArgumentParser(description=f"Baut die Website von {SITE_NAME} nach docs/ (site-kit).")
    ap.add_argument("--out", default=str(ROOT / "docs"))
    a = ap.parse_args(argv)
    return build(Path(a.out).resolve())
