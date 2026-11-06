# L11: test opterećenja llama-servera, samo standardna biblioteka.
# Mjeri TTFT (vrijeme do prvog tokena), tok/s po klijentu, ukupno tok/s, p50/p95 latenciju.
# Pokretanje: python l11_opterecenje.py MODEL.gguf LOG CSV
import csv, json, os, statistics, sys, threading, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posluzitelj import Posluzitelj
MODEL, LOG, CSV_ = sys.argv[1:4]
MAXT = 48
UREDAJI = ["perilica rublja", "perilica posuđa", "hladnjak", "zamrzivač", "pećnica", "sušilica", "bojler", "napa"]
def klijent(url, i, rez):
    # svaki klijent ima drukčiji početak poruke, da se prompt cache ne dijeli između slotova
    tijelo = {"messages":[{"role":"user","content":f"Klijent {i}: {UREDAJI[i%8]} se pokvarila. Napiši kratak popis od pet koraka za provjeru kvara na ovom uređaju, svaki korak jednom rečenicom."}],
              "max_tokens":MAXT,"temperature":0.7,"seed":i,"stream":True,"stream_options":{"include_usage":True},"ignore_eos":True}
    z = urllib.request.Request(url + "/v1/chat/completions", json.dumps(tijelo, ensure_ascii=False).encode("utf-8"), {"Content-Type":"application/json"})
    t0 = time.time(); prvi = None; n = 0
    with urllib.request.urlopen(z, timeout=1200) as r:
        for red in r:
            if not red.startswith(b"data: ") or red.startswith(b"data: [DONE]"): continue
            d = json.loads(red[6:])
            if d.get("choices") and d["choices"][0]["delta"].get("content"):
                if prvi is None: prvi = time.time()
                n += 1
    k = time.time()
    rez.append({"ttft":prvi-t0,"lat":k-t0,"n":n,"tps":(n-1)/(k-prvi) if k>prvi else 0})
cf = open(CSV_, "w", newline="", encoding="utf-8"); w = csv.writer(cf)
w.writerow("parallel klijenti kvu n_ctx_slot ttft_p50_s ttft_p95_s lat_p50_s lat_p95_s tps_po_klijentu_medijan tps_ukupno peakWS_MB".split())
def p(v, q):
    v = sorted(v); return v[min(len(v)-1, int(q*len(v)))]
SLUCAJ = [(1,[1,4],[]),(2,[2,4],[]),(4,[4,8],[]),(4,[4],["--no-kv-unified"])]
for np_, klijenti, dod in SLUCAJ:
    with Posluzitelj(MODEL, LOG, port=8094, args=["-c",8192,"-t",4,"-np",np_,"--reasoning","off",*dod]) as s:
        props = s.get("/props")
        slot = s.get("/slots")
        print(f"\n### --parallel {np_} {dod}: total_slots={props.get('total_slots')}, n_ctx po slotu={slot[0].get('n_ctx')}", flush=True)
        for N in klijenti:
            ponovi = 1 if N >= 8 else 2
            svi = []; t0 = time.time()
            niti = [threading.Thread(target=lambda i=i: [klijent(s.url, i+100*j, svi) for j in range(ponovi)]) for i in range(N)]
            [t.start() for t in niti]; [t.join() for t in niti]
            uk = time.time()-t0; ntok = sum(x["n"] for x in svi)
            red = [np_, N, "" if not dod else "ne", slot[0].get("n_ctx"), round(p([x["ttft"] for x in svi],.5),2), round(p([x["ttft"] for x in svi],.95),2), round(p([x["lat"] for x in svi],.5),2), round(p([x["lat"] for x in svi],.95),2),
                   round(statistics.median(x["tps"] for x in svi),2), round(ntok/uk,2), round(s.memorija_mb()[0])]
            w.writerow(red); cf.flush()
            print(f"  klijenata {N} zahtjeva {len(svi)} tokena {ntok}: TTFT p50 {red[4]} s p95 {red[5]} s | latencija p50 {red[6]} s p95 {red[7]} s | po klijentu {red[8]} tok/s | ukupno {red[9]} tok/s | peak WS {red[10]} MB", flush=True)
