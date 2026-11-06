# L9: LoRA trening na CPU-u (simulator pravog treninga), običan PyTorch + PEFT, bez 4-bitnog učitavanja.
# Gubitak se računa samo na tokenima odgovora, ne na promptu.
# Primjer: python l9_trening.py MODEL PODACI IZLAZ --epohe 3 --r 8 --lr 5e-4
import argparse, csv, json, math, os, random, re, time, sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, PeftModel
a = argparse.ArgumentParser()
a.add_argument("model"); a.add_argument("podaci"); a.add_argument("izlaz")
a.add_argument("--r", type=int, default=8); a.add_argument("--lr", type=float, default=5e-4); a.add_argument("--epohe", type=float, default=3)
a.add_argument("--batch", type=int, default=4); a.add_argument("--train-n", type=int, default=240); a.add_argument("--val-n", type=int, default=60)
a.add_argument("--eval-svakih", type=int, default=30); a.add_argument("--najvise-koraka", type=int, default=0); a.add_argument("--dretve", type=int, default=4)
a.add_argument("--bez-zlatnog", action="store_true"); a.add_argument("--samo-velicine", action="store_true"); a.add_argument("--seed", type=int, default=42)
a = a.parse_args()
torch.set_num_threads(a.dretve); torch.manual_seed(a.seed); random.seed(a.seed)
os.makedirs(a.izlaz, exist_ok=True)
# Kratka sistemska poruka: mali model nauči dopuštene vrijednosti iz primjera, a svaki token na CPU-u košta vrijeme.
SUSTAV = "Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost."
tok = AutoTokenizer.from_pretrained(a.model)
CILJEVI = ["q_proj", "k_proj", "v_proj", "o_proj"]
if tok.pad_token is None: tok.pad_token = tok.eos_token

def nova_lora(model, r):
    return get_peft_model(model, LoraConfig(r=r, lora_alpha=2*r, lora_dropout=0.05, target_modules=CILJEVI, bias="none", task_type="CAUSAL_LM"))
if a.samo_velicine:
    # stvarni učinak r na veličinu adaptera; težine se ne treniraju, veličina ne ovisi o treniranju
    for r in (4, 8, 16, 32):
        m = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32)
        p = nova_lora(m, r)
        ukup = sum(x.numel() for x in p.parameters()); tren = sum(x.numel() for x in p.parameters() if x.requires_grad)
        d = os.path.join(a.izlaz, f"r{r}"); p.save_pretrained(d)
        v = os.path.getsize(os.path.join(d, "adapter_model.safetensors"))
        print(f"r={r}: ukupno {ukup:,}, trenira se {tren:,} ({tren/ukup*100:.3f} %), adapter {v:,} bajtova ({v/1e6:.2f} MB)", flush=True)
        del p, m
    sys.exit(0)

def ucitaj(ime, n):
    return [json.loads(l)["messages"] for l in open(os.path.join(a.podaci, ime), encoding="utf-8")][:n]
def kodiraj(poruke):
    prompt = tok.apply_chat_template([{"role":"system","content":SUSTAV}, poruke[1]], tokenize=False, add_generation_prompt=True)
    p = tok(prompt, add_special_tokens=False).input_ids
    o = tok(poruke[2]["content"] + "<|im_end|>\n", add_special_tokens=False).input_ids
    return p + o, [-100]*len(p) + o
def serija(prim):
    d = max(len(x[0]) for x in prim)
    ids = torch.full((len(prim), d), tok.pad_token_id); lab = torch.full((len(prim), d), -100); mas = torch.zeros((len(prim), d), dtype=torch.long)
    for i, (x, y) in enumerate(prim):
        ids[i, :len(x)] = torch.tensor(x); lab[i, :len(y)] = torch.tensor(y); mas[i, :len(x)] = 1
    return ids, mas, lab
trening = [kodiraj(m) for m in ucitaj("train.jsonl", a.train_n)]
val = [kodiraj(m) for m in ucitaj("val.jsonl", a.val_n)]
print("primjera", len(trening), "val", len(val), "prosjecno tokena po primjeru", sum(len(x[0]) for x in trening)//len(trening), flush=True)
print("primjer dekodiran:", repr(tok.decode(trening[0][0])), flush=True)
ZLATNI = [json.loads(l) for l in open(os.path.join(a.podaci, "zlatni.jsonl"), encoding="utf-8")]
VALTXT = [{"tekst":m[1]["content"], "ocekivano":json.loads(m[2]["content"])} for m in ucitaj("val.jsonl", 30)]
POLJA = ["uredaj", "kvar", "dio", "hitnost"]
@torch.no_grad()
def tocnost(model, skup, oznaka):
    model.eval(); t = time.time(); pogodak = {k: 0 for k in POLJA}; valjan = 0; cijeli = 0; pr = []
    for z in skup:
        s = tok.apply_chat_template([{"role":"system","content":SUSTAV},{"role":"user","content":z["tekst"]}], tokenize=False, add_generation_prompt=True)
        ids = tok(s, return_tensors="pt", add_special_tokens=False)
        izl = model.generate(**ids, max_new_tokens=70, do_sample=False, pad_token_id=tok.pad_token_id, eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"))
        txt = tok.decode(izl[0, ids.input_ids.shape[1]:], skip_special_tokens=True)
        m = re.search(r"\{.*?\}", txt, re.S); o = None
        if m:
            try: o = json.loads(m.group(0))
            except json.JSONDecodeError: pass
        valjan += o is not None
        ok = [bool(o) and str(o.get(k,"")).strip().lower() == z["ocekivano"][k] for k in POLJA]
        for k, v in zip(POLJA, ok): pogodak[k] += v
        cijeli += all(ok); pr.append((txt[:140], sum(ok)))
    n = len(skup)
    print(f"[{oznaka}] n={n} valjan JSON {valjan}/{n}, tocnost po polju {sum(pogodak.values())/(4*n)*100:.1f} %, cijeli zapisnik {cijeli}/{n}, {pogodak}, {time.time()-t:.0f} s", flush=True)
    for p in pr[:4]: print("   ", p[1], repr(p[0]), flush=True)
@torch.no_grad()
def val_gubitak(model):
    model.eval(); u = 0.0; b = 0
    for i in range(0, len(val), 8):
        ids, mas, lab = serija(val[i:i+8]); u += model(input_ids=ids, attention_mask=mas, labels=lab).loss.item(); b += 1
    return u/b
m0 = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32)
print("parametara", f"{sum(x.numel() for x in m0.parameters()):,}", flush=True)
if not a.bez_zlatnog:
    tocnost(m0, ZLATNI, "PRIJE, zlatni"); tocnost(m0, VALTXT, "PRIJE, val30")
model = nova_lora(m0, a.r)
ukup = sum(x.numel() for x in model.parameters()); tren = sum(x.numel() for x in model.parameters() if x.requires_grad)
print(f"r={a.r} ciljevi={CILJEVI} trenira se {tren:,} od {ukup:,} ({tren/ukup*100:.3f} %)", flush=True)
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr, weight_decay=0.0)
koraka_ep = math.ceil(len(trening)/a.batch); ukupno_kor = int(koraka_ep*a.epohe)
if a.najvise_koraka: ukupno_kor = min(ukupno_kor, a.najvise_koraka)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda k: min(1.0, (k+1)/10) * max(0.05, 1 - k/ukupno_kor))
c = open(os.path.join(a.izlaz, "gubitak.csv"), "w", newline="", encoding="utf-8"); w = csv.writer(c); w.writerow(["korak","epoha","train_loss","val_loss","sekunde"])
t0 = time.time(); k = 0; zbroj = 0; br = 0
v = val_gubitak(model); print(f"korak 0 val {v:.4f}", flush=True); w.writerow([0,0,"",round(v,4),0]); c.flush()
najbolji = (v, 0)
while k < ukupno_kor:
    red = list(range(len(trening))); random.shuffle(red)
    for i in range(0, len(red), a.batch):
        if k >= ukupno_kor: break
        model.train()
        ids, mas, lab = serija([trening[j] for j in red[i:i+a.batch]])
        l = model(input_ids=ids, attention_mask=mas, labels=lab).loss
        l.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad()
        k += 1; zbroj += l.item(); br += 1
        if k % a.eval_svakih == 0 or k == ukupno_kor:
            tr = zbroj/br; zbroj = 0; br = 0; v = val_gubitak(model)
            if v < najbolji[0]: najbolji = (v, k)
            print(f"korak {k}/{ukupno_kor} epoha {k/koraka_ep:.2f} train {tr:.4f} val {v:.4f} vrijeme {time.time()-t0:.0f} s", flush=True)
            w.writerow([k, round(k/koraka_ep,2), round(tr,4), round(v,4), round(time.time()-t0)]); c.flush()
print(f"KRAJ koraka {k}, vrijeme treninga {time.time()-t0:.0f} s, najbolji val {najbolji[0]:.4f} na koraku {najbolji[1]}", flush=True)
model.save_pretrained(a.izlaz)
print("adapter", os.path.getsize(os.path.join(a.izlaz, "adapter_model.safetensors")), "bajtova", flush=True)
if not a.bez_zlatnog:
    tocnost(model, ZLATNI, "POSLIJE, zlatni"); tocnost(model, VALTXT, "POSLIJE, val30")
