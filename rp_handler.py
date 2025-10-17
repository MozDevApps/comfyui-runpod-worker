# rp_handler.py
import base64
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

# Default workflow (your provided path)
DEFAULT_WORKFLOW = "/workspace/runpod-slim/ComfyUI/workflows/image_qwen_image_edit_2509_API.json"

# Path to the run_workflow helper (we provide below)
RUNNER = "/app/run_workflow.py"  # adjust if placed elsewhere

def save_b64_image(b64str, path: Path):
    data = base64.b64decode(b64str)
    path.write_bytes(data)

def encode_file_b64(path: Path):
    return base64.b64encode(path.read_bytes()).decode("utf-8")

def handler(event, context):
    """
    Runpod calls this handler. event should be a JSON object:
    {
      "image1_b64": "<base64>",
      "image2_b64": "<base64>",
      "workflow": "/workspace/...json"  # optional, default used otherwise
    }
    Returns JSON:
    { "status": "ok", "output_b64": "<base64 image>", "log": "..." }
    """
    start = time.time()
    try:
        # If event is string, parse it
        if isinstance(event, str):
            event = json.loads(event)

        image1_b64 = event.get("image1_b64")
        image2_b64 = event.get("image2_b64")
        workflow = event.get("workflow", DEFAULT_WORKFLOW)
        params = event.get("params", {})  # optional extra params

        if not image1_b64 or not image2_b64:
            return {"status": "error", "message": "image1_b64 and image2_b64 required"}

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input1 = tmpdir / "input1.png"
            input2 = tmpdir / "input2.png"
            output = tmpdir / "output.png"
            logf = tmpdir / "runlog.txt"

            save_b64_image(image1_b64, input1)
            save_b64_image(image2_b64, input2)

            # Build command to call runner
            cmd = [
                "python", RUNNER,
                "--workflow", workflow,
                "--input1", str(input1),
                "--input2", str(input2),
                "--output", str(output)
            ]
            # Add params as JSON string if present
            if params:
                cmd += ["--params", json.dumps(params)]

            # Run the runner and capture stdout/stderr
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            run_log = proc.stdout + "\n" + proc.stderr
            logf.write_text(run_log)

            if proc.returncode != 0:
                return {
                    "status": "error",
                    "message": "Workflow runner failed",
                    "returncode": proc.returncode,
                    "log": run_log
                }

            if not output.exists():
                return {
                    "status": "error",
                    "message": "No output image produced. See log.",
                    "log": run_log
                }

            out_b64 = encode_file_b64(output)
            total = time.time() - start
            return {"status": "ok", "output_b64": out_b64, "log": run_log, "elapsed_s": total}

    except Exception as e:
        return {"status": "error", "message": str(e)}
