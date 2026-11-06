# Sve brojke iz knjige koje se racunaju. Samo standardna biblioteka.
GB=1e9; GiB=2**30
def kv(c,L,h,d,b): return 2*c*L*h*d*b/8
print("KV cache (GB, decimalno) = 2*c*L*hkv*dh*b/8")
for n,L,h,d,cs in [("Llama 3 8B",32,8,128,[4096,32768,131072]),("Llama 3 70B",80,8,128,[32768,131072])]:
    for c in cs: print(f" {n:12} c={c:>6} FP16={kv(c,L,h,d,16)/GB:6.2f} FP8={kv(c,L,h,d,8)/GB:6.2f} Q4={kv(c,L,h,d,4)/GB:6.2f}")
# Llama 3 8B parametri
V,D,F,L,Kd=128256,4096,14336,32,1024
emb=2*V*D; attn=L*(D*D*2+D*Kd*2); mlp=L*3*D*F; norm=L*2*D+D
tot=emb+attn+mlp+norm
print(f"\nLlama 3 8B: emb {emb/1e9:.2f}B attn {attn/1e9:.2f}B mlp {mlp/1e9:.2f}B ukupno {tot/1e9:.2f}B; MoE 3x = {(tot+2*mlp)/1e9:.2f}B; 8x={(tot+7*mlp)/1e9:.2f}B")
print("\nVelicina tezina za 8e9 parametara:")
for n,b in [("FP32",32),("BF16",16),("FP8",8),("Q8_0",8.5),("Q6_K",6.6),("Q5_K_M",5.7),("Q4_K_M",4.89),("Q3_K_M",3.9),("NF4+DQ",4.0)]:
    print(f" {n:8} {b:5} bpw {8e9*b/8/GB:6.2f} GB")
print("\nPuni trening 8B: tezine 16, gradijenti 16, AdamW 2*4*8 = 64 GB; ukupno", 16+16+64, "+ aktivacije")
r=16;d=k=4096
print(f"\nLoRA r=16 na matrici 4096x4096: puna {d*k:,} parametara, LoRA {r*(d+k):,} = {r*(d+k)/(d*k)*100:.2f}%")
def lora_total(r): # q,k,v,o + gate,up,down
    shapes=[(D,D),(D,Kd),(D,Kd),(D,D),(F,D),(F,D),(D,F)]
    return L*sum(r*(a+b) for a,b in shapes)
for r in (8,16,32,64): print(f" r={r:<3} ukupno {lora_total(r)/1e6:6.1f} M parametara, {lora_total(r)*2/1e6:6.0f} MB u BF16, {lora_total(r)/tot*100:.2f}% modela")
print("\nPrimjer dimenzioniranja: 8B Q4_K_M, c=32768, KV FP16, overhead 1 GB")
w=8e9*4.89/8/GB*1.05; k_=kv(32768,32,8,128,16)/GB; print(f" tezine {w:.2f} + KV {k_:.2f} + 1.0 = {w+k_+1:.2f} GB")
print("\nPropusnost: gornja granica tok/s ~ propusnost / velicina modela")
for n,bw in [("DDR5 dual ch",80),("M4 Pro",273),("M4 Max",546),("RTX 4090",1008)]:
    print(f" {n:14} {bw:5} GB/s -> 4.9 GB model: {bw/4.9:6.0f} tok/s; 16 GB model {bw/16:5.0f}")
