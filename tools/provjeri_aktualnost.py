#!/usr/bin/env python3
"""Provjerava je li knjiga još usklađena sa svijetom: poveznice, modeli, licence i inačice alata.

Treba samo standardnu biblioteku. Ništa ne mijenja, samo piše izvještaj.

    python tools/provjeri_aktualnost.py --izvjestaj izvjestaj.md

Izlazni kod: 0 ako nema ničega za napraviti, 2 ako postoje stavke "Treba reagirati".
Kod 1 znači da sama provjera nije uspjela.
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
VERZIJE = json.loads((KORIJEN / "prilozi" / "okruzenje" / "verzije.json").read_text(encoding="utf-8"))
AGENT = "Mozilla/5.0 (compatible; provjera-poveznica-knjige/1.0)"
# Primjeri u knjizi i lokalne adrese, koji nisu stvarne poveznice.
PRESKOCI = re.compile(r"(127\.0\.0\.1|localhost|example\.(com|org)|0\.0\.0\.0|<|\{|\$"
                      # Početci adresa iz naredbi, na koje se u kodu dodaje ime datoteke. Sami vraćaju 404.
                      r"|/resolve/main/?$|/releases/download/[^/]+/?$|/archive/refs/tags/?$)")
# GitHub token vrijedi samo za GitHubov API; drugim se poslužiteljima ne šalje.
GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def dohvati(url, metoda="GET", vrijeme=30):
    zaglavlja = {"User-Agent": AGENT, "Accept": "*/*"}
    if GH_TOKEN and url.startswith("https://api.github.com/"):
        zaglavlja["Authorization"] = f"Bearer {GH_TOKEN}"
    z = urllib.request.Request(url, headers=zaglavlja, method=metoda)
    with urllib.request.urlopen(z, timeout=vrijeme) as r:
        return r.status, r.read() if metoda == "GET" else b""


def json_s(url):
    return json.loads(dohvati(url)[1])


def nadi_poveznice():
    """Vraća {url: [datoteka, ...]} iz teksta knjige."""
    nadeno = {}
    for d in sorted((KORIJEN / "poglavlja").glob("*.md")):
        for u in re.findall(r"https?://[^\s\)\]>\"'`]+", d.read_text(encoding="utf-8")):
            u = u.rstrip(".,;:*")
            if not PRESKOCI.search(u):
                nadeno.setdefault(u, set()).add(d.name)
    return nadeno


def provjeri_poveznicu(url):
    """Vraća (url, 'ok' | 'mrtva' | 'nejasno', opis). 401, 403, 429 i 5xx ne dokazuju da je poveznica mrtva."""
    for metoda in ("HEAD", "GET"):
        try:
            dohvati(url, metoda, 25)
            return url, "ok", ""
        except urllib.error.HTTPError as e:
            if e.code in (404, 410) and metoda == "GET":
                return url, "mrtva", f"HTTP {e.code}"
            if metoda == "GET":
                return url, "nejasno", f"HTTP {e.code}"
        except Exception as e:
            if metoda == "GET":
                return url, "nejasno", type(e).__name__
    return url, "nejasno", ""


def provjeri_modele(reagiraj, znanje, greske):
    for kljuc, m in VERZIJE["modeli"].items():
        repo, rev = m["repo"], m["revizija"]
        try:
            d = json_s(f"https://huggingface.co/api/models/{repo}")
        except urllib.error.HTTPError as e:
            reagiraj.append(f"Model `{repo}`: repozitorij se ne može otvoriti (HTTP {e.code}).")
            continue
        except Exception as e:
            greske.append(f"Model `{repo}`: {type(e).__name__}")
            continue
        try:
            json_s(f"https://huggingface.co/api/models/{repo}/revision/{rev}")
        except urllib.error.HTTPError as e:
            reagiraj.append(f"Model `{repo}`: prikvačena revizija `{rev[:10]}` više nije dostupna (HTTP {e.code}).")
        except Exception as e:
            greske.append(f"Model `{repo}`, revizija: {type(e).__name__}")
        licenca = (d.get("cardData") or {}).get("license")
        if licenca != m["licenca"]:
            reagiraj.append(f"Model `{repo}`: licenca je sada `{licenca}`, a u knjizi je mjereno uz `{m['licenca']}`.")
        if d.get("gated"):
            reagiraj.append(f"Model `{repo}`: pristup je sada zaključan (`gated`), pa se ne može preuzeti bez prijave.")
        if d.get("sha") and d["sha"] != rev:
            znanje.append(f"Model `{repo}`: postoji novija revizija `{d['sha'][:10]}` (prikvačena je `{rev[:10]}`).")


def provjeri_llama(reagiraj, znanje, greske):
    ll = VERZIJE["llama_cpp"]
    try:
        dohvati(ll["paket"]["url"], "HEAD")
    except urllib.error.HTTPError as e:
        reagiraj.append(f"llama.cpp: paket `{ll['oznaka']}` više se ne može preuzeti (HTTP {e.code}).")
    except Exception as e:
        greske.append(f"llama.cpp paket: {type(e).__name__}")
    try:
        d = json_s("https://api.github.com/repos/ggml-org/llama.cpp/releases/latest")
        if d["tag_name"] != ll["oznaka"]:
            znanje.append(f"llama.cpp: najnovija oznaka je `{d['tag_name']}`, a mjereno je na `{ll['oznaka']}`.")
    except Exception as e:
        greske.append(f"llama.cpp najnovija oznaka: {type(e).__name__}")


def provjeri_pakete(znanje, greske):
    for ime, inacica in VERZIJE["paketi_za_pracenje"].items():
        try:
            nova = json_s(f"https://pypi.org/pypi/{ime}/json")["info"]["version"]
        except Exception as e:
            greske.append(f"PyPI `{ime}`: {type(e).__name__}")
            continue
        if nova != inacica:
            velika = nova.split(".")[0] != inacica.split(".")[0]
            oznaka = " **(nova glavna inačica: vjerojatne su promjene u naredbama)**" if velika else ""
            znanje.append(f"`{ime}`: najnovija je {nova}, a mjereno je na {inacica}{oznaka}.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--izvjestaj", default="izvjestaj-aktualnost.md")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    reagiraj, znanje, greske, nejasne = [], [], [], []
    poveznice = nadi_poveznice()
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        rezultati = list(ex.map(provjeri_poveznicu, poveznice))
    for url, stanje, opis in rezultati:
        gdje = ", ".join(sorted(poveznice[url]))
        if stanje == "mrtva":
            reagiraj.append(f"Mrtva poveznica ({opis}) u {gdje}: {url}")
        elif stanje == "nejasno":
            nejasne.append(f"{url} ({opis or 'bez odgovora'}; {gdje})")
    provjeri_modele(reagiraj, znanje, greske)
    provjeri_llama(reagiraj, znanje, greske)
    provjeri_pakete(znanje, greske)

    izl = [f"Provjera od {date.today():%d. %m. %Y.} Poveznica u knjizi: {len(poveznice)}.", ""]
    for naslov, stavke, uvod in (
        ("Treba reagirati", reagiraj, ""),
        ("Za pregled izdanja", znanje, "Novije inačice same po sebi nisu greška. Prije novog izdanja pokreni `prilozi/pokreni_vjezbe.py`."),
        ("Poveznice koje se nisu mogle provjeriti", nejasne, "Poslužitelj je odbio automatski upit ili nije odgovorio, pa ih provjeri ručno ako se ponavljaju."),
        ("Greške same provjere", greske, ""),
    ):
        if stavke:
            izl += [f"## {naslov} ({len(stavke)})", ""] + ([uvod, ""] if uvod else []) + [f"- {s}" for s in stavke] + [""]
    izl += ["Automatska provjera ne čita sadržaj: cijene, pravila i preporuke treba pregledati ručno pri svakom izdanju."]
    tekst = "\n".join(izl)
    Path(a.izvjestaj).write_text(tekst, encoding="utf-8")
    print(tekst)
    return 2 if reagiraj else 0


if __name__ == "__main__":
    sys.exit(main())
