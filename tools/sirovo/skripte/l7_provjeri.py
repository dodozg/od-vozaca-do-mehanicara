# L7: provjera skupova. Broji primjere, raspodjele i preklapanje zlatnog skupa s treningom.
# Pokretanje: python l7_provjeri.py MAPA_PODATAKA
import json, collections, re, sys, os
m = sys.argv[1]
uc = lambda ime: [json.loads(l) for l in open(os.path.join(m, ime), encoding="utf-8")]
g, tr, va = uc("zlatni.jsonl"), uc("train.jsonl"), uc("val.jsonl")
print("zlatni", len(g), "train", len(tr), "val", len(va))
sh = json.load(open(os.path.join(m, "shema.json"), encoding="utf-8"))["properties"]
for x in g:
    for k, v in x["ocekivano"].items():
        assert v in sh[k]["enum"], (x["id"], k, v)
print("sve vrijednosti zlatnog skupa su u shemi")
for k in ["uredaj", "kvar", "dio", "hitnost"]:
    print("zlatni", k, collections.Counter(x["ocekivano"][k] for x in g).most_common())
    print("train ", k, collections.Counter(json.loads(x["messages"][2]["content"])[k] for x in tr).most_common())
def tg(s):
    w = re.findall(r"\w+", s.lower()); return {tuple(w[i:i+3]) for i in range(len(w)-2)}
A = set().union(*[tg(x["messages"][1]["content"]) for x in tr])
o = [len(tg(x["tekst"]) & A)/max(1, len(tg(x["tekst"]))) for x in g]
print("udio trigrama rijeci zlatnog skupa koji postoje i u treningu: prosjek %.3f, najvise %.3f" % (sum(o)/len(o), max(o)))
L = [len(x["messages"][1]["content"].split()) for x in tr]; print("rijeci po zapisniku, train: prosjek %.1f, min %d, max %d" % (sum(L)/len(L), min(L), max(L)))
L = [len(x["tekst"].split()) for x in g]; print("rijeci po zapisniku, zlatni: prosjek %.1f, min %d, max %d" % (sum(L)/len(L), min(L), max(L)))
print("duplikati train+val:", 300-len({x["messages"][1]["content"] for x in tr+va}))
print("primjeri train:"); [print("  ", x["messages"][1]["content"], "=>", x["messages"][2]["content"]) for x in tr[:8]]
