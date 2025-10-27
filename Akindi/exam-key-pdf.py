#!/usr/bin/env python3
"""
Python port of exam-key-pdf.sh

Usage:
  python make_exam_keys.py <prefix>

Assumptions:
- Versioned sources are named "<prefix>-?.tex" (single-character version tag).
- A template "exam-key.tex" exists alongside this script and uses \\FILE, \\VERSION, \\KEY.
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

def load_keys_map(filename):
    """
    Read keys from file 'F.keys' and return a dict:
      {
        'A': ['A', 'C', 'C', 'A', 'B', 'B', 'C', 'D', 'B', 'B'],
        'B': ['ABC', 'CD', 'C', 'A', 'B', 'B', 'C', 'BD', 'B', '*'],
        ...
      }
    """
    mapping = {}

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # skip empty or commented lines

            parts = line.split('\t')
            key = parts[0]
            values = parts[1:]  # everything after the first entry
            mapping[key] = ",".join(values)

    return mapping

def discover_versioned(prefix: str) -> tuple[list[str], str]:
    """
    Discover TeX source files matching either "<prefix>A.tex" or "<prefix>-A.tex".

    Returns:
        (versioned_files, file_prefix)
        where versioned_files is a sorted list of matching filenames,
        and file_prefix is the prefix pattern used (e.g., "exam-" or "exam").

    Raises:
        SystemExit if no matching files are found.
    """
    versioned = []
    file_prefix = None

    for pattern, fp in (
        (f"{prefix}?.tex", f"{prefix}"),
        (f"{prefix}-?.tex", f"{prefix}-"),
    ):
        matches = sorted(str(p) for p in Path(".").glob(pattern))
        if matches:
            versioned = matches
            file_prefix = fp
            break

    if not versioned or file_prefix is None:
        sys.stderr.write(f"[ERROR] No files found for prefix={prefix}.\n")
        sys.exit(1)

    return versioned, file_prefix

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

    versioned, file_prefix = discover_versioned(prefix)
    
    exam_key_prefix = f"{file_prefix}key"  # e.g., "exam-key"

    # Extract version tags (the character after the last hyphen, before .tex).
    versions = [Path(p).stem.split("-")[-1] for p in versioned]

    # Phase 1: run extractor per version, capture to "<prefix>-key-<v>.txt"
    tex_path = f"{file_prefix}"
    out_txt = f"{file_prefix.removesuffix('-')}.keys"
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

    if not Path(out_txt).exists():
        sys.stderr.write(f"[ERROR] Missing extracted key file: {out_txt}\n")
        sys.exit(1)

    # create a map with version to its keys
    keys = load_keys_map(out_txt)


    # Phase 2: compile one PDF per version using latexmk and pretex definitions
    for v in versions:
        
        V = v.upper()
        K = keys[V]
        
        # Build -usepretex payload:
        # \FILE: the TeX base name prefix (without the version character), e.g., "exam-"
        # \VERSION: the version token (from extractor; often equals v)
        # \KEY: comma-separated list of answers
        # Note: backslashes must be escaped for the shell, hence the double escaping here.
        pretex = f"\\def\\FILE{{{file_prefix.removesuffix('-')}}} \\def\\VERSION{{{V}}} \\def\\KEY{{{K}}} \\def\\SOURCE{{{script_dir}}}"

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
