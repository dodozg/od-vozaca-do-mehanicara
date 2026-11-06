import json, os, sys

m = sys.argv[1]
ucitaj = lambda ime: open(os.path.join(m, ime), encoding="utf-8")
shema = json.load(ucitaj("shema.json"))["properties"]
sustav = ucitaj("sustav.txt").read()
gresaka = 0

def provjeri(p):
    if [x["role"] for x in p] != ["system", "user", "assistant"]:
        return "uloge"
    if p[0]["content"] != sustav:
        return "sistemska poruka"
    if not p[1]["content"].strip():
        return "prazan ulaz"
    try:
        o = json.loads(p[2]["content"])
    except json.JSONDecodeError:
        return "nije JSON"
    if list(o) != list(shema):
        return "polja ili redoslijed"
    for k, v in o.items():
        if v not in shema[k]["enum"]:
            return f"{k}={v}"

for ime in ("train.jsonl", "val.jsonl"):
    n = 0
    for br, red in enumerate(ucitaj(ime), 1):
        n += 1
        g = provjeri(json.loads(red)["messages"])
        if g:
            gresaka += 1
            print(ime, "redak", br, g)
    print(ime, "primjera", n)
print("gresaka", gresaka)
