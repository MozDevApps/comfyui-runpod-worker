# run_workflow.py
import argparse
import json
import os
import sys
from pathlib import Path

def try_execute_with_comfyapi(workflow_path, input1, input2, output_path, params):
    """
    Best-effort attempt to call ComfyUI internals.
    If this exact call doesn't exist in your ComfyUI fork, edit this function to call the right API.
    """
    # Try a few import paths that commonly appear
    tried = []
    for modname in ("execution", "comfy.execution", "comfyui.execution", "comfy.execution.execution"):
        try:
            mod = __import__(modname, fromlist=["*"])
            print(f"Imported module: {modname}")
            # Try to find a plausible function name
            for fn_name in ("run_workflow_file", "run_workflow", "execute_workflow", "execute"):
                fn = getattr(mod, fn_name, None)
                if callable(fn):
                    print(f"Found function: {modname}.{fn_name} - calling it")
                    # The exact signature varies — try common patterns
                    try:
                        # Pattern 1: (workflow_path, inputs, output_path, params)
                        res = fn(workflow_path, {"input_image1": input1, "input_image2": input2}, output_path, params)
                        return 0, str(res)
                    except TypeError:
                        pass
                    try:
                        # Pattern 2: (workflow_json, inputs_dict)
                        with open(workflow_path, "r", encoding="utf-8") as f:
                            wf = json.load(f)
                        res = fn(wf, {"input_image1": input1, "input_image2": input2})
                        # attempt to find produced file:
                        return 0, str(res)
                    except Exception as e:
                        print("Function call attempt failed:", e)
            tried.append(modname)
        except Exception as e:
            # continue searching, but print debug
            print(f"Import {modname} failed: {e}")
            continue
    return 1, f"No usable comfy execution function found. Tried: {tried}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--input1", required=True)
    parser.add_argument("--input2", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--params", default="{}")
    args = parser.parse_args()

    workflow = Path(args.workflow)
    input1 = Path(args.input1)
    input2 = Path(args.input2)
    output = Path(args.output)
    params = json.loads(args.params)

    # Basic checks
    if not workflow.exists():
        print("Workflow file not found:", workflow, file=sys.stderr)
        sys.exit(2)
    if not input1.exists() or not input2.exists():
        print("Input images not found", file=sys.stderr)
        sys.exit(3)

    # Try to run via ComfyUI internal API
    rc, msg = try_execute_with_comfyapi(str(workflow), str(input1), str(input2), str(output), params)
    print("Execution result:", rc, msg)
    if rc == 0 and output.exists():
        print("Output produced at", output)
        sys.exit(0)
    else:
        # Clear informative error for the user — instruct to adapt function
        print("Automatic internal-call method failed.", file=sys.stderr)
        print("Please adapt run_workflow.py -> try_execute_with_comfyapi to match your ComfyUI's execution API.", file=sys.stderr)
        sys.exit(100)

if __name__ == "__main__":
    main()
