#!/usr/bin/env python3
"""Priprema okruženje, pokreće CPU vježbe iz knjige i uspoređuje rezultate s objavljenim mjerenjima.

Radi na Windowsu s Git Bashom, jer su skripte vježbi pisane za taj sustav. Treba samo standardnu biblioteku.

    python pokreni_vjezbe.py popis
    python pokreni_vjezbe.py priprema C:\\vjezbe
    python pokreni_vjezbe.py pokreni C:\\vjezbe sve
    python pokreni_vjezbe.py pokreni C:\\vjezbe L3 L7 --ponovi
    python pokreni_vjezbe.py usporedi C:\\vjezbe

Radna mapa mora biti na lokalnom disku, nikad na disku koji se sinkronizira u oblak.
Izlazni kod naredbe "usporedi": 0 ako su stroge provjere prošle, 1 ako nisu.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import re
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

PRILOZI = Path(__file__).resolve().parent
VERZIJE = json.loads((PRILOZI / "okruzenje" / "verzije.json").read_text(encoding="utf-8"))

G = "models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf"
Q = "models/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf"
S3 = "models/smol3/SmolLM3-Q4_K_M.gguf"
BGE = "models/bge-m3-Q8_0-GGUF/bge-m3-q8_0.gguf"
GRAN = "models/granite-embedding-107m-multilingual-GGUF/granite-embedding-107m-multilingual-Q8_0.gguf"
SM2 = "models/SmolLM2-135M-Instruct"
SM3 = "models/SmolLM3-3B"
F16 = "models/smol3/SmolLM3-F16.gguf"
CONVERT = "llama-src/llama.cpp-b12110/convert_hf_to_gguf.py"
PY = "venv/Scripts/python.exe"
RAZINE = ["Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q3_K_M", "Q2_K"]
RAZINE_PPL = ["Q8_0", "Q4_K_M", "Q4_K_M-imat", "Q3_K_M", "Q3_K_M-imat", "Q2_K", "Q5_K_M", "Q6_K", "F16"]


def py(log, *a, dodaj=False):
    """Python skripta čiji se ispis sprema u logovi/LOG."""
    return {"naredba": [PY, "-X", "utf8", *a], "log": f"logovi/{log}", "dodaj": dodaj}


def mjeri(log, *a):
    """Naredba kroz mjeri.py, koji bilježi vrijeme i memoriju."""
    return {"naredba": [PY, "-X", "utf8", "skripte/mjeri.py", f"logovi/{log}", "--", *a]}


def bash(*a):
    return {"bash": list(a)}


def kopiraj(iz, u):
    return {"kopiraj": (iz, u)}


def koraci_l6():
    k = [mjeri("l6_convert.txt", PY, "-X", "utf8", CONVERT, SM3, "--outtype", "f16", "--outfile", F16),
         py("l6_quant_sazetak.txt", "skripte/l6_kvantizacija.py", "quant", F16, "models/smol3", "logovi/l6_quant.txt",
            "grafovi/kvantizacija_velicina.csv", *RAZINE, dodaj=True),
         py("l6_bench_sazetak.txt", "skripte/l6_kvantizacija.py", "bench", "models/smol3", "logovi/l6_bench.txt",
            "grafovi/kvantizacija_brzina.csv", *RAZINE, dodaj=True),
         mjeri("l6_imatrix.txt", "llama/llama-imatrix.exe", "-m", "models/smol3/SmolLM3-Q8_0.gguf", "-f",
               "models/tekst/kal_mix.txt", "-o", "models/smol3/imatrix.gguf", "-t", "4", "-c", "512", "-b", "512", "--no-ppl"),
         py("l6_quant_sazetak.txt", "skripte/l6_kvantizacija.py", "quant", F16, "models/smol3", "logovi/l6_quant.txt",
            "grafovi/kvantizacija_velicina.csv", "Q4_K_M:models/smol3/imatrix.gguf", "Q3_K_M:models/smol3/imatrix.gguf", dodaj=True)]
    for t in RAZINE_PPL:
        for j in ("hr", "en"):
            k.append(py("l6_ppl_sazetak.txt", "skripte/l6_kvantizacija.py", "ppl", "models/smol3", "logovi/l6_ppl.txt",
                        "grafovi/kvantizacija_ppl.csv", f"models/tekst/ppl_{j}_krat.txt", j, t, dodaj=True))
    return k


# trajanje je u minutama na mjernom stroju; "obrisi" su rezultati koje korak iznova stvara
VJEZBE = {
    "L7": dict(naslov="Podaci: generiranje i provjera", trajanje=1, ovisi=[], obrisi=[], koraci=[
        py("l7.txt", "skripte/l7_generiraj.py", "podaci"),
        py("l7.txt", "skripte/l7_provjeri.py", "podaci", dodaj=True)], izlazi=["logovi/l7.txt"]),
    "L2": dict(naslov="Mapa modela", trajanje=1, ovisi=[], obrisi=[], koraci=[
        py("l2.txt", "skripte/l2_mapa_modela.py", SM3)], izlazi=["logovi/l2.txt"]),
    "L3": dict(naslov="Tokeni", trajanje=1, ovisi=[], obrisi=[], koraci=[
        py("l3.txt", "skripte/l3_tokeni.py", SM3, SM2, G, Q)], izlazi=["logovi/l3.txt"]),
    "L1": dict(naslov="Prva vožnja i poslužitelj", trajanje=8, ovisi=[], obrisi=[], koraci=[
        bash("skripte/l1_prva_voznja.sh"), bash("skripte/l1_posluzitelj.sh"), bash("skripte/l1_curl.sh")],
        izlazi=["logovi/l1_curl2.txt", "logovi/l1_gemma_completion.txt"]),
    "L4": dict(naslov="Predlošci", trajanje=5, ovisi=[], obrisi=[], koraci=[
        py("l4.txt", "skripte/l4_predlosci.py", G, SM3, SM2, "logovi/l4_server.txt"),
        py("l4b.txt", "skripte/l4b_predlosci.py", G, "logovi/l4b_server.txt")], izlazi=["logovi/l4.txt", "logovi/l4b.txt"]),
    "L6": dict(naslov="Kvantizacija i šteta", trajanje=75, ovisi=[],
               obrisi=["grafovi/kvantizacija_velicina.csv", "grafovi/kvantizacija_brzina.csv", "grafovi/kvantizacija_ppl.csv"],
               koraci=koraci_l6(), izlazi=["grafovi/kvantizacija_ppl.csv", S3]),
    "L5": dict(naslov="Memorija", trajanje=3, ovisi=["L6"], obrisi=["grafovi/memorija_kontekst.csv"], koraci=[
        py("l5.txt", "skripte/l5_memorija.py", "logovi/l5_raw.txt", "grafovi/memorija_kontekst.csv", G, Q, S3)],
        izlazi=["grafovi/memorija_kontekst.csv"]),
    "L8": dict(naslov="Točnost na zlatnom skupu", trajanje=10, ovisi=[], obrisi=[], koraci=[
        py("l8.txt", "skripte/l8_tocnost.py", G, "Gemma-4-E2B-Q4_K_M", "podaci", "logovi/l8_server.txt",
           "grafovi/tocnost_zlatni.csv", "--no-rea")], izlazi=["grafovi/tocnost_zlatni.csv"]),
    "L9": dict(naslov="LoRA na CPU-u", trajanje=45, ovisi=[],
               obrisi=["grafovi/gubitak_glavni.csv", "grafovi/gubitak_prenaucen.csv", "models/l9"], koraci=[
        mjeri("l9_glavni.txt", PY, "-X", "utf8", "skripte/l9_trening.py", SM2, "podaci", "models/l9/glavni",
              "--epohe", "5", "--r", "8", "--lr", "5e-4", "--eval-svakih", "30"),
        kopiraj("models/l9/glavni/gubitak.csv", "grafovi/gubitak_glavni.csv"),
        mjeri("l9_prenaucen.txt", PY, "-X", "utf8", "skripte/l9_trening.py", SM2, "podaci", "models/l9/prenaucen",
              "--train-n", "20", "--val-n", "24", "--epohe", "20", "--r", "16", "--lr", "2e-3", "--eval-svakih", "5", "--bez-zlatnog"),
        kopiraj("models/l9/prenaucen/gubitak.csv", "grafovi/gubitak_prenaucen.csv"),
        bash("skripte/l9_lanac.sh")], izlazi=["grafovi/gubitak_glavni.csv", "models/l9/gguf/kvaka-Q4_K_M.gguf", "models/l9/spojeno_prenaucen"]),
    "L10": dict(naslov="Kirurgija i Mergekit", trajanje=5, ovisi=["L9"], obrisi=["models/l10"], koraci=[
        py("l10.txt", "skripte/l10_kirurgija.py", SM2, "models/l10"),
        bash("skripte/l10_mergekit.sh"), bash("skripte/l10_mergekit2.sh"),
        py("l10_mergekit_provjera.txt", "skripte/l10_provjera_spoja.py", "models/l10/mk/izlaz_linear", "podaci"),
        py("l10_mergekit_provjera.txt", "skripte/l10_provjera_spoja.py", "models/l10/mk/izlaz_dare", "podaci", dodaj=True)],
        izlazi=["logovi/l10.txt", "models/l10/mk/izlaz_linear/tokenizer.json", "models/l10/mk/izlaz_dare/tokenizer.json"]),
    "L11": dict(naslov="Opterećenje poslužitelja", trajanje=15, ovisi=[], obrisi=["grafovi/opterecenje.csv"], koraci=[
        py("l11.txt", "skripte/l11_opterecenje.py", G, "logovi/l11_server.txt", "grafovi/opterecenje.csv")],
        izlazi=["grafovi/opterecenje.csv"]),
    "L12": dict(naslov="RAG i podmetnuta naredba", trajanje=10, ovisi=[], obrisi=[], koraci=[
        py("l12.txt", "skripte/l12_rag.py", G, BGE, GRAN, "podaci/kvaka_prirucnik.md", "logovi/l12_server.txt"),
        py("l12b.txt", "skripte/l12b_injekcija.py", G, "logovi/l12b_server.txt")], izlazi=["logovi/l12.txt", "logovi/l12b.txt"]),
}

# strogo: (stupac, "tocno" | "apsolutno" | "relativno", granica). Ostali stupci ovise o stroju i samo se prikazuju.
PROVJERE = {
    "kvantizacija_velicina": dict(kljuc=["tip", "imatrix"], strogo=[("bajtova", "relativno", 0.001)], stroj=["quant_s", "peakWS_MB"]),
    "kvantizacija_ppl": dict(kljuc=["tip", "tekst"], strogo=[("ppl", "relativno", 0.02), ("chunks", "tocno", 0)], stroj=["sekunde", "peakWS_MB"]),
    "kvantizacija_brzina": dict(kljuc=["tip"], strogo=[], stroj=["prefill_tok_s", "gen_tok_s", "peakWS_MB"]),
    "memorija_kontekst": dict(kljuc=["model", "c", "args", "parallel"], strogo=[("kv_prijavljeno_MiB", "relativno", 0.05)], stroj=["peakWS_MB"]),
    "tocnost_zlatni": dict(kljuc=["model", "nacin"], strogo=[("n", "tocno", 0), ("valjan_json", "apsolutno", 2), ("tocnost_polje", "apsolutno", 0.05)], stroj=["p50_s", "p95_s"]),
    "opterecenje": dict(kljuc=["parallel", "klijenti", "kvu"], strogo=[("n_ctx_slot", "tocno", 0)], stroj=["lat_p95_s", "tps_ukupno", "peakWS_MB"]),
    "gubitak_glavni": dict(kljuc=["korak"], strogo=[("val_loss", "relativno", 0.25)], stroj=["sekunde"], samo_zadnji=True),
    "gubitak_prenaucen": dict(kljuc=["korak"], strogo=[("val_loss", "relativno", 0.25)], stroj=["sekunde"], samo_zadnji=True),
}


def nadi_bash():
    for k in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files (x86)\Git\bin\bash.exe"):
        if os.path.exists(k):
            return k
    git = shutil.which("git")
    if git:
        k = Path(git).resolve().parent.parent / "bin" / "bash.exe"
        if k.exists():
            return str(k)
    sys.exit("Nema Git Basha. Instaliraj Git for Windows.")


def preuzmi(url, cilj):
    print(f"  preuzimam {url}", flush=True)
    z = urllib.request.Request(url, headers={"User-Agent": "llm-prirucnik-vjezbe/1.0"})
    with urllib.request.urlopen(z, timeout=120) as r, open(cilj, "wb") as f:
        shutil.copyfileobj(r, f)


def sazetak(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for d in iter(lambda: f.read(2**20), b""):
            h.update(d)
    return h.hexdigest()


def je_u_oblaku(p):
    s = str(p).lower()
    return any(o in s for o in ("my drive", "google drive", "onedrive", "dropbox", "icloud"))


def priprema(a):
    if sys.platform != "win32":
        sys.exit("Skripte vježbi zasad rade samo na Windowsu (mjeri.py, .exe alati).")
    rad = Path(a.mapa).resolve()
    if je_u_oblaku(rad):
        sys.exit(f"{rad} izgleda kao mapa koja se sinkronizira u oblak. Izaberi lokalni disk.")
    nadi_bash()
    rad.mkdir(parents=True, exist_ok=True)
    slobodno = shutil.disk_usage(rad).free / 1e9
    print(f"Radna mapa: {rad}; slobodno {slobodno:.0f} GB (sve vježbe trebaju oko 40 GB)", flush=True)
    if slobodno < 40:
        print("  UPOZORENJE: moglo bi ponestati mjesta.", flush=True)
    for m in ("logovi", "grafovi", "models/tekst", "models/smol3", "llama", "llama-src"):
        (rad / m).mkdir(parents=True, exist_ok=True)
    for iz, u in (("podaci", "podaci"), ("vjezbe", "skripte"), ("okruzenje", "okruzenje")):
        shutil.copytree(PRILOZI / iz, rad / u, dirs_exist_ok=True)
    for f in (PRILOZI / "podaci" / "tekst").glob("*.txt"):
        shutil.copy2(f, rad / "models" / "tekst" / f.name)

    ll = VERZIJE["llama_cpp"]
    zp = rad / "llama" / Path(ll["paket"]["url"]).name
    if not (rad / "llama" / "llama-server.exe").exists():
        if not zp.exists():
            preuzmi(ll["paket"]["url"], zp)
        if sazetak(zp) != ll["paket"]["sha256"]:
            sys.exit(f"Kontrolni zbroj ne odgovara: {zp}")
        zipfile.ZipFile(zp).extractall(rad / "llama")
    if not (rad / "llama-src" / ll["izvor"]["mapa"]).exists():
        zs = rad / "llama-src" / "src.zip"
        if not zs.exists():
            preuzmi(ll["izvor"]["url"], zs)
        # Web sučelje nije potrebno, a njegove duge putanje na Windowsu ruše raspakiranje.
        with zipfile.ZipFile(zs) as z:
            z.extractall(rad / "llama-src", [n for n in z.namelist() if "/tools/ui/" not in n])

    if not (rad / PY).exists():
        p = shutil.which("py")
        trazi = VERZIJE["python"].rsplit(".", 1)[0]
        n = [p, f"-{trazi}"] if p else [sys.executable]
        subprocess.run([*n, "-m", "venv", str(rad / "venv")], check=True)
    subprocess.run([str(rad / PY), "-m", "pip", "install", "--disable-pip-version-check", "-r",
                    str(rad / "okruzenje" / "requirements.txt")], check=True)

    izvor = Path(a.izvor_modela).resolve() if a.izvor_modela else None
    za_preuzeti = []
    for kljuc, m in VERZIJE["modeli"].items():
        ime = m["repo"].split("/")[1]
        cilj = rad / "models" / ime
        if not izvor or kljuc in a.preuzmi:
            za_preuzeti.append(kljuc)
        elif (izvor / ime).exists() and not cilj.exists():
            subprocess.run(["cmd", "/c", "mklink", "/J", str(cilj), str(izvor / ime)], check=True, stdout=subprocess.DEVNULL)
            print(f"  {ime}: povezano iz {izvor}", flush=True)
        elif not cilj.exists():
            za_preuzeti.append(kljuc)
    if za_preuzeti:
        subprocess.run([str(rad / PY), "-X", "utf8", str(rad / "skripte" / "preuzmi.py"), str(rad / "models"), *za_preuzeti],
                       cwd=rad, check=True)
    print("Priprema je gotova.", flush=True)


def izvedi(k, rad, bash_exe, okolina):
    if "kopiraj" in k:
        iz, u = k["kopiraj"]
        shutil.copy2(rad / iz, rad / u)
        return 0
    if "bash" in k:
        return subprocess.run([bash_exe, *k["bash"]], cwd=rad, env=okolina).returncode
    naredba = [str(rad / k["naredba"][0]), *k["naredba"][1:]]
    if "log" not in k:
        return subprocess.run(naredba, cwd=rad, env=okolina).returncode
    with open(rad / k["log"], "ab" if k.get("dodaj") else "wb") as f:
        return subprocess.run(naredba, cwd=rad, env=okolina, stdout=f, stderr=subprocess.STDOUT).returncode


def pokreni(a):
    rad = Path(a.mapa).resolve()
    if not (rad / PY).exists():
        sys.exit("Prvo pokreni naredbu priprema.")
    bash_exe = nadi_bash()
    okolina = {**os.environ, "PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1"}
    gotovo = rad / "logovi" / ".gotovo"
    gotovo.mkdir(exist_ok=True)
    trazene = list(VJEZBE) if "sve" in a.vjezbe else [v.upper() for v in a.vjezbe]
    nepoznate = [v for v in trazene if v not in VJEZBE]
    if nepoznate:
        sys.exit(f"Nepoznate vježbe: {nepoznate}. Popis daje naredba popis.")
    neuspjele = []
    for v in VJEZBE:  # redoslijed iz VJEZBE poštuje ovisnosti
        if v not in trazene:
            continue
        d = VJEZBE[v]
        oznaka = gotovo / v
        if oznaka.exists() and not a.ponovi:
            print(f"[{v}] već gotovo, preskačem (--ponovi pokreće iznova)", flush=True)
            continue
        fali = [o for o in d["ovisi"] if not (gotovo / o).exists()]
        if fali:
            print(f"[{v}] NIJE POKRENUTO: prvo treba {fali}", flush=True)
            neuspjele.append(v)
            continue
        print(f"[{v}] {d['naslov']} (na mjernom stroju oko {d['trajanje']} min) {datetime.now():%H:%M}", flush=True)
        for o in d["obrisi"]:
            p = rad / o
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
        t = time.time()
        kodovi = [izvedi(k, rad, bash_exe, okolina) for k in d["koraci"]]
        fale = [o for o in d["izlazi"] if not (rad / o).exists()]
        if fale or any(kodovi):
            print(f"[{v}] GREŠKA: izlazni kodovi {kodovi}, nedostaju {fale}. Pogledaj logovi/.", flush=True)
            neuspjele.append(v)
            oznaka.unlink(missing_ok=True)
        else:
            oznaka.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
            print(f"[{v}] gotovo za {(time.time() - t) / 60:.1f} min", flush=True)
    print("Neuspjele vježbe: " + ", ".join(neuspjele) if neuspjele else "Sve tražene vježbe su prošle.", flush=True)
    return 1 if neuspjele else 0


def broj(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def citaj_csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ocijeni(nacin, granica, ref, nov):
    if nacin == "tocno" and ref == nov:
        return True
    a, b = broj(ref), broj(nov)
    if a is None or b is None:
        return (ref or "") == (nov or "")
    if nacin == "tocno":
        return a == b
    if nacin == "apsolutno":
        return abs(a - b) <= granica
    return a == b if a == 0 else abs(a - b) / abs(a) <= granica


def usporedi(a):
    rad = Path(a.mapa).resolve()
    strogo, stroj, nije = [], [], []
    for ime, pr in PROVJERE.items():
        nov_p = rad / "grafovi" / f"{ime}.csv"
        if not nov_p.exists():
            nije.append(ime)
            continue
        ref, nov = citaj_csv(PRILOZI / "grafovi" / f"{ime}.csv"), citaj_csv(nov_p)
        kljuc = lambda r: " / ".join((r.get(k) or "-") for k in pr["kljuc"])
        novi = {kljuc(r): r for r in nov}  # zadnji red vrijedi kad je vježba ponavljana
        if pr.get("samo_zadnji"):
            ref = ref[-1:]
        for r in ref:
            kl, n = kljuc(r), novi.get(kljuc(r))
            if n is None:
                strogo.append((ime, kl, "(red)", "postoji", "nedostaje", False))
                continue
            for st, nacin, gr in pr["strogo"]:
                strogo.append((ime, kl, st, r.get(st, ""), n.get(st, ""), ocijeni(nacin, gr, r.get(st), n.get(st))))
            for st in pr["stroj"]:
                x, y = broj(r.get(st)), broj(n.get(st))
                if x and y is not None:
                    stroj.append((ime, kl, st, r[st], n[st], y / x))

    for ime in ("train.jsonl", "val.jsonl"):  # sjeme 42 mora dati iste bajtove
        if (rad / "logovi" / ".gotovo" / "L7").exists():
            x, y = sazetak(PRILOZI / "podaci" / ime), sazetak(rad / "podaci" / ime)
            strogo.append(("L7 podaci", ime, "sha256", x[:12], y[:12], x == y))
    for ime in ("l2.txt", "l3.txt"):
        p = rad / "logovi" / ime
        if p.exists():
            cisti = lambda t: [r.rstrip() for r in t.splitlines() if r.strip() and not r.startswith(("[transformers]", "Warning"))]
            x = cisti((PRILOZI / "okruzenje" / "referenca" / ime).read_text(encoding="utf-8", errors="replace"))
            y = cisti(p.read_text(encoding="utf-8", errors="replace"))
            razlika = sum(1 for u, v in zip(x, y) if u != v) + abs(len(x) - len(y))
            strogo.append(("logovi", ime, "različiti reci", "0", str(razlika), razlika == 0))

    p = rad / "logovi" / "l10_mergekit_provjera.txt"
    if p.exists():  # dare_ties namjerno daje loš model, pa je i njegov gubitak dio provjere
        t = p.read_text(encoding="utf-8", errors="replace")
        for ime, ref in (("izlaz_linear", "0.3037"), ("izlaz_dare", "1.7574")):
            m = re.search(ime + r" val gubitak \(30 primjera\) ([\d.]+)", t)
            nov = m.group(1) if m else ""
            strogo.append(("L10 spajanje", ime, "val_loss", ref, nov or "nedostaje", ocijeni("relativno", 0.25, ref, nov)))

    pale = [r for r in strogo if not r[5]]
    izl = ["# Usporedba s mjerenjima iz knjige", "",
           f"Datum: {datetime.now():%d. %m. %Y. %H:%M}  ", f"Procesor: {platform.processor() or 'nepoznat'}  ",
           f"Referenca: llama.cpp {VERZIJE['llama_cpp']['oznaka']}, mjerenja od {VERZIJE['datum_mjerenja']}", "",
           f"**Stroge provjere: {len(strogo) - len(pale)} od {len(strogo)} prošlo.**", ""]
    if nije:
        izl += ["Nije pokrenuto: " + ", ".join(f"`{n}`" for n in nije), ""]
    tablica = ["| Izvor | Stavka | Mjera | Knjiga | Sada |", "|---|---|---|---|---|"]
    if pale:
        izl += ["## Odstupanja koja treba pregledati", "",
                "Prije izmjene knjige provjeri je li razlika stvarna: točnost i gubitak mogu se malo razlikovati među procesorima.", "",
                *tablica, *[f"| {i} | {k} | {s} | {x} | {y} |" for i, k, s, x, y, _ in pale], ""]
    if stroj:
        izl += ["## Brzina i memorija", "",
                "Ovise o stroju, pa ne utječu na ishod. Na istom su se računalu u istom danu brzine razlikovale i do dva puta.", "",
                "| Izvor | Stavka | Mjera | Knjiga | Sada | Omjer |", "|---|---|---|---|---|---|",
                *[f"| {i} | {k} | {s} | {x} | {y} | {o:.2f} |" for i, k, s, x, y, o in stroj], ""]
    izvj = rad / "izvjestaj.md"
    izvj.write_text("\n".join(izl), encoding="utf-8")
    print(f"Stroge provjere: {len(strogo) - len(pale)} od {len(strogo)} prošlo. Nije pokrenuto: {nije or 'ništa'}.")
    for i, k, s, x, y, _ in pale:
        print(f"  ODSTUPANJE {i} | {k} | {s}: knjiga {x}, sada {y}")
    print(f"Izvještaj: {izvj}")
    return 1 if pale else 0


def popis(_):
    print(f"llama.cpp {VERZIJE['llama_cpp']['oznaka']}, Python {VERZIJE['python']}. Trajanja vrijede za mjerni stroj (i5-10210U).\n")
    for v, d in VJEZBE.items():
        ov = f"  (treba {', '.join(d['ovisi'])})" if d["ovisi"] else ""
        print(f"{v:4} {d['trajanje']:>3} min  {d['naslov']}{ov}")
    print(f"\nUkupno oko {sum(d['trajanje'] for d in VJEZBE.values()) / 60:.1f} h.")
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = a.add_subparsers(dest="naredba", required=True)
    s.add_parser("popis").set_defaults(f=popis)
    p = s.add_parser("priprema")
    p.add_argument("mapa")
    p.add_argument("--izvor-modela", help="mapa s već preuzetim modelima; povezuju se umjesto preuzimanja")
    p.add_argument("--preuzmi", nargs="*", default=[], help="uz --izvor-modela: modeli koje ipak treba preuzeti")
    p.set_defaults(f=priprema)
    p = s.add_parser("pokreni")
    p.add_argument("mapa")
    p.add_argument("vjezbe", nargs="+", help="sve ili npr. L3 L7")
    p.add_argument("--ponovi", action="store_true")
    p.set_defaults(f=pokreni)
    p = s.add_parser("usporedi")
    p.add_argument("mapa")
    p.set_defaults(f=usporedi)
    a = a.parse_args()
    sys.exit(a.f(a) or 0)


if __name__ == "__main__":
    main()
