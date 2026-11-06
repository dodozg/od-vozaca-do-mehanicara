# L10: kirurgija na malom modelu. (1) provjera zdravlja tenzora jedan po jedan,
# (2) dva nova posebna tokena, (3) uklanjanje gornjih slojeva na kopiji i posljedice.
# Pokretanje: python l10_kirurgija.py MODEL_MAPA RADNA_MAPA
import json, math, os, shutil, struct, sys, time
import torch
from safetensors import safe_open
from safetensors.torch import save_file
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
model, radna = sys.argv[1:3]
os.makedirs(radna, exist_ok=True)
print("### 1. provjera zdravlja, jedan tenzor u memoriji u svakom trenutku")
t0 = time.time(); br = 0; los = []; najveca = (0, ""); najmanja = (math.inf, ""); norme = {}
with safe_open(os.path.join(model, "model.safetensors"), "pt") as f:
    for ime in f.keys():
        t = f.get_tensor(ime).float()
        nan, inf, nule = int(torch.isnan(t).sum()), int(torch.isinf(t).sum()), int((t == 0).sum())
        n = float(torch.linalg.vector_norm(t))
        br += 1
        if nan or inf or nule == t.numel(): los.append((ime, nan, inf, nule))
        if n > najveca[0]: najveca = (n, ime)
        if n < najmanja[0]: najmanja = (n, ime)
        norme[ime] = n
        del t  # bez gomilanja
print(f"tenzora {br}, {time.time()-t0:.1f} s, problematicnih {len(los)}: {los}")
print(f"najveca L2 norma {najveca[0]:.2f} {najveca[1]}; najmanja {najmanja[0]:.2f} {najmanja[1]}")
print("uzorak normi:", {k: round(v,2) for k, v in list(norme.items())[:5]})
print("\n### 1b. isti alat na namjerno pokvarenoj kopiji (jedan NaN, jedan tenzor nula)")
with safe_open(os.path.join(model, "model.safetensors"), "pt") as f:
    d = {k: f.get_tensor(k) for k in list(f.keys())[:6]}
kljucevi = list(d)
d[kljucevi[1]].view(-1)[0] = float("nan"); d[kljucevi[2]] *= 0
pok = os.path.join(radna, "pokvareno.safetensors"); save_file(d, pok)
with safe_open(pok, "pt") as f:
    for ime in f.keys():
        t = f.get_tensor(ime).float()
        print(f"  {ime:<50} nan={int(torch.isnan(t).sum())} sve_nule={bool((t==0).all())} norma={float(torch.nan_to_num(t).norm()):.2f}")
print("\n### 2. dva nova posebna tokena")
tok = AutoTokenizer.from_pretrained(model); m = AutoModelForCausalLM.from_pretrained(model, dtype=torch.float32)
print("prije: len(tok)", len(tok), "embed", tuple(m.get_input_embeddings().weight.shape), "lm_head", tuple(m.get_output_embeddings().weight.shape), "vezano", m.config.tie_word_embeddings, "vocab_size", m.config.vocab_size)
tekst = "<|kvaka_zapisnik|>perilica<|kvaka_kraj|>"
print("tokeni prije:", tok(tekst).input_ids)
d = tok.add_special_tokens({"additional_special_tokens":["<|kvaka_zapisnik|>","<|kvaka_kraj|>"]})
print("dodano", d, "len(tok)", len(tok), "tokeni poslije:", tok(tekst).input_ids)
try:
    ids = torch.tensor([tok(tekst).input_ids]); m(input_ids=ids); print("BEZ resize: prolaz nije pao (neocekivano)")
except Exception as e: print("BEZ resize_token_embeddings pada:", type(e).__name__, str(e)[:160])
m.resize_token_embeddings(len(tok))
print("poslije: embed", tuple(m.get_input_embeddings().weight.shape), "lm_head", tuple(m.get_output_embeddings().weight.shape), "vocab_size", m.config.vocab_size)
w = m.get_input_embeddings().weight
print("norma stare zadnje retke", float(w[len(tok)-3].norm()), "norme novih redaka", float(w[-2].norm()), float(w[-1].norm()))
print("izlaz logita:", m(input_ids=torch.tensor([tok(tekst).input_ids])).logits.shape)
izl = os.path.join(radna, "s_tokenima"); m.save_pretrained(izl); tok.save_pretrained(izl); print("spremljeno", izl, os.path.getsize(os.path.join(izl,"model.safetensors")), "bajtova")
del m
print("\n### 3. uklanjanje gornjih slojeva na kopiji")
kop = os.path.join(radna, "bez_slojeva"); os.makedirs(kop, exist_ok=True)
for fn in os.listdir(model):
    if fn.endswith((".json",".txt")) and "results" not in fn and "trainer_state" not in fn: shutil.copy(os.path.join(model, fn), kop)
cfg = json.load(open(os.path.join(model,"config.json"), encoding="utf-8")); L = cfg["num_hidden_layers"]; ostaje = L-6
print("slojeva izvorno", L, "ostavljamo", ostaje)
d = {}
with safe_open(os.path.join(model,"model.safetensors"), "pt") as f:
    for ime in f.keys():
        if ".layers." in ime and int(ime.split(".layers.")[1].split(".")[0]) >= ostaje: continue
        d[ime] = f.get_tensor(ime)
save_file(d, os.path.join(kop,"model.safetensors"), metadata={"format":"pt"})
print("tenzora ostalo", len(d), "velicina", os.path.getsize(os.path.join(kop,"model.safetensors")))
print("-- a) config i dalje kaze", L, "slojeva, ucitavanje:")
try:
    mm = AutoModelForCausalLM.from_pretrained(kop, dtype=torch.float32)
    prazni = float(mm.model.layers[-1].self_attn.q_proj.weight.abs().mean())
    print("  NIJE PALO. from_pretrained je vratio model s", len(mm.model.layers), "slojeva; zadnji sloj je nasumicno inicijaliziran, |q_proj| =", round(prazni,4))
    x = torch.tensor([tok("Zagreb je glavni grad").input_ids])
    print("  izlaz:", repr(tok.decode(mm.generate(x, max_new_tokens=14, do_sample=False, pad_token_id=tok.eos_token_id)[0])))
    del mm
except Exception as e: print("  PALO:", type(e).__name__, str(e)[:400])
print("-- a2) strogo ucitavanje load_state_dict(strict=True):")
try:
    c = AutoConfig.from_pretrained(kop); mm = AutoModelForCausalLM.from_config(c); mm.load_state_dict(d, strict=True); print("  proslo")
except Exception as e: print("  PALO:", type(e).__name__, str(e)[:300])
print("-- b) popravljen config (num_hidden_layers =", ostaje, "):")
cfg["num_hidden_layers"] = ostaje
if "layer_types" in cfg: cfg["layer_types"] = cfg["layer_types"][:ostaje]
json.dump(cfg, open(os.path.join(kop,"config.json"),"w",encoding="utf-8"), indent=1)
mm = AutoModelForCausalLM.from_pretrained(kop, dtype=torch.float32)
print("  ucitano, slojeva", len(mm.model.layers), "parametara", f"{sum(p.numel() for p in mm.parameters()):,}")
x = torch.tensor([tok("Zagreb je glavni grad").input_ids])
print("  izlaz:", repr(tok.decode(mm.generate(x, max_new_tokens=14, do_sample=False, pad_token_id=tok.eos_token_id)[0])))
m0 = AutoModelForCausalLM.from_pretrained(model, dtype=torch.float32)
print("  izvorni izlaz:", repr(tok.decode(m0.generate(x, max_new_tokens=14, do_sample=False, pad_token_id=tok.eos_token_id)[0])))
