#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 cloud-project contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prüft die generierte Website (und die Quellen) auf verbotene Inhalte – Muster dieser Website.

Die Prüflogik und die gemeinsamen Muster stehen im Kern site-kit (kit/leakcheck.py).
Endet mit Code 1, wenn etwas gefunden wird. Nur Standardbibliothek.

Aufruf:  python3 check-leaks.py [VERZEICHNIS ...]   (Standard: docs content)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "kit"))
import leakcheck as lc  # noqa: E402  (Kopie aus site-kit, siehe kit/README.md)

lc.PATTERNS += [
    ("Ticketschlüssel", re.compile(r"\bCLOU-\d+", re.I)),
] + lc.RUST_PATTERNS

lc.ALLOW_LINES += [
    re.compile(r"mistral\.rs"),  # Name eines Fremdprojekts, kein Quellpfad
]

if __name__ == "__main__":
    sys.exit(lc.run(ROOT, sys.argv[1:]))
