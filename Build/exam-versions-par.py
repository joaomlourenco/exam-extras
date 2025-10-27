#!/usr/bin/env python3
"""
exam_versions.py — parallel-by-version with live progress

- Builds each version (exam-a.tex, exam-b.tex, …) in PARALLEL
- Within a version: SEQUENTIAL builds → print, then answers
- Live progress line with spinner: shows sub-steps per version (0/2, 1/2, 2/2)
- Captures latexmk output; only shows with --show-build-output or on failure

Usage:
  python exam-versions.py BASE
  python exam-versions.py exam --show-build-output
"""

from __future__ import annotations
import argparse
import re
import shutil
import subprocess
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict
from queue import Queue, Empty
import time
import threading

# ---------- Defaults ----------
DEFAULT_LATEX = "pdf"
DEFAULT_OPTS  = "-shell-escape -auxdir=AUX"
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
        BOLD=DIM=RED=GREEN=YELLOW=BLUE=CYAN=GRAY=RESET=""

# ---------- Regex to toggle answers/noanswers ----------
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

def indent(s: str, pad: int = 2) -> str:
    prefix = " " * pad
    return "\n".join(prefix + line for line in s.splitlines())

def run_latexmk(
    tex: Path,
    version_letter: str,
    latex: str,
    opts: str,
) -> Tuple[int, str, str]:
    cmd = [
        "latexmk",
        f"-{latex}",
        f"-usepretex=\\def\\VERSION{{\\MakeUppercase{{{version_letter}}}}}"
    ]
    if opts:
        cmd[1:1] = [o for o in opts.split() if o.strip()]
    cmd.append(str(tex))

    try:
        result = subprocess.run(
            cmd, text=True, capture_output=True, check=False
        )
    except FileNotFoundError:
        return (127, "", "'latexmk' not found on PATH.")
    return (result.returncode, result.stdout, result.stderr)

# ---------- Event types for progress ----------
# ('start', name)
# ('substep', name, completed_substeps)   # 0,1,2
# ('done', name, ok_bool)
# ('log', name, stdout_str, stderr_str)   # only when --show-build-output or on failure

# ---------- Worker (per version) ----------
def build_one_version(
    tex: Path,
    latex: str,
    opts: str,
    show_build_output: bool,
    event_q: Queue
) -> Tuple[str, bool, str]:
    """
    Builds a single version SEQUENTIALLY: print then answers.
    Posts progress/log events into event_q.

    Returns (version_display_block, success_bool, key_name_for_ordering)
    """
    out_lines: List[str] = []
    name_for_order = tex.name

    v = version_letter_from_filename(tex).upper()
    header = f"{C.BOLD}Processing {tex.name} (version {v})...{C.RESET}"
    out_lines.append(header)
    event_q.put(('start', tex.name))
    event_q.put(('substep', tex.name, 0))

    # Read original
    original = tex.read_text(encoding="utf-8", errors="ignore")

    # ---- PRINT (noanswers) ----
    out_lines.append(f"  {C.CYAN}Compiling print version...{C.RESET}")
    try:
        tmp_text = set_answers_mode(original, "noanswers")
        if tmp_text != original:
            tex.write_text(tmp_text, encoding="utf-8")

        rc, so, se = run_latexmk(tex, v, latex, opts)
        # progress update: finished substep 1
        if (show_build_output or rc != 0) and (so.strip() or se.strip()):
            event_q.put(('log', tex.name, so, se))
            if so.strip():
                out_lines.append(f"{C.GRAY}{indent(so.strip())}{C.RESET}")
            if se.strip():
                out_lines.append(f"{C.YELLOW}{indent(se.strip())}{C.RESET}")

        if rc != 0:
            out_lines.append(f"  {C.RED}Build failed for print version of {tex.name}.{C.RESET}")
            event_q.put(('substep', tex.name, 1))  # we attempted 1st substep
            event_q.put(('done', tex.name, False))
            if tex.read_text(encoding="utf-8", errors="ignore") != original:
                tex.write_text(original, encoding="utf-8")
            out_lines.append("")
            return ("\n".join(out_lines), False, name_for_order)

        pdf_path = tex.with_suffix(".pdf")
        target = tex.with_suffix("").with_name(f"{tex.stem}-{PRINT_LABEL}.pdf")
        if target.exists():
            target.unlink()
        pdf_path.rename(target)
        out_lines.append(f"  {C.GREEN}Created:{C.RESET} {target.name}")
        event_q.put(('substep', tex.name, 1))

    finally:
        if tex.read_text(encoding="utf-8", errors="ignore") != original:
            tex.write_text(original, encoding="utf-8")

    # ---- ANSWERS ----
    out_lines.append(f"  {C.CYAN}Compiling answers version...{C.RESET}")
    try:
        tmp_text = set_answers_mode(original, "answers")
        if tmp_text != original:
            tex.write_text(tmp_text, encoding="utf-8")

        rc, so, se = run_latexmk(tex, v, latex, opts)
        if (show_build_output or rc != 0) and (so.strip() or se.strip()):
            event_q.put(('log', tex.name, so, se))
            if so.strip():
                out_lines.append(f"{C.GRAY}{indent(so.strip())}{C.RESET}")
            if se.strip():
                out_lines.append(f"{C.YELLOW}{indent(se.strip())}{C.RESET}")

        if rc != 0:
            out_lines.append(f"  {C.RED}Build failed for answers version of {tex.name}.{C.RESET}")
            event_q.put(('substep', tex.name, 2))  # attempted second substep
            event_q.put(('done', tex.name, False))
            if tex.read_text(encoding="utf-8", errors="ignore") != original:
                tex.write_text(original, encoding="utf-8")
            out_lines.append("")
            return ("\n".join(out_lines), False, name_for_order)

        pdf_path = tex.with_suffix(".pdf")
        target = tex.with_suffix("").with_name(f"{tex.stem}-{ANSWERS_LABEL}.pdf")
        if target.exists():
            target.unlink()
        pdf_path.rename(target)
        out_lines.append(f"  {C.GREEN}Created:{C.RESET} {target.name}")
        event_q.put(('substep', tex.name, 2))
        event_q.put(('done', tex.name, True))

    finally:
        if tex.read_text(encoding="utf-8", errors="ignore") != original:
            tex.write_text(original, encoding="utf-8")

    out_lines.append("")
    return ("\n".join(out_lines), True, name_for_order)

# ---------- Live progress renderer ----------
SPINNER = ["|", "/", "-", "\\"]

def render_progress(status: Dict[str, int], total_versions: int, logs_pending: bool, tick: int) -> str:
    """
    status[name] => completed substeps (0,1,2) for that version.
    Shows a single-line progress with per-version substeps and spinner.
    """
    done_substeps = sum(status.values())
    total_substeps = total_versions * 2
    pct = int(100 * done_substeps / max(1, total_substeps))
    bar_w = 24
    filled = int(bar_w * pct / 100)
    bar = "[" + "#" * filled + "-" * (bar_w - filled) + "]"
    spinner = SPINNER[tick % len(SPINNER)]
    parts = [f"{spinner} {bar} {pct:3d}%  ({done_substeps}/{total_substeps} steps)"]

    # Append small per-version summary like a:1/2 b:2/2 …
    tail = "  " + " ".join(f"{name}:{v}/2" for name, v in status.items())
    if logs_pending:
        tail += f"  {C.DIM}[logs ready]{C.RESET}"
    return parts[0] + tail

def progress_loop(event_q: Queue, status: Dict[str, int], total_versions: int, print_logs_inline: bool, stop_event: threading.Event):
    """
    Consume events and update an in-place progress line.
    If print_logs_inline is True, prints logs as they come (still shows progress after).
    """
    tick = 0
    logs_buffer: List[Tuple[str, str, str]] = []  # (name, stdout, stderr)
    tty = sys.stdout.isatty()

    while not stop_event.is_set() or not event_q.empty():
        try:
            evt = event_q.get(timeout=0.05)
        except Empty:
            evt = None

        logs_pending = False
        if evt:
            etype = evt[0]
            if etype == 'start':
                name = evt[1]
                status[name] = 0
            elif etype == 'substep':
                name, steps = evt[1], evt[2]
                status[name] = steps
            elif etype == 'done':
                name, ok = evt[1], evt[2]
                # Ensure 2/2 even if earlier failure recorded 1/2
                status[name] = max(2, status.get(name, 0))
            elif etype == 'log':
                name, so, se = evt[1], evt[2], evt[3]
                logs_buffer.append((name, so, se))
                logs_pending = True

        # Print or update progress line
        if tty:
            line = render_progress(status, total_versions, logs_pending or len(logs_buffer) > 0, tick)
            sys.stdout.write("\r" + " " * (shutil.get_terminal_size((120, 20)).columns - 1) + "\r")
            sys.stdout.write(line[:shutil.get_terminal_size((120, 20)).columns - 1])
            sys.stdout.flush()
        tick += 1

        # If user requested to show logs inline, dump and keep progress going
        if print_logs_inline and logs_buffer:
            if tty:
                sys.stdout.write("\n")
            while logs_buffer:
                name, so, se = logs_buffer.pop(0)
                if so.strip():
                    print(f"{C.GRAY}{indent(so.strip())}{C.RESET}")
                if se.strip():
                    print(f"{C.YELLOW}{indent(se.strip())}{C.RESET}")

    # Clear progress line at the end for TTY
    if sys.stdout.isatty():
        sys.stdout.write("\r" + " " * (shutil.get_terminal_size((120, 20)).columns - 1) + "\r")
        sys.stdout.flush()

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Build exam versions (print and answers) in parallel per version with live progress.")
    parser.add_argument("base", help="LaTeX base filename WITHOUT '-V.tex' (e.g., 'exam' for 'exam-a.tex').")
    parser.add_argument("--latex", default=DEFAULT_LATEX, help="latexmk target (default: pdf) -> uses '-pdf'.")
    parser.add_argument("--opts", default=DEFAULT_OPTS, help="Extra latexmk opts (default: '-shell-escape -auxdir=AUX').")
    parser.add_argument("--show-build-output", action="store_true", help="Show latexmk output (stdout/stderr) during builds.")
    parser.add_argument("--keep-aux", action="store_true", help="Do not clean aux files or remove AUX directory at the end.")
    parser.add_argument("--max-workers", type=int, default=None, help="Limit parallel workers (default: number of versions).")
    args = parser.parse_args()

    # Locate version files
    candidates = find_version_files(args.base)
    if not candidates:
        print(f"{C.RED}ERROR:{C.RESET} No version files found for base '{args.base}'.", file=sys.stderr)
        sys.exit(1)

    names = ", ".join(p.name for p in candidates)
    print(f"{C.BOLD}Found {len(candidates)} exam file(s):{C.RESET} {names}\n")

    # Setup event queue + progress thread
    event_q: Queue = Queue()
    progress_status: Dict[str, int] = {}  # name -> completed substeps (0..2)
    stop_progress = threading.Event()
    progress_thread = threading.Thread(
        target=progress_loop,
        args=(event_q, progress_status, len(candidates), args.show_build_output, stop_progress),
        daemon=True
    )
    progress_thread.start()

    # Schedule parallel builds (one per version)
    max_workers = args.max_workers or len(candidates)
    results_by_name = {}
    any_fail = False

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {
            pool.submit(build_one_version, tex, args.latex, args.opts, args.show_build_output, event_q): tex.name
            for tex in candidates
        }
        for fut in as_completed(future_map):
            name = future_map[fut]
            try:
                block, ok, key = fut.result()
            except Exception as e:
                block = (
                    f"{C.BOLD}Processing {name}...{C.RESET}\n"
                    f"  {C.RED}Unexpected error in worker:{C.RESET} {e}\n"
                )
                ok = False
                key = name
            results_by_name[key] = (block, ok)

    # Stop progress and join
    stop_progress.set()
    progress_thread.join()

    # Print blocks in the same order we discovered the files
    for tex in candidates:
        block, ok = results_by_name.get(tex.name, ("", False))
        if block:
            print(block, end="")
        any_fail |= (not ok)

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
