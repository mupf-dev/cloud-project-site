# SPDX-FileCopyrightText: 2026 site-kit contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""site-kit – Prüfung der generierten Website (und der Quellen) auf verbotene Inhalte.

NICHT in den Website-Repos bearbeiten: Quelle ist das Repo site-kit, sync.py kopiert diese Datei nach kit/.
Die Website ergänzt in check-leaks.py ihre eigenen Muster (PATTERNS, ALLOW_LINES, ggf. RUST_PATTERNS)
und ruft run(ROOT, argv) auf. Endet mit Code 1, wenn etwas gefunden wird. Nur Standardbibliothek.
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
import sys
from pathlib import Path

EXTS = {".html", ".json", ".js", ".css", ".md", ".svg", ".txt", ".xml", ".py", ".sh", ".yml", ".yaml"}

# (Name, Muster) – gilt für alle Websites; eigene Muster hängt check-leaks.py der Website an
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Hoster/Build-Infrastruktur", re.compile(r"hetzner|hcloud|buildbox|build-box|buildfarm|bauserver|steuerserver", re.I)),
    ("Interne Kennungen", re.compile(r"\b(ABW|THR|RR|ND)-[A-Z]*-?\d+", re.I)),
    ("Lab-/Testzugang", re.compile(r"cp-lab\b|lab-uplink|testschlüssel|testschluessel|tailscale", re.I)),
    ("Interne Pfade", re.compile(r"(?<![\w.])/(root|opt/buildfarm|work)/", re.I)),
    ("Sprintbericht", re.compile(r"docs/sprint|\bsprint\s*\d", re.I)),
    ("Secret-Datei/Infra", re.compile(r"\.tfstate|tfvars|azurerm|hcloud-token|sops\b|age1[0-9a-z]{20,}", re.I)),
    ("Schlüsselmaterial", re.compile(r"-----BEGIN")),
    ("E-Mail-Adresse", re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.(?:org|com|net)\b)[A-Za-z0-9-]+\.[A-Za-z0-9.-]*[A-Za-z]\b")),
    ("Freemail", re.compile(r"@(gmail|googlemail|outlook|hotmail|gmx|web\.de|yahoo|proton)", re.I)),
]

# Implementierungscode (Rust) – Websites von Rust-Projekten hängen diese Liste an PATTERNS an
RUST_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Rust-Code: fn", re.compile(r"\b(pub\s+)?(async\s+)?fn\s+[a-z_][a-z0-9_]*\s*[(<]")),
    ("Rust-Code: impl", re.compile(r"\bimpl\b(\s*<|\s+[A-Z][A-Za-z0-9_]*\b)")),
    ("Rust-Code: use crate", re.compile(r"\buse\s+(crate|super|std|tokio)::")),
    ("Rust-Code: Attribut", re.compile(r"#\[(derive|cfg|tokio|test|allow|deny)\b")),
    ("Rust-Code: let mut", re.compile(r"\blet\s+mut\b")),
    ("Rust-Code: struct/enum", re.compile(r"\b(pub\s+)?(struct|enum|trait)\s+[A-Z][A-Za-z0-9]*\s*[{<(]")),
    ("Quelldatei-Pfad (.rs)", re.compile(r"[\w/-]+\.rs\b")),
    ("Quelldatei-Pfad (crates/src)", re.compile(r"\b(crates|bin)/[\w-]+/src\b")),
]

# Interne Namen (Domain, Accounts) nur als SHA-256 der kleingeschriebenen Wort-Token,
# damit das öffentliche Prüfskript die Namen nicht selbst enthält.
HASHED_TOKENS = {
    "85e6f62630861380f3f21434fb51336c0607bb22137eaa84bce0f29ad38ffae5",  # interne Domain
    "43aedf47dfa5073710c4111476d845b94e0bce4aeb5aa7b0b5d1575ba41f990b",  # Accountname
}
TOKEN = re.compile(r"[a-z0-9]+")

IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/(\d{1,2}))?(?![\w.]*\d)")
# Erlaubte Dokumentations-/Beispielnetze
ALLOWED_V4 = [ipaddress.ip_network(n) for n in (
    "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24",  # RFC 5737
    "127.0.0.0/8", "0.0.0.0/32", "255.255.255.255/32",
)]
IPV6_ULA = re.compile(r"\bfd[0-9a-f]{2}:[0-9a-f]{1,4}:[0-9a-f]{1,4}", re.I)
IPV6_ALLOWED = re.compile(r"2001:db8", re.I)

# Ausdrücklich erlaubte Fundstellen (bekannte False Positives); werden vor der Prüfung entfernt
# (die Website ergänzt ihre öffentlichen Adressen, damit der Accountname sonst verboten bleibt)
ALLOW_LINES: list[re.Pattern] = []


# Pflichtangaben (§ 5 DDG) – ausschließlich auf Impressum und Datenschutzerklärung erlaubt
IMPRESSUM_FILES = {"impressum", "datenschutz", "legal-notice", "privacy"}  # DE + EN
IMPRESSUM_ALLOW = re.compile(r"marc\.leunig\+cloudproject(@|&#64;|&amp;#64;)miefda\.de")
# Anbieterdaten (Name, Anschrift) dürfen nur dort stehen – nicht auf anderen Seiten und nicht im Suchindex
IMPRESSUM_ONLY = re.compile(r"\bleunig|burgstallstra", re.I)


def check_ipv4(text: str) -> list[str]:
    hits = []
    for m in IPV4.finditer(text):
        addr = m.group(1)
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue  # z. B. Versionsnummer wie 1.2.300.4
        prefix = m.group(2)
        if prefix is not None:
            # Netzangaben: nur Dokumentationsnetze erlaubt
            try:
                net = ipaddress.ip_network(f"{addr}/{prefix}", strict=False)
            except ValueError:
                continue
            if any(net.subnet_of(a) for a in ALLOWED_V4 if a.version == 4):
                continue
            hits.append(f"{addr}/{prefix}")
            continue
        if any(ip in a for a in ALLOWED_V4):
            continue
        hits.append(addr)
    return hits


def scan_file(path: Path) -> list[str]:
    findings = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings
    for lineno, line in enumerate(text.splitlines(), 1):
        for a in ALLOW_LINES:  # nur die erlaubte Fundstelle entfernen, Rest der Zeile weiter prüfen
            line = a.sub(" ", line)
        if path.stem in IMPRESSUM_FILES:  # Anbieterkennzeichnung: nur die Kontaktadresse ist dort erlaubt
            line = IMPRESSUM_ALLOW.sub(" ", line)
        else:
            for m in IMPRESSUM_ONLY.finditer(line):
                findings.append(f"{path}:{lineno}: Impressumsdaten außerhalb von Impressum/Datenschutz: {m.group(0)!r}")
        for name, pat in PATTERNS:
            for m in pat.finditer(line):
                findings.append(f"{path}:{lineno}: {name}: {m.group(0)!r}")
        for tok in set(TOKEN.findall(line.lower())):
            if hashlib.sha256(tok.encode()).hexdigest() in HASHED_TOKENS:
                findings.append(f"{path}:{lineno}: interner Name (Hash-Treffer): {tok!r}")
        for ip in check_ipv4(line):
            findings.append(f"{path}:{lineno}: IPv4 außerhalb RFC 5737: {ip!r}")
        for m in IPV6_ULA.finditer(line):
            if not IPV6_ALLOWED.search(m.group(0)):
                findings.append(f"{path}:{lineno}: konkrete IPv6-ULA: {m.group(0)!r}")
    return findings


# Bilder (static/img/, docs/assets/img/): nur Formate der Whitelist, Inhalt passend zur Endung, keine Metadaten
# (EXIF, XMP, ICC-Profil, Text-/Zeit-Chunks) – Metadaten werden beim Optimieren entfernt.
IMG_FORMATS = {".webp", ".png", ".svg"}
WEBP_META = {b"EXIF", b"XMP ", b"ICCP"}
PNG_META = {b"eXIf", b"tEXt", b"zTXt", b"iTXt", b"tIME", b"iCCP"}


def check_image(path: Path) -> list[str]:
    suf = path.suffix.lower()
    if suf not in IMG_FORMATS:
        return [f"{path}: Bildformat nicht erlaubt (nur {', '.join(sorted(IMG_FORMATS))})"]
    data = path.read_bytes()
    if suf == ".svg":
        return [] if b"<svg" in data[:2048] else [f"{path}: kein SVG"]
    found = []
    if suf == ".webp":
        if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
            return [f"{path}: Inhalt ist kein WebP"]
        i = 12
        while i + 8 <= len(data):
            cid, size = data[i:i + 4], int.from_bytes(data[i + 4:i + 8], "little")
            if cid in WEBP_META:
                found.append(f"{path}: Metadaten-Chunk {cid.decode().strip()!r}")
            if cid == b"VP8X" and data[i + 8] & 0x2C:  # ICC/EXIF/XMP-Flag
                found.append(f"{path}: VP8X kündigt Metadaten an")
            i += 8 + size + (size & 1)
    elif suf == ".png":
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            return [f"{path}: Inhalt ist kein PNG"]
        i = 8
        while i + 8 <= len(data):
            size, cid = int.from_bytes(data[i:i + 4], "big"), data[i + 4:i + 8]
            if cid in PNG_META:
                found.append(f"{path}: Metadaten-Chunk {cid.decode()!r}")
            i += 12 + size
    return found


def image_files(targets: list[Path]) -> list[Path]:
    out = []
    for t in targets:
        if t.is_dir():
            out += [p for p in sorted(t.rglob("*")) if p.is_file() and "img" in p.relative_to(t).parts[:-1]]
    return out


def run(root: Path, argv: list[str]) -> int:
    """Aufruf aus check-leaks.py der Website: python3 check-leaks.py [VERZEICHNIS ...] (Standard: docs content)"""
    root = Path(root).resolve()
    local = root / ".leak-patterns.local"  # zusätzliche, nicht veröffentlichte Muster (eine Regex je Zeile)
    if local.exists():
        for ln in local.read_text(encoding="utf-8").splitlines():
            if ln.strip() and not ln.startswith("#"):
                PATTERNS.append(("Lokales Muster", re.compile(ln.strip(), re.I)))
    targets = [Path(a) for a in argv] or [root / "docs", root / "content"]
    files: list[Path] = []
    for t in targets:
        if not t.exists():
            print(f"FEHLER: {t} existiert nicht (zuerst python3 build.py ausführen)", file=sys.stderr)
            return 2
        files += [t] if t.is_file() else [p for p in sorted(t.rglob("*")) if p.is_file() and p.suffix in EXTS]
    findings = []
    for f in files:
        findings += scan_file(f)
    imgs = image_files(targets)
    for f in imgs:
        findings += check_image(f)
    if findings:
        for f in findings:
            print(f)
        print(f"\nLEAK-CHECK FEHLGESCHLAGEN: {len(findings)} Fund(e) in {len(files)} Dateien.", file=sys.stderr)
        return 1
    print(f"LEAK-CHECK OK: {len(files)} Dateien und {len(imgs)} Bilder geprüft, keine verbotenen Muster/Metadaten.")
    return 0

