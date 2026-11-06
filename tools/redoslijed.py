# Iteracija 3 plana: je li svaki pojam uveden prije prve upotrebe? (ch: uvodi / koristi)
P={1:("api_vs_lokalno kvaka",""),
2:("llama_server","gguf* kvantizacija* kontekst* temperatura*"),
3:("tezine config mapa_modela open_weight","tokenizator* safetensors*"),
4:("token tokenizator posebni_tokeni","mapa_modela"),
5:("chat_template thinking","token posebni_tokeni tokenizator"),
6:("embedding polozaj paznja mlp sloj logiti temperatura moe","token tezine"),
7:("tenzor parametar fp32 bf16 fp8","tezine sloj"),
8:("vram propusnost prefill kv_cache kontekst formula_mem","parametar bf16 paznja moe"),
9:("model_card licenca zlatni_skup","formula_mem open_weight moe chat_template"),
10:("pickle safetensors gguf trust_remote_code","mapa_modela chat_template tenzor"),
11:("kvantizacija q4_k_m imatrix","gguf bf16 formula_mem paznja"),
12:("perpleksnost kld","kvantizacija zlatni_skup logiti chat_template"),
13:("rag strukturirani_izlaz prompt_injection","embedding zlatni_skup llama_server"),
14:("skup_podataka val_skup","chat_template kvaka zlatni_skup"),
15:("gubitak prenaucenost lora nf4","tezine kvantizacija val_skup paznja mlp vram bf16"),
16:("unsloth axolotl spajanje_adaptera","lora nf4 gubitak skup_podataka gguf q4_k_m zlatni_skup licenca"),
17:("inspekcija yarn mergekit task_vektor","safetensors tenzor polozaj posebni_tokeni lora"),
18:("vllm fp8_awq metrike","kv_cache propusnost kvantizacija llama_server fp8"),
19:("","rag lora kvantizacija zlatni_skup vllm licenca moe kv_cache")}
seen=set(); bad=0
for c in sorted(P):
    intro,use=P[c]
    for u in use.split():
        fwd=u.endswith('*'); u=u.rstrip('*')
        if u not in seen and not fwd: print(f"PROBLEM pogl {c}: koristi '{u}' prije uvoda"); bad+=1
        if fwd: print(f"  najava pogl {c}: '{u}' (okvir s uputom)")
    seen|=set(intro.split())
print("problema:",bad)
