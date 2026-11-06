import collections, json, os, re, sys, unicodedata

m = sys.argv[1]

def ucitaj(ime):
    r = []
    for red in open(os.path.join(m, ime), encoding="utf-8"):
        x = json.loads(red)
        if "tekst" in x:
            r.append((x["tekst"], x["ocekivano"]))
        else:
            p = x["messages"]
            r.append((p[1]["content"], json.loads(p[2]["content"])))
    return r

def kljuc(t):  # bez velikih slova, dijakritika, brojeva, interpunkcije
    t = unicodedata.normalize("NFD", t.lower().replace("đ", "d"))
    t = "".join(z for z in t if not unicodedata.combining(z))
    return " ".join(re.findall(r"[a-z]+", t))

def trigrami(t):
    w = re.findall(r"\w+", t.lower())
    return {tuple(w[i:i+3]) for i in range(len(w) - 2)}

tr, va, zl = map(ucitaj, ("train.jsonl", "val.jsonl", "zlatni.jsonl"))
K = collections.Counter(kljuc(t) for t, _ in tr)
print("bliski duplikati u train:", sum(n - 1 for n in K.values()))
print("val blizak train:", sum(kljuc(t) in K for t, _ in va))
A = set().union(*(trigrami(t) for t, _ in tr))
for ime, s in (("val", va), ("zlatni", zl)):
    u = [len(trigrami(t) & A) / max(1, len(trigrami(t))) for t, _ in s]
    print(f"trigrami {ime} u train: {sum(u) / len(u):.3f}")
for ime, s in (("train", tr), ("val", va), ("zlatni", zl)):
    c = collections.Counter(o["hitnost"] for _, o in s)
    print(ime, dict(sorted(c.items())))
