import subprocess
import time
import os
from openai import OpenAI
QWEN_API_BASE = os.getenv("QWEN_API_BASE", "0.0.0.0:8000/v1")

def await_client(printing: bool = False):
    for _ in range(15 * 60):
        time.sleep(1)
        try:
            model_list = client.models.list()
            if printing:
                print(model_list)
        except Exception:
            continue
        break
    else:
        raise TimeoutError

def start_vllm_server() -> subprocess.Popen[bytes]:


    command = [
    "python", "-m", "vllm.entrypoints.openai.api_server",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--model", "Qwen/Qwen2.5-7B-Instruct",
    "--enable-auto-tool-choice",
    "--tool-call-parser", "hermes",
    "--gpu-memory-utilization", "0.9",
    "--tensor-parallel-size", "2",
    "--dtype", "half",
    "--enforce_eager",
    "--disable-custom-all-reduce",
    "--max-model-len", "4096"
    ]

    # Start the process in the background
    with open("/kaggle/working/a-vllm.log", "w") as logfile:
        process: subprocess.Popen[bytes] = subprocess.Popen(
            command, stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True
        )

    print("Logs: /kaggle/working/a-vllm.log")
    return process

vllm_process: subprocess.Popen[bytes] = start_vllm_server()
client = OpenAI(api_key="EMPTY", base_url=QWEN_API_BASE)


await_client()