import os
import torch
from transformers import pipeline
# from openai import OpenAI
from llama_cpp import Llama
# from faster_whisper import WhisperModel

PATH_ROOT = os.path.dirname(os.path.abspath(__file__))
PATH_RUBERT = os.path.join(PATH_ROOT, "src/modelsAi/Rubert")
# PATH_WHISPER = os.path.join(PATH_ROOT, "src/modelAi/whisper_small")
PATH_NEMO = os.path.join(
    PATH_ROOT, "src/modelsAi/Nemo/saiga_nemo_12b.Q4_K_M.gguf")

classifier = pipeline("text-classification", model=PATH_RUBERT,
                      top_k=None, truncation=True, max_length=512)

# whisper = WhisperModel(PATH_WHISPER, device="cpu", compute_type="float16")

llm = Llama(model_path=PATH_NEMO, n_gpu_layers=15, n_ctx=2048,
            offload_kqv=True, flash_attn=True, n_threads=10, n_batch=512, verbose=False)
