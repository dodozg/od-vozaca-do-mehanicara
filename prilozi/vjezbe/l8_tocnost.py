# L8: točnost po polju na zlatnom skupu, preko llama-servera.
# Svaki način: s JSON shemom (json_schema) i bez nje (samo prompt).
# Pokretanje: python l8_tocnost.py MODEL.gguf NAZIV MAPA_PODATAKA LOG CSV [--bez-razmisljanja] [--broj N] [--nacini shema,prompt]
import argparse, csv, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posluzitelj import Posluzitelj
a = argparse.ArgumentParser()
a.add_argument("model"); a.add_argument("naziv"); a.add_argument("podaci"); a.add_argument("log"); a.add_argument("csv")
a.add_argument("--broj", type=int, default=40); a.add_argument("--nacini", default="shema,prompt"); a.add_argument("--port", type=int, default=8091); a.add_argument("--max", type=int, default=90)
a.add_argument("--no-rea", action="store_true"); a.add_argument("--ispis", type=int, default=5); a.add_argument("--sustav-tekst", default=None)
a = a.parse_args()
SUSTAV = open(os.path.join(a.podaci, "sustav.txt"), encoding="utf-8").read()
if a.sustav_tekst: SUSTAV = a.sustav_tekst
SHEMA = json.load(open(os.path.join(a.podaci, "shema.json"), encoding="utf-8"))
ZLATNI = [json.loads(l) for l in open(os.path.join(a.podaci, "zlatni.jsonl"), encoding="utf-8")][:a.broj]
POLJA = ["uredaj", "kvar", "dio", "hitnost"]
def izvuci(t):
    # uzmi prvi {...} iz odgovora; model bez sheme često doda ```json ili objašnjenje
    if t is None: return None
    m = re.search(r"\{.*?\}", t, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except json.JSONDecodeError: return None
args = ["-c", 8192, "-t", 4, "-np", 1]
if a.no_rea: args += ["--reasoning", "off"]
with Posluzitelj(a.model, a.log, port=a.port, args=args) as s:
    print(f"### {a.naziv}: ucitavanje {s.ucitavanje_s:.1f} s", flush=True)
    for nacin in a.nacini.split(","):
        tocno = {k: 0 for k in POLJA}; cijeli = 0; valjano = 0; t0 = time.time(); vr = []; gen = []; pre = []; primjeri = []
        for z in ZLATNI:
            tijelo = {"messages":[{"role":"system","content":SUSTAV},{"role":"user","content":z["tekst"]}], "max_tokens":a.max, "temperature":0, "seed":1}
            if nacin == "shema": tijelo["response_format"] = {"type":"json_schema","json_schema":{"name":"zapisnik","strict":True,"schema":SHEMA}}
            t = time.time()
            r = s.post("/v1/chat/completions", tijelo)
            vr.append(time.time()-t)
            c = r["choices"][0]["message"].get("content"); o = izvuci(c)
            gen.append(r["timings"]["predicted_per_second"]); pre.append(r["timings"]["prompt_per_second"])
            if o is not None: valjano += 1
            d = {k: (str(o.get(k, "")).strip().lower() if o else "") for k in POLJA}
            ok = {k: d[k] == z["ocekivano"][k] for k in POLJA}
            for k in POLJA: tocno[k] += ok[k]
            cijeli += all(ok.values())
            primjeri.append((z["id"], c, sum(ok.values())))
        n = len(ZLATNI); vr2 = sorted(vr)
        ukupna = sum(tocno.values())/(4*n)
        print(f"\n== {a.naziv} / {nacin}: n={n} valjan JSON {valjano}/{n}  tocnost po polju {ukupna*100:.1f} %  cijeli zapisnik {cijeli}/{n}", flush=True)
        print("   po polju:", {k: f"{v}/{n}" for k, v in tocno.items()})
        print(f"   latencija p50 {vr2[n//2]:.1f} s, p95 {vr2[int(n*.95)]:.1f} s, ukupno {time.time()-t0:.0f} s, generiranje medijan {sorted(gen)[n//2]:.1f} tok/s, peak WS {s.memorija_mb()[0]:.0f} MB")
        for p in primjeri[:a.ispis]: print("   primjer", p[0], f"{p[2]}/4", repr(p[1])[:220])
        nov = not os.path.exists(a.csv)
        with open(a.csv, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if nov: w.writerow("model nacin n valjan_json tocnost_polje uredaj kvar dio hitnost cijeli p50_s p95_s".split())
            w.writerow([a.naziv, nacin, n, valjano, round(ukupna,3), *[tocno[k] for k in POLJA], cijeli, round(vr2[n//2],1), round(vr2[int(n*.95)],1)])
        with open(a.log + f".{a.naziv}.{nacin}.json", "w", encoding="utf-8") as f: json.dump(primjeri, f, ensure_ascii=False, indent=0)
