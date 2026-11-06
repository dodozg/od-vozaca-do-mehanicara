# L9: spaja LoRA adapter s baznim modelom (merge_and_unload) i sprema običan model za pretvorbu u GGUF.
# Pokretanje: python l9_spoji.py BAZNI_MODEL ADAPTER IZLAZ
import os, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
baza, adapter, izlaz = sys.argv[1:4]
m = AutoModelForCausalLM.from_pretrained(baza, dtype=torch.float32)
s = PeftModel.from_pretrained(m, adapter).merge_and_unload()
print("nakon spajanja, klasa:", type(s).__name__, "lora tenzora:", sum("lora" in k for k in s.state_dict()))
s = s.to(torch.float16)  # GGUF pretvorba ide iz običnog F16
s.save_pretrained(izlaz)
AutoTokenizer.from_pretrained(baza).save_pretrained(izlaz)
for f in sorted(os.listdir(izlaz)): print(f"{os.path.getsize(os.path.join(izlaz,f)):>12,}  {f}")
