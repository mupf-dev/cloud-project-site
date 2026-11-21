#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 cloud-project contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Website von BYOC (Build Your Own Cloud) – Angaben der Website; der Generator ist der gemeinsame Kern site-kit (kit/sitekit.py).

Aufruf:  python3 build.py            # baut nach docs/
         python3 build.py --out DIR  # anderes Zielverzeichnis
Aufbau der Inhalte, Kopffelder und Prüfungen: README.md und tools/INHALTSREGELN.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "kit"))
import sitekit  # noqa: E402  (Kopie aus site-kit, siehe kit/README.md)

SITE_NAME = "BYOC"
SITE_SHORT = "Build Your Own Cloud"
# Pfad der Website auf dem Server (nur für die 404-Seite, die GitHub Pages unter beliebigen Pfaden ausliefert).
# hreflang-/canonical-Links sind relativ, damit die Website ohne festen Host funktioniert.
BASE_PATH = "/cloud-project-site/"

LANGS = {
    "de": {
        "dir": "",
        "docs": "doku",
        "search": "suche.html",
        "index_json": "suche-index.json",
        "nav": [
            ("index.html", "Start"),
            ("funktionen.html", "Funktionen"),
            ("portal.html", "Portal"),
            ("architektur.html", "Architektur"),
            ("doku/index.html", "Dokumentation"),
            ("roadmap.html", "Status & Roadmap"),
            ("mitmachen.html", "Mitmachen"),
        ],
        "groups": [("konzept", "Konzepte und Architekturentscheidungen"), ("prozess", "Prozesse")],
        "t": {
            "skip": "Zum Inhalt springen", "menu": "Menü", "mainnav": "Hauptnavigation",
            "search": "Suche", "search_ph": "Suchen …", "home_label": "Startseite",
            "toc_label": "Inhalt dieser Seite", "toc_title": "Auf dieser Seite",
            "anchor": "Link zu diesem Abschnitt", "crumbs": "Brotkrumen", "start": "Start",
            "docs": "Dokumentation", "pager": "Weitere Seiten", "source": "Aufbereitet aus",
            "switch": "English", "switch_short": "EN", "switch_label": "English version of this page",
            "tagline": "Quelloffene, dezentrale Cloud-Plattform – vom Homelab bis zum Rechenzentrum.",
            "foot_license": 'Dokumentation unter <a href="https://creativecommons.org/licenses/by/4.0/deed.de" rel="license noopener">CC BY 4.0</a>, Code unter AGPL-3.0-or-later. Keine Cookies, kein Tracking, keine externen Ressourcen.',
            "foot_links": [("mitmachen.html#lizenz", "Lizenz"), ("mitmachen.html#sicherheit", "Sicherheitslücke melden"),
                           ("suche.html", "Suche"), ("impressum.html", "Impressum"), ("datenschutz.html", "Datenschutz")],
            "foot_nav": "Rechtliches und Service",
            "prefix_note": "Komponenten tragen das Präfix <code>cp</code>.",
            "docs_lead": "Aufbereitete Fassungen der Konzepte, Architekturentscheidungen (ADRs) und Prozesse von BYOC. Die Seiten fassen die Projektdokumente für ein öffentliches Publikum zusammen.",
            "docs_desc": "Konzepte, Architekturentscheidungen und Prozesse von BYOC (Build Your Own Cloud).",
            "docs_index_s": "Übersicht aller Konzepte und Prozesse",
            "pages": "Seiten",
            "search_label": "Suchbegriff", "search_btn": "Suchen", "search_desc": "Volltextsuche",
            "search_noscript": 'Die Suche benötigt JavaScript. Alternativ: <a href="doku/index.html">Dokumentationsübersicht</a>.',
            "nf_title": "Seite nicht gefunden",
        },
    },
    "en": {
        "dir": "en/",
        "docs": "docs",
        "search": "search.html",
        "index_json": "search-index.json",
        "nav": [
            ("index.html", "Home"),
            ("features.html", "Features"),
            ("portal.html", "Portal"),
            ("architecture.html", "Architecture"),
            ("docs/index.html", "Docs"),
            ("roadmap.html", "Status & roadmap"),
            ("contribute.html", "Contribute"),
        ],
        "groups": [("konzept", "Concepts and architecture decisions"), ("prozess", "Processes")],
        "t": {
            "skip": "Skip to content", "menu": "Menu", "mainnav": "Main navigation",
            "search": "Search", "search_ph": "Search …", "home_label": "Home",
            "toc_label": "Contents of this page", "toc_title": "On this page",
            "anchor": "Link to this section", "crumbs": "Breadcrumb", "start": "Home",
            "docs": "Docs", "pager": "More pages", "source": "Adapted from",
            "switch": "Deutsch", "switch_short": "DE", "switch_label": "Deutsche Fassung dieser Seite",
            "tagline": "Open-source, decentralized cloud platform – from homelab to data center.",
            "foot_license": 'Documentation under <a href="https://creativecommons.org/licenses/by/4.0/deed.en" rel="license noopener">CC BY 4.0</a>, code under AGPL-3.0-or-later. No cookies, no tracking, no third-party resources.',
            "foot_links": [("contribute.html#license", "License"), ("contribute.html#security", "Report a vulnerability"),
                           ("search.html", "Search"), ("legal-notice.html", "Legal notice"), ("privacy.html", "Privacy policy")],
            "foot_nav": "Legal and service",
            "prefix_note": "Components carry the prefix <code>cp</code>.",
            "docs_lead": "Public editions of BYOC's concepts, architecture decision records (ADRs) and processes, condensed from the project documents for a general audience.",
            "docs_desc": "Concepts, architecture decisions and processes of BYOC (Build Your Own Cloud).",
            "docs_index_s": "Overview of all concepts and processes",
            "pages": "Pages",
            "search_label": "Search term", "search_btn": "Search", "search_desc": "Full-text search",
            "search_noscript": 'Search needs JavaScript. Alternatively, browse the <a href="docs/index.html">documentation overview</a>.',
            "nf_title": "Page not found",
        },
    },
}

LOGO_SVG = (
    '<svg class="logo" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" focusable="false">'
    '<rect width="32" height="32" rx="6" class="logo-bg"/>'
    '<path d="M9.5 20.5a4.6 4.6 0 0 1 .5-9.15A6.6 6.6 0 0 1 22.6 12.6a4 4 0 0 1-.5 7.9Z" class="logo-cloud"/>'
    '<g class="logo-dots"><circle cx="11" cy="25" r="1.5"/><circle cx="16" cy="25" r="1.5"/><circle cx="21" cy="25" r="1.5"/></g>'
    '<path d="M11 20.5V23.5M16 20.5V23.5M21 20.5V23.5" class="logo-wire"/></svg>'
)

# Umbruchstellen der Kopfzeile (px): kompakt, enger, Menü-Schalter – abhängig von der Länge der Navigation
NAV_BREAKPOINTS = (1180, 1060, 1000)

sitekit.configure(
    root=ROOT, site_name=SITE_NAME, site_short=SITE_SHORT, base_path=BASE_PATH,
    nav_breakpoints=NAV_BREAKPOINTS, langs=LANGS, logo_svg=LOGO_SVG,
)

if __name__ == "__main__":
    sys.exit(sitekit.run())
