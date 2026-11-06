# Preuzima modele za vježbe u zadanu mapu, bez tokena i samo nezaključane modele.
# Revizije i kontrolni zbrojevi dolaze iz ../okruzenje/verzije.json, pa se preuzima ono što je mjereno.
# Primjer: python preuzmi.py MAPA qwen gemma smol3 smol2 bge granite
import hashlib, json, os, sys, time
from huggingface_hub import hf_hub_download, snapshot_download
os.environ.pop("HF_TOKEN", None)
put = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "okruzenje", "verzije.json")
if not os.path.exists(put):
    sys.exit(f"Nema {put}. Kopiraj mapu prilozi/okruzenje uz mapu skripte.")
MODELI = json.load(open(put, encoding="utf-8"))["modeli"]
korijen = sys.argv[1]
def sazetak(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for d in iter(lambda: f.read(2**20), b""): h.update(d)
    return h.hexdigest()
greske = 0
for korak in sys.argv[2:]:
    m = MODELI[korak]
    mapa = os.path.join(korijen, m["repo"].split("/")[1])
    t = time.time()
    try:
        if "datoteka" in m:
            p = hf_hub_download(m["repo"], m["datoteka"], revision=m["revizija"], local_dir=mapa, token=False)
            if sazetak(p) != m["sha256"]:
                raise RuntimeError(f"kontrolni zbroj ne odgovara: {p}")
        else:
            p = snapshot_download(m["repo"], revision=m["revizija"], allow_patterns=m["uzorci"], local_dir=mapa, token=False)
        print(m["repo"], "gotovo", p, round(time.time() - t), "s", flush=True)
    except Exception as e:
        greske += 1
        print("GRESKA", korak, repr(e)[:800], flush=True)
sys.exit(1 if greske else 0)
