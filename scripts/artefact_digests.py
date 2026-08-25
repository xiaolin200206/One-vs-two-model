#!/usr/bin/env python3
"""
artefact_digests.py — write a SHA256 manifest for the six ONNX artefacts.

The model weights are not released (see README, "On the data"), so this
manifest is what lets a reader confirm that the artefacts described in the
Methods are the ones that produced the released telemetry, and that they have
not changed between runs. It is cheap to produce and costs nothing in
confidentiality: a digest identifies a file without disclosing it.

Run it from the repository root with the exported ONNX files present, then
commit the resulting docs/artefact_digests.txt:

    python scripts/artefact_digests.py --dir /path/to/onnx

Until that file exists and is committed, do NOT claim in a manuscript or cover
letter that the artefacts are identified by digest.
"""
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = [
    "combined_640.onnx", "combined_1280.onnx",
    "leaf_640.onnx", "leaf_1280.onnx",
    "pest_640.onnx", "pest_1280.onnx",
]

ROOT = Path(__file__).resolve().parent.parent


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".", help="directory holding the .onnx files")
    ap.add_argument("--out", default=str(ROOT / "docs" / "artefact_digests.txt"))
    args = ap.parse_args()

    src = Path(args.dir)
    rows, missing = [], []
    for name in EXPECTED:
        p = src / name
        if p.exists():
            rows.append((name, p.stat().st_size, sha256(p)))
        else:
            missing.append(name)

    if not rows:
        raise SystemExit(f"no ONNX artefacts found in {src.resolve()}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        fh.write("ONNX artefact digests\n")
        fh.write(f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}\n")
        fh.write("SHA256 over the exported graph as benchmarked.\n\n")
        for name, size, digest in rows:
            fh.write(f"{digest}  {size:>12,d}  {name}\n")
        if missing:
            fh.write("\nNOT FOUND: " + ", ".join(missing) + "\n")

    for name, size, digest in rows:
        print(f"{digest}  {size:>12,d}  {name}")
    if missing:
        print("\nWARNING — not found:", ", ".join(missing))
        print("The manifest is incomplete; do not describe it as covering all six artefacts.")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
