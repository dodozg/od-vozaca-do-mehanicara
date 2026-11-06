# L5: memorija. Za svaki model i -c mjeri vršni RSS i ono što llama.cpp sam prijavi za KV cache,
# zatim uspoređuje s formulom 2*c*L*h*d*b/8. Na kraju utjecaj broja dretvi (llama-bench).
# Pokretanje: python l5_memorija.py LOG CSV model1.gguf model2.gguf ...
import csv, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mjeri
LOG, CSV_, modeli = sys.argv[1], sys.argv[2], sys.argv[3:]
with open(CSV_, "a", newline="", encoding="utf-8") as cf:
    w = csv.writer(cf); w.writerow("model c args parallel peakWS_MB peakPrivate_MB kv_prijavljeno_MiB kv_retci graph_MiB output_MiB model_buf_MiB repack_MiB".split())
    for gg in modeli:
        for c, dodatno in [(2048,[]),(8192,[]),(32768,[]),(8192,["-ctk","q8_0"]),(8192,["-np","4"]),(8192,["-lm","none"]),(8192,["-fa","off"])]:
            log1 = LOG + ".tmp"
            if os.path.exists(log1): os.remove(log1)
            n = [os.path.abspath("llama/llama-completion.exe"), "-m", gg, "-no-cnv", "-p", "Perilica rublja", "-n", "8", "-c", str(c), "-t", "4", "-v", "--no-display-prompt", *dodatno]
            rc, tr, ws, pv = mjeri.pokreni(n, log1)
            t = open(log1, encoding="utf-8", errors="replace").read()
            # zadržimo samo redove bitne za memoriju
            kv = re.findall(r"llama_kv_cache: +size = +([\d.]+) MiB \( *(\d+) cells, +(\d+) layers?, +(\d+)/(\d+) seqs\), K \(([^)]*)\): +([\d.]+) MiB, V \(([^)]*)\): +([\d.]+) MiB", t)
            graf = re.findall(r"graph.*?size *= *([\d.]+) MiB|CPU compute buffer size = +([\d.]+) MiB", t)
            izl = re.findall(r"output buffer size = +([\d.]+) MiB", t)
            buf = re.findall(r"CPU model buffer size = +([\d.]+) MiB", t); rep = re.findall(r"CPU_REPACK model buffer size = +([\d.]+) MiB", t)
            arg = " ".join(dodatno)
            print(f"\n### {os.path.basename(gg)} -c {c} {arg} exit={rc} wall={tr:.1f}s peakWS={ws:.0f} MB peakPrivate={pv:.0f} MB", flush=True)
            for red in t.splitlines():
                if re.search(r"llama_kv_cache(_iswa)?:( +size| creating)|n_ctx_seq +=|n_seq_max|compute buffer|memory_breakdown|print_info: (n_layer |n_head |n_embd |n_embd_k_gqa|n_swa |n_embd_head_k|file size|model params|n_head_kv)|memory_breakdown|llama_memory", red) and "D load_tensors" not in red:
                    print("  ", re.sub(r"^\S+ \S ", "", red)[:170])
            kv = kv[len(kv)//2:]  # alat prvo prođe "suhi" prolaz za --fit pa isti redovi dolaze dvaput; uzimamo drugi
            k = sum(float(x[0]) for x in kv)
            w.writerow([os.path.basename(gg), c, arg, "4" if "-np" in dodatno else "1", round(ws), round(pv), round(k,2), "+".join(x[1] for x in kv),
                        graf[-1][1] if graf else "", izl[-1] if izl else "", buf[-1] if buf else "", rep[-1] if rep else ""])
            cf.flush()
