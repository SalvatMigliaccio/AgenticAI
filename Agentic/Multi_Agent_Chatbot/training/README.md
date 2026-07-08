Tappa 5 - QLoRA offline e export Ollama

Obiettivo
- Addestrare adapter LoRA per dominio in WSL2 con QLoRA 4-bit.
- Convertire ogni adapter in GGUF.
- Importare gli adapter in Ollama con gli stessi nomi usati dal registry backend.

Prerequisiti
- WSL2 con CUDA funzionante.
- GPU consigliata: 16 GB VRAM o superiore.
- Python 3.11+.
- Accesso al modello base Qwen/Qwen2.5-7B-Instruct su Hugging Face.

Struttura
- training/requirements.txt
- training/data/crypto.jsonl
- training/data/eidas.jsonl
- training/train_qlora.py
- training/ollama/crypto-pqc-lora.Modelfile
- training/ollama/eidas-lora.Modelfile
- training/adapters/

1) Install dipendenze (WSL2)
- pip install -r training/requirements.txt

2) Fine-tuning QLoRA
- python training/train_qlora.py --data training/data/crypto.jsonl --out training/adapters/crypto-pqc
- python training/train_qlora.py --data training/data/eidas.jsonl --out training/adapters/eidas

Parametri utili dello script
- --base-model Qwen/Qwen2.5-7B-Instruct
- --epochs 3
- --batch-size 2
- --grad-accum 4
- --learning-rate 2e-4
- --max-seq-length 1024
- --system-prompt "..."

3) Conversione adapter in GGUF
Nota: il nome esatto dello script puo cambiare in base alla versione di llama.cpp.
Flusso invariato: adapter PEFT safetensors -> adapter GGUF.

Esempio:
- python llama.cpp/convert_lora_to_gguf.py training/adapters/crypto-pqc --outfile training/adapters/crypto-pqc/adapter.gguf --base Qwen/Qwen2.5-7B-Instruct
- python llama.cpp/convert_lora_to_gguf.py training/adapters/eidas --outfile training/adapters/eidas/adapter.gguf --base Qwen/Qwen2.5-7B-Instruct

4) Creazione modelli Ollama
- ollama create crypto-pqc-lora -f training/ollama/crypto-pqc-lora.Modelfile
- ollama create eidas-lora -f training/ollama/eidas-lora.Modelfile

5) Attivazione backend
Nel backend/.env imposta:
- USE_ADAPTERS=True

Il registry del progetto usa gia questi nomi modello:
- crypto-pqc-lora
- eidas-lora

Quindi non servono altre modifiche al codice per usare gli specialisti addestrati.
