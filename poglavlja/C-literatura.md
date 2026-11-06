# Izvori i literatura

Svim poveznicama pristupljeno je u studenom 2026. Dokumentacija alata mijenja se bez najave, pa se ono što tu piše može razlikovati od stanja opisanog u knjizi. Oznaka **[S]** znači sekundarni izvor, a sve ostalo je primarni izvor: rad, službena dokumentacija, izvorni kod ili pravni tekst.

Polazni priručnik: Domagoj Zoričić, *Praktični priručnik za inženjering LLM težina*, v. 2.4.

## llama.cpp

- Repozitorij: <https://github.com/ggml-org/llama.cpp>
- PR #4861, *Importance Matrix calculation* (ikawrakow, 2024.): <https://github.com/ggml-org/llama.cpp/pull/4861>
- README `llama-quantize`: <https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md>
- README `llama-server`: <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- README `llama-perplexity`: <https://github.com/ggml-org/llama.cpp/blob/master/tools/perplexity/README.md>
- README `llama-imatrix`: <https://github.com/ggml-org/llama.cpp/blob/master/tools/imatrix/README.md>
- Slike i zvuk: <https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md>
- Pozivi alata: <https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md>
- Gramatike GBNF: <https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md>
- Pretvorba modela: <https://github.com/ggml-org/llama.cpp/blob/master/convert_hf_to_gguf.py>
- Pretvorba adaptera: <https://github.com/ggml-org/llama.cpp/blob/master/convert_lora_to_gguf.py>
- Objava o prelasku tima ggml.ai u Hugging Face (2026.): <https://huggingface.co/blog/ggml-joins-hf>

## Hugging Face

- Transformers, vodič za prijelaz na v5: <https://github.com/huggingface/transformers/blob/main/MIGRATION_GUIDE_V5.md>
- Transformers, dokumentacija: <https://huggingface.co/docs/transformers/index>
- PEFT: <https://huggingface.co/docs/peft>
- safetensors: <https://huggingface.co/docs/safetensors>
- huggingface_hub: <https://huggingface.co/docs/huggingface_hub>
- GGUF na Hubu: <https://huggingface.co/docs/hub/gguf>
- Sigurnost pickle datoteka: <https://huggingface.co/docs/hub/security-pickle>

## Trening i spajanje

- Axolotl, dokumentacija: <https://docs.axolotl.ai>
- Axolotl, referenca konfiguracije: <https://docs.axolotl.ai/docs/config-reference.html>
- Axolotl, repozitorij: <https://github.com/axolotl-ai-cloud/axolotl>
- TRL, SFTTrainer: <https://huggingface.co/docs/trl/sft_trainer>
- Unsloth, dokumentacija: <https://unsloth.ai/docs>
- Unsloth, repozitorij: <https://github.com/unslothai/unsloth>
- Mergekit: <https://github.com/arcee-ai/mergekit>

## Posluživanje

- vLLM, dokumentacija: <https://docs.vllm.ai>
- vLLM, repozitorij: <https://github.com/vllm-project/vllm>
- vLLM, kvantizacija: <https://docs.vllm.ai/en/latest/features/quantization/>
- vLLM, ModelOpt: <https://docs.vllm.ai/en/latest/features/quantization/modelopt/>
- LLM Compressor, dokumentacija: <https://docs.vllm.ai/projects/llm-compressor/>
- LLM Compressor, repozitorij: <https://github.com/vllm-project/llm-compressor>
- NVIDIA Model Optimizer: <https://github.com/NVIDIA/Model-Optimizer>
- SGLang: <https://github.com/sgl-project/sglang>
- Ollama: <https://docs.ollama.com>
- LM Studio: <https://lmstudio.ai/docs>

## Radovi

- Hu i sur., *LoRA: Low-Rank Adaptation of Large Language Models*, arXiv 2106.09685: <https://arxiv.org/abs/2106.09685>
- Dettmers i sur., *QLoRA: Efficient Finetuning of Quantized LLMs*, arXiv 2305.14314: <https://arxiv.org/abs/2305.14314>
- Peng i sur., *YaRN: Efficient Context Window Extension of Large Language Models*, arXiv 2309.00071: <https://arxiv.org/abs/2309.00071>
- Qi i sur., *Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!*, arXiv 2310.03693: <https://arxiv.org/abs/2310.03693>
- Yang i sur., *Looped Transformers are Better at Learning Learning Algorithms*, arXiv 2311.12424: <https://arxiv.org/abs/2311.12424>
- Arditi i sur., *Refusal in Language Models Is Mediated by a Single Direction*, arXiv 2406.11717: <https://arxiv.org/abs/2406.11717>
- Young, *Comparative Analysis of LLM Abliteration Methods: A Cross-Architecture Evaluation*, arXiv 2512.13655: <https://arxiv.org/abs/2512.13655>
- Fogel i sur., *Inference-Time Backdoors via Chat Templates: From LLM Supply Chains to Agentic System Compromise*, arXiv 2602.04653: <https://arxiv.org/abs/2602.04653>

## Sigurnost modela

- JFrog, *Data Scientists Targeted by Malicious Hugging Face ML Models with Silent Backdoor* (veljača 2024.): <https://jfrog.com/blog/data-scientists-targeted-by-malicious-hugging-face-ml-models-with-silent-backdoor/>
- ReversingLabs, *Malicious ML models discovered on Hugging Face platform* (veljača 2025.): <https://www.reversinglabs.com/blog/rl-identifies-malware-ml-model-hosted-on-hugging-face>
- PickleScan: <https://github.com/mmaitre314/picklescan>

## Regulativa

Ovo nije pravni savjet. Rokove provjeri u Službenom listu EU na dan odluke.

- Uredba (EU) 2024/1689 (AI Act): <https://eur-lex.europa.eu/eli/reg/2024/1689/oj>
- Europska komisija, smjernice o obvezama pružatelja modela opće namjene (srpanj 2025.): <https://digital-strategy.ec.europa.eu/en/library/guidelines-scope-obligations-providers-general-purpose-ai-models-under-ai-act>
- **[S]** Digitalni omnibus, Uredba (EU) 2026/1744, rokovi prema pregledu Modulosa: <https://www.modulos.ai/blog/eu-ai-act-omnibus-now-law>

## Modeli i licence

Primjeri korišteni u knjizi, bez ikakvog poretka po kvaliteti.

- NVIDIA Dory1.0-4B, kartica modela: <https://huggingface.co/nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-BF16>
- Dory, inačica GGUF: <https://huggingface.co/nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-GGUF>
- Dory, inačica NVFP4: <https://huggingface.co/nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-NVFP4>
- OpenMDW, licenca: <https://openmdw.ai/license/>
- Gemma 4 E2B: <https://huggingface.co/google/gemma-4-E2B-it>
- Gemma 4 E2B, GGUF: <https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF>
- Qwen3-4B, GGUF: <https://huggingface.co/Qwen/Qwen3-4B-GGUF>
- SmolLM3-3B: <https://huggingface.co/HuggingFaceTB/SmolLM3-3B>
- SmolLM2-135M-Instruct: <https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct>

**[S]** Podaci o modelima Kimi K3, GLM-5.3, DeepSeek V4.1 Flash i Muse Spark Open (veličine i uvjeti licence) u poglavlju 9 potječu iz sekundarnih izvora koje ovdje ne navodimo pojedinačno. Prije upotrebe pročitaj licencu na stranici modela.

## Za dalje

Polazište za ono što knjiga namjerno izostavlja, poput propagacije unatrag i PyTorcha. Knjiga se na ove naslove ne oslanja kao na izvore.

- Vaswani i sur., *Attention Is All You Need*, arXiv 1706.03762: <https://arxiv.org/abs/1706.03762>
- PyTorch, vodiči: <https://docs.pytorch.org/tutorials/>
- Hugging Face, tečaj o LLM-ovima: <https://huggingface.co/learn/llm-course>
- Andrej Karpathy, *Neural Networks: Zero to Hero*: <https://karpathy.ai/zero-to-hero.html>
