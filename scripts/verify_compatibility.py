"""Check the original and current server using one Python environment."""

import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "9e074ae5e22e89c4aa1a51bdb5a0f64e654d64d0"
BASELINE_BLOB = "23eca8d91445b3e952b4250ccdbc12c6197b3a57"


def check_tests(label: str, paths: list[str], environment: dict) -> None:
    print(f"\n{label}", flush=True)
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *paths],
        cwd=ROOT, env=environment, check=True, timeout=60,
    )


def verify() -> None:
    # Read only: never check out the old commit over the current working tree.
    source = subprocess.check_output(
        ["git", "show", f"{BASELINE}:pancake_server.py"], cwd=ROOT, timeout=15,
    )
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    if blob != BASELINE_BLOB:
        raise ValueError("The baseline source does not match the recorded Git blob.")

    current_env = os.environ.copy()
    current_env.pop("PANCAKE_LEGACY_SOURCE", None)
    with tempfile.TemporaryDirectory(prefix="pancake-compatibility-") as directory:
        legacy_path = Path(directory) / "pancake_legacy.py"
        legacy_path.write_bytes(source)
        legacy_env = {**current_env, "PANCAKE_LEGACY_SOURCE": str(legacy_path)}

        check_tests("BASELINE_API", ["tests/test_api_contract.py"], legacy_env)
        check_tests("CURRENT_API_AND_ISOLATION", ["tests"], current_env)

        spec = importlib.util.spec_from_file_location("pancake_legacy", legacy_path)
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        sys.path.insert(0, str(ROOT))
        from pancake_server import app

        before, after = legacy.app.openapi(), app.openapi()
        if before != after:
            diff = difflib.unified_diff(
                json.dumps(before, sort_keys=True, indent=2).splitlines(),
                json.dumps(after, sort_keys=True, indent=2).splitlines(),
                fromfile="baseline-openapi", tofile="current-openapi", lineterm="",
            )
            print("\n".join(diff))
            raise ValueError("OpenAPI changed; review the compatibility change explicitly.")
        print("OPENAPI_IDENTICAL=PASS", flush=True)


def main() -> int:
    try:
        verify()
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"COMPATIBILITY=FAIL: {error}", file=sys.stderr)
        return 1
    print("COMPATIBILITY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
