# L10: provjera spojenog modela: gubitak na validaciji i jedan odgovor.
# Pokretanje: python l10_provjera_spoja.py MODEL PODACI
import json, os, sys, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
m, pod = sys.argv[1:3]; torch.set_num_threads(4)
tok = AutoTokenizer.from_pretrained(m); M = AutoModelForCausalLM.from_pretrained(m, dtype=torch.float32).eval()
SUS = "Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost."
val = [json.loads(l)["messages"] for l in open(os.path.join(pod,"val.jsonl"),encoding="utf-8")][:30]
u = 0
with torch.no_grad():
    for p in val:
        s = tok.apply_chat_template([{"role":"system","content":SUS},p[1]],tokenize=False,add_generation_prompt=True)
        a = tok(s,add_special_tokens=False).input_ids; b = tok(p[2]["content"]+"<|im_end|>\n",add_special_tokens=False).input_ids
        u += M(input_ids=torch.tensor([a+b]),labels=torch.tensor([[-100]*len(a)+b])).loss.item()
    s = tok.apply_chat_template([{"role":"system","content":SUS},{"role":"user","content":"Stranka zove, hladnjak ne hladi, sumnja na kompresor. Treba odmah."}],tokenize=False,add_generation_prompt=True)
    i = tok(s,return_tensors="pt",add_special_tokens=False)
    o = M.generate(**i,max_new_tokens=60,do_sample=False,pad_token_id=tok.pad_token_id,eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"))
print(os.path.basename(m), "val gubitak (30 primjera)", round(u/len(val),4), "| odgovor:", repr(tok.decode(o[0,i.input_ids.shape[1]:],skip_special_tokens=True)))
