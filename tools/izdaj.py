#!/usr/bin/env python3
"""Provjerava je li sve spremno za izdanje i objavljuje ga: git oznaka i GitHub Release s PDF-om.

Pokretanje:  python tools/izdaj.py            samo provjere, ništa ne mijenja
             python tools/izdaj.py --objavi   provjere, oznaka vGGGG.MM i Release

Ako objava stane na pola, ponovno pokretanje nastavlja gdje je stala.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from izdanje import kao_brojevi, procitaj

KORIJEN = Path(__file__).resolve().parent.parent
PDF = KORIJEN / "Od-vozaca-do-mehanicara.pdf"
GRANA = "main"
# Promjena ovih putanja nakon zadnje gradnje znači da je PDF zastario.
IZVORI = ["poglavlja", "slike", "tools/knjiga.css", "tools/ispis.css"]


def naredba(*args, provjeri=True) -> str | None:
    """Vraća ispis naredbe. Uz provjeri=False neuspjeh vraća None umjesto iznimke."""
    p = subprocess.run(args, cwd=KORIJEN, capture_output=True, encoding="utf-8")
    if p.returncode:
        if provjeri:
            raise SystemExit(f"Nije uspjelo: {' '.join(args)}\n{p.stderr.strip()}")
        return None
    return p.stdout.strip()


def git(*args, provjeri=True):
    return naredba("git", *args, provjeri=provjeri)


def naslovnica_pdfa() -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise SystemExit("Nedostaje pypdf: pip install -r tools/requirements.txt")
    return " ".join(PdfReader(PDF).pages[0].extract_text().split())


def provjere(izd) -> list[str]:
    greske = []
    if git("status", "--porcelain"):
        greske.append("Ima nepotvrđenih promjena (git status).")
    if git("branch", "--show-current") != GRANA:
        greske.append(f"Izdaje se samo s grane {GRANA}.")
    git("fetch", "--tags", "origin", GRANA)
    glava = git("rev-parse", "HEAD")
    if glava != git("rev-parse", f"origin/{GRANA}"):
        greske.append(f"Lokalna grana i origin/{GRANA} se razlikuju; prvo pošalji ili povuci promjene.")

    novija = [t for t in git("tag", "-l", "v*").split()
              if t[1:].replace(".", "").isdigit() and kao_brojevi(t[1:]) > kao_brojevi(izd.oznaka)]
    if novija:
        greske.append(f"Već postoji novije izdanje: {', '.join(novija)}.")
    oznaceno = git("rev-parse", "-q", "--verify", f"{izd.tag}^{{commit}}", provjeri=False)
    if oznaceno and oznaceno != glava:
        greske.append(f"{izd.tag} već postoji na drugom commitu; dodaj novi zapis na vrh IZMJENE.md.")

    if not PDF.exists():
        greske.append(f"Nema {PDF.name}.")
    else:
        if f"Izdanje {izd.oznaka}." not in naslovnica_pdfa():
            greske.append(f"Na naslovnici PDF-a ne piše 'Izdanje {izd.oznaka}.'; ponovno izgradi PDF.")
        zadnji_pdf = git("log", "-1", "--format=%H", "--", PDF.name)
        if zadnji_pdf and git("log", "--oneline", f"{zadnji_pdf}..HEAD", "--", *IZVORI):
            greske.append("Tekst, slike ili stilovi mijenjani su nakon zadnje gradnje PDF-a; ponovno ga izgradi.")
    return greske


def objavi(izd):
    if not git("rev-parse", "-q", "--verify", f"refs/tags/{izd.tag}", provjeri=False):
        git("tag", "-a", izd.tag, "-m", f"Izdanje {izd.oznaka}")
        print(f"Oznaka {izd.tag} stvorena.")
    git("push", "origin", f"refs/tags/{izd.tag}")
    print(f"Oznaka {izd.tag} poslana.")

    if naredba("gh", "release", "view", izd.tag, provjeri=False) is not None:
        print(f"Release {izd.tag} već postoji, ništa ne diram.")
        return
    with tempfile.TemporaryDirectory() as t:
        kopija = Path(t) / f"{PDF.stem}-{izd.oznaka}.pdf"
        shutil.copyfile(PDF, kopija)
        biljeske = Path(t) / "biljeske.md"
        biljeske.write_text(izd.biljeske + "\n", encoding="utf-8")
        adresa = naredba("gh", "release", "create", izd.tag, str(kopija), "--verify-tag",
                         "--title", f"Izdanje {izd.oznaka}", "--notes-file", str(biljeske))
    print(f"Release objavljen: {adresa}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    izd = procitaj()
    print(f"Izdanje {izd.oznaka}, stanje alata i mjerenja {izd.stanje}, oznaka {izd.tag}.")
    greske = provjere(izd)
    if greske:
        print("Nije spremno:")
        for g in greske:
            print(f"  - {g}")
        return 1
    print("Provjere su prošle.")
    if "--objavi" in sys.argv:
        objavi(izd)
    else:
        print("Ništa nije objavljeno. Za objavu dodaj --objavi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
