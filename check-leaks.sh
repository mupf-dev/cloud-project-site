#!/bin/sh
# SPDX-FileCopyrightText: 2026 cloud-project contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# Baut die Seite und prüft Ausgabe + Quellen auf verbotene Muster. Exit 1 bei Funden.
set -eu
cd "$(dirname "$0")"
python3 build.py
# Ausgabe, Quellen und Generator prüfen (das Prüfskript selbst enthält die Muster und bleibt außen vor)
exec python3 check-leaks.py docs content tools static build.py check-leaks.sh README.md "$@"
