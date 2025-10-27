#!/usr/bin/env python3
"""
exam_versions.py — verbose Python port of exam-versions.sh

- Finds versioned .tex files (BASE-?.tex preferred, falls back to BASE?.tex)
- Builds each version twice with latexmk:
    1) noanswers  -> "<name>-print.pdf"
    2) answers    -> "<name>-answers.pdf"
- Injects \\VERSION via -usepretex (uppercase of version letter)
- Uses -auxdir=AUX by default (keeps the root tidy)
- Captures latexmk stdout/stderr; shows them only on --show-build-output or on failure
- Prints readable, colorized progress

Usage:
  python exam_versions.py BASE
  python exam_versions.py exam --show-build-output
"""

from __future__ import annotations
import argparse
import re
import shutil
import subprocess
from pathlib import Path
import sys
from typing import List

# ---------- Defaults ----------
DEFAULT_LATEX = "pdf"                          # maps to -pdf for latexmk
DEFAULT_OPTS  = "-shell-escape -auxdir=AUX"    # AUX keeps aux files contained
PRINT_LABEL   = "print"
ANSWERS_LABEL = "answers"

# ---------- Colors (ANSI) ----------
def _enable_colors() -> bool:
    return sys.stdout.isatty()

COLOR_ON = _enable_colors()
class C:
    if COLOR_ON:
        BOLD   = "\033[1m"
        DIM    = "\033[2m"
        RED    = "\033[31m"
        GREEN  = "\033[32m"
        YELLOW = "\033[33m"
        BLUE   = "\033[34m"
        CYAN   = "\033[36m"
        GRAY   = "\033[90m"
        RESET  = "\033[0m"
    else:
        BOLD=DIM=RED=GREEN=YELLOW=BLUE=CYAN=GRAY=RESET=""  # no color on non-tty

# ---------- Regex to toggle answers/noanswers (matches start-of-line token) ----------
_ANSWERS_LINE = re.compile(r'^( *%? *,? *)(?:no)?answers\b', re.MULTILINE)

# ---------- Helpers ----------
def find_version_files(base: str) -> List[Path]:
    p = Path(base)
    parent = p.parent if p.parent != Path("") else Path(".")
    stem = p.name
    pat1 = sorted(parent.glob(f"{stem}-?.tex"))
    if pat1:
        return pat1
    return sorted(parent.glob(f"{stem}?.tex"))

def version_letter_from_filename(tex_path: Path) -> str:
    return tex_path.stem[-1]

def set_answers_mode(text: str, mode: str) -> str:
    replacement = r"\1" + ("answers" if mode == "answers" else "noanswers")
    if _ANSWERS_LINE.search(text) is None:
        return text
    return _ANSWERS_LINE.sub(replacement, text)

def run_latexmk(
    tex: Path,
    version_letter: str,
    latex: str,
    opts: str,
    show_build_output: bool
) -> subprocess.CompletedProcess:
    cmd = [
        "latexmk",
        f"-{latex}",
        f"-usepretex=\\def\\VERSION{{\\MakeUppercase{{{version_letter}}}}}"
    ]
    if opts:
        cmd[1:1] = [o for o in opts.split() if o.strip()]
    cmd.append(str(tex))

    try:
        # Capture output so we can show a clean summary unless user requests logs.
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            check=False
        )
    except FileNotFoundError:
        print(f"{C.RED}ERROR:{C.RESET} 'latexmk' not found on PATH.", file=sys.stderr)
        sys.exit(2)

    if show_build_output or result.returncode != 0:
        # Indent build output for readability.
        out = result.stdout.strip()
        err = result.stderr.strip()
        if out:
            print(f"{C.GRAY}{indent(out)}{C.RESET}")
        if err:
            print(f"{C.YELLOW}{indent(err)}{C.RESET}", file=sys.stderr)

    return result

def indent(s: str, pad: int = 2) -> str:
    prefix = " " * pad
    return "\n".join(prefix + line for line in s.splitlines())

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Build exam versions (print and answers) with latexmk.")
    parser.add_argument("base", help="LaTeX base filename WITHOUT '-V.tex' (e.g., 'exam' for 'exam-a.tex').")
    parser.add_argument("--latex", default=DEFAULT_LATEX, help="latexmk target (default: pdf) -> uses '-pdf'.")
    parser.add_argument(
        "--opts",
        default=DEFAULT_OPTS,
        help="Extra latexmk opts (default: '-shell-escape -auxdir=AUX')."
    )
    parser.add_argument(
        "--show-build-output",
        action="store_true",
        help="Show latexmk output (stdout/stderr) during builds."
    )
    parser.add_argument(
        "--keep-aux",
        action="store_true",
        help="Do not clean aux files or remove AUX directory at the end."
    )
    args = parser.parse_args()

    # Locate version files
    candidates = find_version_files(args.base)
    if not candidates:
        print(f"{C.RED}ERROR:{C.RESET} No version files found for base '{args.base}'.", file=sys.stderr)
        sys.exit(1)

    # Header: Found N files
    names = ", ".join(p.name for p in candidates)
    print(f"{C.BOLD}Found {len(candidates)} exam file(s):{C.RESET} {names}\n")

    any_fail = False

    for tex in candidates:
        out_base = tex.with_suffix("")  # drop .tex
        v = version_letter_from_filename(tex).upper()
        print(f"{C.BOLD}Processing {tex.name} (version {v})...{C.RESET}")

        original = tex.read_text(encoding="utf-8", errors="ignore")

        # ---- PRINT (noanswers) ----
        print(f"  {C.CYAN}Compiling print version...{C.RESET}")
        try:
            tmp_text = set_answers_mode(original, "noanswers")
            if tmp_text != original:
                tex.write_text(tmp_text, encoding="utf-8")

            result = run_latexmk(tex, v, args.latex, args.opts, args.show_build_output)
            if result.returncode != 0:
                any_fail = True
                print(f"  {C.RED}Build failed for print version of {tex.name}.{C.RESET}")
            else:
                pdf_path = tex.with_suffix(".pdf")
                target = Path(f"{out_base}-{PRINT_LABEL}.pdf")
                if target.exists():
                    target.unlink()
                pdf_path.rename(target)
                print(f"  {C.GREEN}Created:{C.RESET} {target.name}")
        finally:
            # restore original after this phase
            if tex.read_text(encoding="utf-8", errors="ignore") != original:
                tex.write_text(original, encoding="utf-8")

        # ---- ANSWERS ----
        print(f"  {C.CYAN}Compiling answers version...{C.RESET}")
        try:
            tmp_text = set_answers_mode(original, "answers")
            if tmp_text != original:
                tex.write_text(tmp_text, encoding="utf-8")

            result = run_latexmk(tex, v, args.latex, args.opts, args.show_build_output)
            if result.returncode != 0:
                any_fail = True
                print(f"  {C.RED}Build failed for answers version of {tex.name}.{C.RESET}")
            else:
                pdf_path = tex.with_suffix(".pdf")
                target = Path(f"{out_base}-{ANSWERS_LABEL}.pdf")
                if target.exists():
                    target.unlink()
                pdf_path.rename(target)
                print(f"  {C.GREEN}Created:{C.RESET} {target.name}")
        finally:
            # restore original after this phase
            if tex.read_text(encoding="utf-8", errors="ignore") != original:
                tex.write_text(original, encoding="utf-8")

        print()  # blank line between versions

    # ---- Cleanup ----
    if not args.keep_aux:
        print(f"{C.DIM}Cleaning up auxiliary files...{C.RESET}\n")
        try:
            subprocess.run(["latexmk", f"-{args.latex}", "-c"], check=False, capture_output=True, text=True)
        except Exception:
            pass
        shutil.rmtree("AUX", ignore_errors=True)

    # ---- Summary ----
    if any_fail:
        print(f"{C.RED}{C.BOLD}Some builds failed. See messages above.{C.RESET}")
        sys.exit(1)
    else:
        print(f"{C.GREEN}{C.BOLD}All exam versions compiled successfully!{C.RESET}")

if __name__ == "__main__":
    main()
