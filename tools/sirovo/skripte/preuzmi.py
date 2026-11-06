# Preuzima modele za vjezbe u zadanu mapu. Bez tokena, samo nezakljucani modeli.
# Primjer: python preuzmi.py MAPA
import sys, time, os
from huggingface_hub import hf_hub_download, snapshot_download, HfApi
os.environ.pop("HF_TOKEN", None)
korijen = sys.argv[1]
api = HfApi(token=False)
def gguf(repo, ime_sadrzi):
    d = [f for f in api.list_repo_files(repo) if f.endswith(".gguf")]
    print(repo, "GGUF datoteke:", len(d), flush=True)
    izbor = [f for f in d if ime_sadrzi.lower() in f.lower() and "mmproj" not in f.lower()]
    print(" izbor:", izbor, flush=True)
    t = time.time()
    p = hf_hub_download(repo, izbor[0], local_dir=os.path.join(korijen, repo.split("/")[1]), token=False)
    print(" gotovo", p, os.path.getsize(p), round(time.time()-t), "s", flush=True)
def snap(repo, uzorci):
    t = time.time()
    p = snapshot_download(repo, allow_patterns=uzorci, local_dir=os.path.join(korijen, repo.split("/")[1]), token=False)
    print(repo, "gotovo", p, round(time.time()-t), "s", flush=True)
for korak in sys.argv[2:]:
    try:
        if korak == "qwen": gguf("Qwen/Qwen3-4B-GGUF", "Q4_K_M")
        if korak == "gemma": gguf("unsloth/gemma-4-E2B-it-GGUF", "Q4_K_M")
        if korak == "smol2": snap("HuggingFaceTB/SmolLM2-135M-Instruct", ["*.json","*.txt","*.jinja","model.safetensors","*.md"])
        if korak == "bge": gguf("ggml-org/bge-m3-Q8_0-GGUF", "q8_0")
        if korak == "granite": gguf("bartowski/granite-embedding-107m-multilingual-GGUF", "Q8_0")
        if korak == "smol3": snap("HuggingFaceTB/SmolLM3-3B", ["*.json","*.txt","*.jinja","*.safetensors","*.md"])
    except Exception as e:
        print("GRESKA", korak, repr(e)[:800], flush=True)
