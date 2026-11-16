import io as image_io
import logging
import time

import numpy as np
import requests
import torch
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import comfy.model_management as memory
import comfy.utils
from comfy_api.latest import ComfyExtension, io
from .prompt_translate import JapanesePromptToEnglish
from .save_prompt import SaveImageWithPositivePrompt

WEB_DIRECTORY = "./web"


class MiniMaxH3Image(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MiniMaxH3Image",
            display_name="MiniMax H3 Image (Local Server)",
            category="MiniMax H3",
            inputs=[
                io.String.Input("prompt", multiline=True, default="A red ceramic teapot beside a sunlit window, realistic photograph."),
                io.Int.Input("width", default=1024, min=256, max=8192, step=32),
                io.Int.Input("height", default=1024, min=256, max=8192, step=32),
                io.Int.Input("seed", default=42, min=0, max=0xFFFFFFFF, control_after_generate=False),
                io.Combo.Input("steps", options=["3", "2", "6"], default="3"),
                io.Combo.Input("generation_area", options=["native", "requested"], default="native"),
                io.String.Input("server_url", default="http://127.0.0.1:8633"),
                io.Boolean.Input("unload_after", default=True),
            ],
            outputs=[io.Image.Output()],
        )

    @classmethod
    def execute(cls, prompt, width, height, seed, steps, generation_area, server_url, unload_after):
        base = server_url.rstrip("/")
        memory.unload_all_models()
        memory.soft_empty_cache()
        progress = comfy.utils.ProgressBar(100)
        job_id = None
        terminal = False
        with requests.Session() as session:
            session.trust_env = False
            session.mount("http://", HTTPAdapter(max_retries=Retry(
                total=3, connect=0, read=3, backoff_factor=0.5, allowed_methods={"GET"},
            )))
            try:
                response = session.post(base + "/api/jobs", json={
                    "mode": "t2i", "prompt": prompt, "width": width, "height": height,
                    "seed": seed, "steps": int(steps), "generation_area": generation_area,
                }, timeout=30)
                response.raise_for_status()
                job_id = response.json()["id"]
                deadline = time.monotonic() + 3600
                while True:
                    memory.throw_exception_if_processing_interrupted()
                    response = session.get(base + "/api/jobs/" + job_id, timeout=30)
                    response.raise_for_status()
                    job = response.json()
                    progress.update_absolute(int(job["progress"] * 100), 100)
                    if job["status"] in ("completed", "failed", "interrupted"):
                        terminal = True
                        break
                    if time.monotonic() >= deadline:
                        raise TimeoutError("H3 generation exceeded one hour")
                    time.sleep(1)
                if job["status"] != "completed":
                    raise RuntimeError(f"H3 {job['status']}: {job.get('error')}")
                response = session.get(base + job["image_url"], timeout=60)
                response.raise_for_status()
                with Image.open(image_io.BytesIO(response.content)) as image:
                    pixels = np.array(image.convert("RGB"), dtype=np.float32) / 255.0
                return io.NodeOutput(torch.from_numpy(pixels).unsqueeze(0))
            finally:
                if job_id is not None and not terminal:
                    try:
                        session.post(base + "/api/interrupt", json={"job_id": job_id}, timeout=10).raise_for_status()
                    except requests.RequestException as exc:
                        logging.warning("Could not interrupt H3 job %s: %s", job_id, exc)
                if unload_after and terminal:
                    try:
                        session.post(base + "/api/admin/unload", json={}, timeout=60).raise_for_status()
                    except requests.RequestException as exc:
                        logging.warning("Could not unload H3 models: %s", exc)


class MiniMaxH3Extension(ComfyExtension):
    async def get_node_list(self):
        return [MiniMaxH3Image, JapanesePromptToEnglish, SaveImageWithPositivePrompt]


async def comfy_entrypoint():
    return MiniMaxH3Extension()
