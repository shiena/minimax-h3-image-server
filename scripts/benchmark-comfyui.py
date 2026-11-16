"""Benchmark a ComfyUI API workflow with GPU-wide VRAM sampling."""

import argparse
import copy
import json
import subprocess
import threading
import time
import urllib.request
from pathlib import Path


def request(base, route, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + route, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = response.read()
    return json.loads(payload) if payload else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    args = parser.parse_args()
    graph = json.loads(args.workflow.read_text(encoding="utf-8"))
    environment = request(args.url, "/system_stats")
    ui_path = args.workflow.with_name(args.workflow.name.replace("-api.json", "-workflow.json"))
    ui = json.loads(ui_path.read_text())
    queue = request(args.url, "/queue")
    if queue["queue_running"] or queue["queue_pending"]:
        raise RuntimeError("ComfyUI is busy; benchmark requires an idle queue")
    request("http://127.0.0.1:8633", "/api/admin/unload", {})
    request(args.url, "/free", {"unload_models": True, "free_memory": True})
    time.sleep(3)
    samples = []
    sampler = subprocess.Popen(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "--id=0", "--loop-ms=250"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    def collect():
        for line in sampler.stdout:
            try:
                samples.append((time.monotonic(), int(line.strip())))
            except ValueError:
                continue

    reader = threading.Thread(target=collect, daemon=True)
    reader.start()
    results = []
    try:
        time.sleep(2)
        if not samples:
            raise RuntimeError("nvidia-smi returned no VRAM samples")
        for index, label in enumerate(("cold", "warm")):
            prompt = copy.deepcopy(graph)
            workflow = copy.deepcopy(ui)
            for node in prompt.values():
                if node["class_type"] == "KSampler":
                    node["inputs"]["seed"] += index
            for node in workflow["nodes"]:
                if node["type"] == "KSampler":
                    node["widgets_values"][0] += index
            baseline = samples[-1][1]
            start = time.monotonic()
            submitted = request(args.url, "/prompt", {"prompt": prompt, "extra_data": {"extra_pnginfo": {"workflow": workflow}}})
            job_id = submitted["prompt_id"]
            print(f"{label}: submitted {job_id}", flush=True)
            while True:
                entry = request(args.url, "/history/" + job_id).get(job_id)
                if entry:
                    break
                if time.monotonic() - start > 1800:
                    raise TimeoutError(f"ComfyUI job still pending: {job_id}")
                time.sleep(1)
            end = time.monotonic()
            measured = [used for timestamp, used in samples if start <= timestamp <= end]
            result = {
                "run": label, "prompt_id": job_id, "seconds": round(end - start, 2),
                "baseline_gpu_mib": baseline, "peak_gpu_mib": max(measured),
                "samples": len(measured), "status": entry["status"], "outputs": entry["outputs"],
            }
            results.append(result)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({
                "workflow": str(args.workflow), "prompt": graph, "environment": environment,
                "vram_scope": "whole GPU, sampled every 250 ms; includes other applications",
                "runs": results,
            }, indent=2))
            print(json.dumps(result), flush=True)
            if entry["status"]["status_str"] != "success":
                raise RuntimeError("Workflow failed; see benchmark JSON")
    finally:
        sampler.terminate()
        sampler.wait(timeout=10)
        reader.join(timeout=5)


if __name__ == "__main__":
    main()
