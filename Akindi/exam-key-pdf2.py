#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# 1) CLI parsing
# ──────────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "prefix",
        help="Prefix for versioned TeX files, e.g., 'exam' for exam-A.tex, exam-B.tex",
    )
    return ap.parse_args()


# ──────────────────────────────────────────────────────────────────────────────
# 2) Environment + path resolution
# ──────────────────────────────────────────────────────────────────────────────
def resolve_paths() -> Tuple[Path, Path, str, Path]:
    """
    Returns: (script_dir, extract_key, base_key, base_key_tex)
    - base_key is the stem for the template (e.g. 'exam-key' → 'exam-key.tex')
    """
    script_dir = Path(__file__).resolve().parent
    extract_key = script_dir / "exam-extract-key.py"
    base_key = "exam-key"
    base_key_tex = script_dir / f"{base_key}.tex"
    return script_dir, extract_key, base_key, base_key_tex


def validate_dependencies(extract_key: Path, base_key_tex: Path) -> None:
    if not base_key_tex.exists():
        sys.stderr.write(f"[ERROR] Missing template: {base_key_tex}\n")
        sys.exit(1)
    if not extract_key.exists():
        sys.stderr.write(f"[ERROR] Missing extractor: {extract_key}\n")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# 3) Version discovery (what exam-?.tex files exist)
# ──────────────────────────────────────────────────────────────────────────────
def discover_versioned(prefix: str) -> Tuple[List[Path], str]:
    """
    Returns:
      - sorted list of matching '<prefix>-?.tex' files
      - file_prefix ending with '-' (e.g. 'exam-') to build other names
    """
    # Accept both 'exam' and 'exam-' as input; normalize to 'exam-'
    file_prefix = prefix if prefix.endswith("-") else f"{prefix}-"
    versioned = sorted(Path(".").glob(f"{file_prefix}?.tex"))
    if not versioned:
        sys.stderr.write(f"[ERROR] No files like '{file_prefix}?.tex' found.\n")
        sys.exit(1)
    return versioned, file_prefix


# ──────────────────────────────────────────────────────────────────────────────
# 4) Key extraction (run the external extractor and parse mapping)
# ──────────────────────────────────────────────────────────────────────────────
def run_extractor_to_file(extract_key: Path, tex_path: str, out_txt: str) -> None:
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


def load_version_key_map(keys_txt_path: Path) -> Dict[str, str]:
    """
    The extractor is expected to print lines like:
        <version>\t<ans1>\t<ans2>\t...
    Returns a dict: {version_char: 'ans1 ans2 ...'}
    """
    if not keys_txt_path.exists():
        sys.stderr.write(f"[ERROR] Missing extracted key file: {keys_txt_path}\n")
        sys.exit(1)

    mapping: Dict[str, str] = {}
    for raw in keys_txt_path.read_text().splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        version = parts[0].strip()
        answers = " ".join(p.strip() for p in parts[1:] if p.strip())
        if not version:
            continue
        mapping[version] = answers
    if not mapping:
        sys.stderr.write(f"[ERROR] No keys parsed from {keys_txt_path}\n")
        sys.exit(1)
    return mapping


# ──────────────────────────────────────────────────────────────────────────────
# 5) TeX templating for a single version (fill \FILE, \VERSION, \KEY)
# ──────────────────────────────────────────────────────────────────────────────
def render_exam_key_tex(
    template_path: Path,
    source_file: str,
    version: str,
    key_line: str,
    out_stem: str,
) -> Path:
    """
    Create a temporary TeX file for this version by replacing placeholders in
    the template. Returns the path to the generated .tex file.
    """
    src = template_path.read_text()
    src = src.replace(r"\FILE", source_file)
    src = src.replace(r"\VERSION", version)
    src = src.replace(r"\KEY", key_line)

    tex_out = Path(f"{out_stem}.tex")
    tex_out.write_text(src)
    return tex_out


# ──────────────────────────────────────────────────────────────────────────────
# 6) Build PDF with latexmk and do minimal cleanup
# ──────────────────────────────────────────────────────────────────────────────
def latexmk_pdf(target: Path, script_dir: Path, pretex: Path, quiet: bool = True) -> Path:
    """
    Runs latexmk to compile the given TeX file to PDF in the current directory.
    Returns the produced PDF path.
    """
    # latexmk -pdf -f -quiet tex_file
    cmd = [
        "latexmk",
        "-pdf",
        "-f",  # continue on errors
        f"-usepretex={pretex}",
    ]
    if quiet:
        cmd.append("-quiet")
    cmd.append(str(script_dir / target))

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.stderr.write("[ERROR] latexmk not found in PATH.\n")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[ERROR] latexmk failed for {tex_file} ({e.returncode}).\n")
        sys.exit(e.returncode)

    produced_pdf = Path(target).with_suffix(".pdf")
    if not produced_pdf.exists():
        sys.stderr.write(f"[ERROR] Expected PDF not found: {produced_pdf}\n")
        sys.exit(1)
    return produced_pdf


def minimal_cleanup_for_template(base_key: str) -> None:
    """
    Mirrors the small cleanup from the original script:
      rm -f exam-key.{aux,fdb*,fls,log}
    """
    for pattern in [f"{base_key}.aux", f"{base_key}.fdb*", f"{base_key}.fls", f"{base_key}.log"]:
        for p in Path(".").glob(pattern):
            try:
                p.unlink()
            except FileNotFoundError:
                pass


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator (previously `main`)
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    script_dir, extract_key, base_key, base_key_tex = resolve_paths()
    validate_dependencies(extract_key, base_key_tex)

    # Discover versions like '<prefix>-A.tex', '<prefix>-B.tex', ...
    versioned, file_prefix = discover_versioned(args.prefix)
    versions = [Path(p).stem.split("-")[-1] for p in versioned]

    # Extract all keys (the extractor prints multiple lines; we store them in one file)
    tex_path = f"{file_prefix}"                 # input to the extractor (matches original script)
    out_txt = f"{file_prefix.removesuffix('-')}.keys"
    run_extractor_to_file(extract_key, tex_path, out_txt)

    version_to_key = load_version_key_map(Path(out_txt))

    # Build PDFs: one per discovered version
    for v in versions:
        key_line = version_to_key.get(v.upper()).replace(" ", ",")
        if not key_line:
            sys.stderr.write(f"[WARN] No key for version '{v.upper()}', skipping.\n")
            continue

        # 1) materialize template with placeholders filled
        out_stem = f"{base_key}-{v}"            # e.g., 'exam-key-A'
        pretex = f"\\def\\FILE{{{args.prefix}}} \\def\\VERSION{{{v.upper()}}} \\def\\KEY{{{key_line}}} \\def\\SOURCE{{{script_dir}}}"

        # 2) compile to PDF and move/rename as needed (keep produced name)
        produced_pdf = latexmk_pdf(base_key, script_dir, pretex, quiet=True)

        # Ensure final name stays as '<base_key>-<v>.pdf' (latexmk already did that)
        target_pdf = Path(f"{out_stem}.pdf")
        if produced_pdf != target_pdf:
            try:
                if target_pdf.exists():
                    target_pdf.unlink()
                produced_pdf.rename(target_pdf)
            except OSError as e:
                sys.stderr.write(f"[WARN] Could not rename {produced_pdf} → {target_pdf}: {e}\n")

    # Minimal template byproduct cleanup (matches original)
    minimal_cleanup_for_template(base_key)


if __name__ == "__main__":
    main()
