# L2: mapa modela. Ispisuje datoteke, ključna polja config.json i čita safetensors zaglavlje samo
# standardnom bibliotekom, bez učitavanja težina.
# Pokretanje: python l2_mapa_modela.py MAPA_MODELA
import json, os, struct, sys, glob, collections, math
m = sys.argv[1]
print("== datoteke")
ukupno = 0
for f in sorted(os.listdir(m)):
    p = os.path.join(m, f)
    if os.path.isfile(p):
        print(f"{os.path.getsize(p):>14,}  {f}"); ukupno += os.path.getsize(p)
print(f"{ukupno:>14,}  UKUPNO ({ukupno/1e9:.2f} GB)")
print("== config.json")
c = json.load(open(os.path.join(m, "config.json"), encoding="utf-8"))
for k in ["architectures","model_type","vocab_size","hidden_size","intermediate_size","num_hidden_layers","num_attention_heads","num_key_value_heads","head_dim",
          "max_position_embeddings","torch_dtype","dtype","rope_scaling","rope_parameters","tie_word_embeddings","hidden_act","layer_types","no_rope_layers","no_rope_layer_interval","use_sliding_window","sliding_window"]:
    if k in c:
        v = c[k]
        s = json.dumps(v)
        print(f"{k}: {s[:120]}{'...' if len(s)>120 else ''}")
print("== safetensors zaglavlja")
VEL = {"F64":8,"F32":4,"BF16":2,"F16":2,"U8":1,"I8":1,"I64":8,"I32":4,"BOOL":1}
tenzori = {}
for f in sorted(glob.glob(os.path.join(m, "*.safetensors"))):
    with open(f, "rb") as d:
        n = struct.unpack("<Q", d.read(8))[0]      # prvih 8 bajtova: duljina JSON zaglavlja
        z = json.loads(d.read(n))                  # zatim sam JSON
    meta = z.pop("__metadata__", None)
    print(os.path.basename(f), "duljina zaglavlja", n, "bajtova, tenzora", len(z), "metadata", meta)
    tenzori.update(z)
par, baj = 0, 0
vrste = collections.Counter(); skupine = collections.Counter(); oblici = collections.OrderedDict()
for ime, t in tenzori.items():
    k = math.prod(t["shape"]) if t["shape"] else 1
    par += k; baj += k*VEL[t["dtype"]]; vrste[t["dtype"]] += 1
    d = ime.split(".")
    if "layers" in d:
        i = d.index("layers"); kljuc = ".".join(d[i+2:])
        skupine[kljuc] += k
        if d[i+1] == "0": oblici[ime] = t
    else:
        skupine[ime] += k; oblici[ime] = t
print("dtype:", dict(vrste))
print("== prvi sloj i tenzori izvan slojeva (ime, oblik, dtype)")
for ime, t in oblici.items(): print(f"  {ime:<55} {str(t['shape']):<18} {t['dtype']}")
print("== parametri po skupini (svi slojevi zajedno)")
for k, v in skupine.most_common(): print(f"  {v:>14,}  {v/par*100:5.1f} %  {k}")
print(f"BROJ TENZORA {len(tenzori)}  PARAMETARA {par:,}  ({par/1e9:.3f} milijardi)  BAJTOVA PODATAKA {baj:,} ({baj/1e9:.3f} GB)")
