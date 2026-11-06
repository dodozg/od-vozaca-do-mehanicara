# L6: kvantizacija i mjerenje štete. Faze se pokreću zasebno da se vrijeme može rasporediti.
#   python l6_kvantizacija.py quant F16.gguf MAPA LOG CSV Q8_0 Q6_K ...
#   python l6_kvantizacija.py bench MAPA LOG CSV Q8_0 Q6_K ...
#   python l6_kvantizacija.py ppl   MAPA LOG CSV TEKST.txt OZNAKA F16 Q8_0 ...
import csv, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mjeri
b = lambda ime: os.path.abspath(f"llama/{ime}.exe")
faza = sys.argv[1]
def zapisi(put, red, zaglavlje):
    nov = not os.path.exists(put)
    with open(put, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nov: w.writerow(zaglavlje)
        w.writerow(red)
if faza == "quant":
    f16, mapa, log, cs = sys.argv[2:6]
    for t in sys.argv[6:]:
        im = None
        if ":" in t: t, im = t.split(":")   # npr. Q4_K_M:imatrix.gguf
        izl = os.path.join(mapa, f"SmolLM3-{t}{'-imat' if im else ''}.gguf")
        n = [b("llama-quantize"), *(["--imatrix", im] if im else []), f16, izl, t, "4"]
        rc, tr, ws, pv = mjeri.pokreni(n, log)
        v = os.path.getsize(izl)
        print(f"{t}{' imatrix' if im else ''}: exit {rc} {tr:.0f} s, {v:,} bajtova ({v/1e9:.2f} GB), peak WS {ws:.0f} MB, private {pv:.0f} MB", flush=True)
        zapisi(cs, [t, bool(im), v, round(tr,1), round(ws), round(pv)], ["tip","imatrix","bajtova","quant_s","peakWS_MB","peakPrivate_MB"])
elif faza == "bench":
    mapa, log, cs = sys.argv[2:5]
    for t in sys.argv[5:]:
        g = os.path.join(mapa, f"SmolLM3-{t}.gguf")
        lg = log + ".tmp"
        if os.path.exists(lg): os.remove(lg)
        rc, tr, ws, pv = mjeri.pokreni([b("llama-bench"), "-m", g, "-t", "4", "-p", "128", "-n", "32", "-r", "2", "-o", "csv"], lg)
        s = open(lg, encoding="utf-8", errors="replace").read(); open(log, "a", encoding="utf-8").write(s)
        redovi = [r for r in s.splitlines() if r.startswith('"') or r.startswith('build_commit')]
        zag = None; pre = gen = None
        for r in csv.reader(redovi):
            if r[0] == "build_commit": zag = r; continue
            d = dict(zip(zag, r))
            if d["n_prompt"] != "0": pre = float(d["avg_ts"]); pres = float(d["stddev_ts"])
            else: gen = float(d["avg_ts"]); gens = float(d["stddev_ts"])
        print(f"{t}: prefill {pre:.1f} +- {pres:.1f} tok/s, generiranje {gen:.2f} +- {gens:.2f} tok/s, peak WS {ws:.0f} MB, {tr:.0f} s", flush=True)
        zapisi(cs, [t, round(pre,2), round(pres,2), round(gen,2), round(gens,2), round(ws), round(pv)], ["tip","prefill_tok_s","prefill_sd","gen_tok_s","gen_sd","peakWS_MB","peakPrivate_MB"])
elif faza == "ppl":
    mapa, log, cs, tekst, oznaka = sys.argv[2:7]
    for t in sys.argv[7:]:
        g = os.path.join(mapa, f"SmolLM3-{t}.gguf")
        lg = log + ".tmp"
        if os.path.exists(lg): os.remove(lg)
        rc, tr, ws, pv = mjeri.pokreni([b("llama-perplexity"), "-m", g, "-f", tekst, "-t", "4", "-c", "512", "-b", "512", "--no-mmap"] if False else [b("llama-perplexity"), "-m", g, "-f", tekst, "-t", "4", "-c", "512", "-b", "512"], lg)
        s = open(lg, encoding="utf-8", errors="replace").read(); open(log, "a", encoding="utf-8").write(s)
        m = re.search(r"Final estimate: PPL = ([\d.]+)(?: \+/- ([\d.]+))?", s); tok = re.search(r"tokenizing the input \.\.\.|calculating perplexity over (\d+) chunks, n_ctx=(\d+), batch_size=(\d+), n_seq=(\d+)", s)
        ch = re.search(r"over (\d+) chunks", s)
        print(f"{t} {oznaka}: PPL {m.group(1) if m else 'NEMA'} +- {m.group(2) if m and m.group(2) else '?'}, chunks {ch.group(1) if ch else '?'}, {tr:.0f} s, peak WS {ws:.0f} MB, exit {rc}", flush=True)
        zapisi(cs, [t, oznaka, m.group(1) if m else "", m.group(2) if m and m.group(2) else "", ch.group(1) if ch else "", round(tr), round(ws)], ["tip","tekst","ppl","ppl_plusminus","chunks","sekunde","peakWS_MB"])
