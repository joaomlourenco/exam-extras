#!/usr/bin/env python3
"""
Python port of exam-key-pdf.sh

Usage:
  python make_exam_keys.py <prefix>

Assumptions:
- Versioned sources are named "<prefix>-?.tex" (single-character version tag).
- A template "exam-key.tex" exists alongside this script and uses \FILE, \VERSION, \KEY.
- The extractor "exam-extract-key.py" exists alongside this script and prints one
  tab-separated line: "<version>\t<ans1>\t<ans2>\t...".
- latexmk is available in PATH.

Outputs:
- Text files: "<prefix>-key-<v>.txt"
- PDFs:       "<prefix>-key-<v>.pdf"
"""

import argparse
import glob
import os
import shlex
import subprocess
import sys
from pathlib import Path

def run(cmd, cwd=None):
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[ERROR] Command failed ({e.returncode}): {' '.join(cmd)}\n")
        sys.exit(e.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", help="Prefix for versioned TeX files, e.g., 'exam' for exam-A.tex, exam-B.tex")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    extract_key = script_dir / "exam-extract-key.py"
    base_key = "exam-key"  # template base name (exam-key.tex)
    base_key_tex = script_dir / f"{base_key}.tex"

    if not base_key_tex.exists():
        sys.stderr.write(f"[ERROR] Missing template: {base_key_tex}\n")
        sys.exit(1)
    if not extract_key.exists():
        sys.stderr.write(f"[ERROR] Missing extractor: {extract_key}\n")
        sys.exit(1)

    prefix = args.prefix
    file_prefix = f"{prefix}-"        # matches original script’s $PREFIX
    exam_key_prefix = f"{file_prefix}key"  # e.g., "exam-key"

    # Discover versions matching "<prefix>-?.tex" (single-character version tag).
    versioned = sorted(glob.glob(f"{file_prefix}?.tex"))
    if not versioned:
        # Mirror the shell script behavior: exit quietly if no matches.
        sys.stderr.write(f"[ERROR] No files found for prefix={file_prefix}.\n")
        sys.stderr.write("")
        sys.exit(1)

    # Extract version tags (the character after the last hyphen, before .tex).
    versions = [Path(p).stem.split("-")[-1] for p in versioned]

    # Phase 1: run extractor per version, capture to "<prefix>-key-<v>.txt"
    for v in versions:
        tex_path = f"{file_prefix}{v}.tex"
        out_txt = f"{exam_key_prefix}-{v}.txt"
        # Capture stdout of the extractor
        try:
            result = subprocess.run(
                [sys.executable, str(extract_key), tex_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"[ERROR] Extractor failed for {tex_path} ({e.returncode}).\n")
            sys.stderr.write(e.stderr or "")
            sys.exit(e.returncode)

        Path(out_txt).write_text(result.stdout)

    # Phase 2: compile one PDF per version using latexmk and pretex definitions
    for v in versions:
        txt_path = Path(f"{exam_key_prefix}-{v}.txt")
        if not txt_path.exists():
            sys.stderr.write(f"[ERROR] Missing extracted key file: {txt_path}\n")
            sys.exit(1)

        # Expect a single line: "<V>\t<k1>\t<k2>\t..."
        line = txt_path.read_text().strip().splitlines()[0] if txt_path.read_text().strip() else ""
        if not line:
            sys.stderr.write(f"[ERROR] Empty key file: {txt_path}\n")
            sys.exit(1)

        fields = line.split("\t")
        V = fields[0].strip()
        K = ",".join(f.strip() for f in fields[1:] if f.strip())

        # Build -usepretex payload:
        # \FILE: the TeX base name prefix (without the version character), e.g., "exam-"
        # \VERSION: the version token (from extractor; often equals v)
        # \KEY: comma-separated list of answers
        # Note: backslashes must be escaped for the shell, hence the double escaping here.
        pretex = f"\\def\\FILE{{{file_prefix}}}\\def\\VERSION{{{V}}}\\def\\KEY{{{K}}}"

        # latexmk call (quiet failure-tolerant mode -f, PDF output)
        cmd = [
            "latexmk",
            "-f",
            "-pdf",
            f"-usepretex={pretex}",
            str(base_key_tex),
        ]
        run(cmd)

        # latexmk writes exam-key.pdf in the working directory; move/rename it
        produced_pdf = Path(f"{base_key}.pdf")
        target_pdf = Path(f"{exam_key_prefix}-{v}.pdf")
        if not produced_pdf.exists():
            sys.stderr.write("[ERROR] latexmk did not produce expected PDF: "
                             f"{produced_pdf}\n")
            sys.exit(1)
        # If a stale PDF exists with the target name, remove it before moving.
        if target_pdf.exists():
            target_pdf.unlink()
        produced_pdf.rename(target_pdf)

        # Optional: remove the transient PDF name if present under an alternate name
        # (kept minimal; latexmk’s cleanup below covers usual byproducts).

    # Minimal cleanup of LaTeX byproducts for the template
    # Equivalent to: rm -f exam-key.{aux,fdb*,fls,log}
    for pattern in [f"{base_key}.aux", f"{base_key}.fdb*", f"{base_key}.fls", f"{base_key}.log"]:
        for p in Path(".").glob(pattern):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

if __name__ == "__main__":
    main()
