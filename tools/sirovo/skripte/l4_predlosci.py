# L4: predlošci. Prvo ispisuje što apply_chat_template stvarno napravi od poruka,
# a zatim isti upit šalje modelu s ispravnim i s namjerno krivim predloškom.
# Pokretanje: python l4_predlosci.py MODEL_GGUF MAPA_SMOLLM3 MAPA_SMOLLM2 LOG
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from posluzitelj import Posluzitelj
from transformers import AutoTokenizer
GGUF, S3, S2, LOG = sys.argv[1:5]
PORUKE = [{"role":"system","content":"Odgovaraj isključivo jednom riječju: DA ili NE."},
          {"role":"user","content":"Smije li se perilica rublja pokrenuti dok je voda u bubnju?"}]
print("### poruke:", json.dumps(PORUKE, ensure_ascii=False))
for ime, m in (("SmolLM3-3B", S3), ("SmolLM2-135M-Instruct", S2)):
    t = AutoTokenizer.from_pretrained(m)
    print(f"\n### apply_chat_template, {ime}, add_generation_prompt=True")
    print(repr(t.apply_chat_template(PORUKE, tokenize=False, add_generation_prompt=True)))
    if ime.startswith("SmolLM3"):
        print(f"### isto, enable_thinking=False")
        print(repr(t.apply_chat_template(PORUKE, tokenize=False, add_generation_prompt=True, enable_thinking=False)))
    print("### tokena:", len(t.apply_chat_template(PORUKE, tokenize=True, add_generation_prompt=True, return_dict=True)["input_ids"]))

DROP = os.path.join(os.path.dirname(os.path.abspath(LOG)), "predlozak_bez_sustava.jinja")
with open(DROP, "w", encoding="utf-8", newline="\n") as f:  # predložak koji tiho baca sistemsku poruku
    f.write("{%- for m in messages -%}{%- if m.role != 'system' -%}<|turn>{{ 'model' if m.role == 'assistant' else m.role }}\n{{ m.content }}<turn|>\n{%- endif -%}{%- endfor -%}{%- if add_generation_prompt -%}<|turn>model\n{%- endif -%}")
SLUCAJEVI = [("ispravan (ugrađen u GGUF)", ["--reasoning","off"]),
             ("krivi: chatml", ["--chat-template","chatml"]),
             ("krivi: llama2", ["--chat-template","llama2"]),
             ("krivi: tiho baca sistemsku poruku", ["--chat-template-file",DROP]),]
ZAHTJEV = {"messages":PORUKE,"max_tokens":120,"temperature":0,"seed":1}
for naziv, args in SLUCAJEVI:
    print(f"\n### SLUČAJ: {naziv}  args={args}")
    with Posluzitelj(GGUF, LOG, args=["-c",4096,"-t",4,"-np",1,*args]) as s:
        print("apply-template:", repr(s.post("/apply-template", {"messages":PORUKE})["prompt"]))
        r = s.post("/v1/chat/completions", ZAHTJEV)
        c = r["choices"][0]
        print("finish_reason:", c["finish_reason"], "| prompt_tokens:", r["usage"]["prompt_tokens"], "| completion_tokens:", r["usage"]["completion_tokens"], "| gen tok/s:", round(r["timings"]["predicted_per_second"],2))
        print("content:", repr(c["message"].get("content")))
        if c["message"].get("reasoning_content"): print("reasoning_content:", repr(c["message"]["reasoning_content"])[:600])

print("\n### SLUČAJ: sirovi prompt bez ikakvog predloška, /completion")
with Posluzitelj(GGUF, LOG, args=["-c",4096,"-t",4,"-np",1]) as s:
    r = s.post("/completion", {"prompt":PORUKE[0]["content"]+"\n"+PORUKE[1]["content"],"n_predict":120,"temperature":0,"seed":1,"cache_prompt":False})
    print("stop_type:", r.get("stop_type"), "tokens_predicted:", r["tokens_predicted"]); print("content:", repr(r["content"]))
    print("\n### SLUČAJ: razmišljanje uključeno (zadano), bez max_tokens ograničenja na 120")
    r = s.post("/v1/chat/completions", {**ZAHTJEV,"max_tokens":400})
    c = r["choices"][0]
    print("apply-template:", repr(s.post("/apply-template", {"messages":PORUKE})["prompt"]))
    print("finish_reason:", c["finish_reason"], "completion_tokens:", r["usage"]["completion_tokens"])
    print("content:", repr(c["message"].get("content")))
    print("reasoning_content:", repr(c["message"].get("reasoning_content"))[:800])
    print("\n### SLUČAJ: zadani GGUF predložak, razmišljanje, ali tražimo samo 40 tokena (odgovor nikad ne stigne)")
    r = s.post("/v1/chat/completions", {**ZAHTJEV,"max_tokens":40})
    c = r["choices"][0]
    print("finish_reason:", c["finish_reason"], "content:", repr(c["message"].get("content")), "reasoning_content:", repr(c["message"].get("reasoning_content"))[:300])
