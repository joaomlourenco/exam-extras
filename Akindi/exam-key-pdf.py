#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Pretty, colored progress messages
# ──────────────────────────────────────────────────────────────────────────────
RESET = "\033[0m"
COLORS = {
    "blue": "\033[34m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "red": "\033[31m",
    "bold": "\033[1m",
}

def _cprint(emoji: str, color: str, msg: str) -> None:
    color_code = COLORS.get(color, "")
    print(f"{color_code}{emoji} {msg}{RESET}")


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
def discover_versioned(prefix: str) -> List[Path]:
    """
    Returns:
      - sorted list of matching '<prefix>-?.tex' files
    """
    # Accept both 'exam' and 'exam-' as input; normalize to 'exam-'
    versioned = sorted(Path(".").glob(f"{prefix}-?.tex"))
    if not versioned:
        sys.stderr.write(f"[ERROR] No files like '{prefix}-?.tex' found.\n")
        sys.exit(1)
    # Progress: how many and which versions
    names = [Path(p).stem.split("-")[-1] for p in versioned]
    _cprint("🔎", "blue", f"Found {len(versioned)} version(s): {', '.join(names)}")
    return versioned


# ──────────────────────────────────────────────────────────────────────────────
# 4) Key extraction (run the external extractor and parse mapping)
# ──────────────────────────────────────────────────────────────────────────────
def run_extractor_to_file(extract_key: Path, tex_path: str, out_txt: str) -> None:
    _cprint("🚀", "magenta", f"Running key extractor on '{tex_path}' → '{out_txt}'...")
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
    _cprint("✅", "green", f"Keys extracted to '{out_txt}'")


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
def latexmk_pdf(tex_file: Path, script_dir: Path, pretex: Path, prefix: str, version: str, quiet: bool = True) -> Path:
    ver_hint = Path(f"{prefix}-{version}")
    _cprint("🛠️", "cyan", f"Building PDF with latexmk for '{ver_hint}'...")
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
    cmd.append(str(script_dir / tex_file))

    try:
        result = subprocess.run(cmd,
                       check=True,
                       capture_output=True,
                       text=True,
        )
    except FileNotFoundError:
        sys.stderr.write("[ERROR] latexmk not found in PATH.\n")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"[ERROR] latexmk failed for {tex_file} ({e.returncode}).\n")
        _cprint("❌", "red", f"latexmk failed for '{ver_hint}'")
        sys.exit(e.returncode)

    produced_pdf = Path(tex_file).with_suffix(".pdf")
    if not produced_pdf.exists():
        sys.stderr.write(f"[ERROR] Expected PDF not found: {produced_pdf}\n")
        _cprint("❌", "red", f"Build did not produce PDF for '{ver_hint}'")
        sys.exit(1)
    _cprint("✅", "green", f"Built PDF: {produced_pdf}")
    return produced_pdf


def minimal_cleanup_for_template(base_key: str) -> None:
    _cprint("🧹", "yellow", f"Cleaning byproducts for template '{base_key}'...")
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
    _cprint("🧹", "green", "Cleanup complete.")


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator (previously `main`)
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    prefix = args.prefix.removesuffix("-")

    # script_dir:     the script dir
    # extract_key:    the full path to the python script to extract keys from TeX source files
    # base_key:       base file for the TeX file that fills Akindi MCQ forms (i.e., exam-key)
    # base_key_tex:   the full path to the TeX file that fills Akindi MCQ forms
    script_dir, extract_key, base_key, base_key_tex = resolve_paths()
    validate_dependencies(extract_key, base_key_tex)

    # Discover versions like '<prefix>-A.tex', '<prefix>-B.tex', ...
    # versioned:      The file names of the versions '<prefix>-a.tex', '<prefix>-b.tex', ...
    # file_prefix:    The file names without version nor extension '<prefix>'
    versioned = discover_versioned(prefix)

    # versions:       The list of versions (small caps), e.g., ['a', 'b']
    versions = [Path(p).stem.split("-")[-1] for p in versioned]

    # Extract all keys (the extractor prints multiple lines; we store them in one file)
    keys_file = f"{prefix}.keys"
    run_extractor_to_file(extract_key, prefix, keys_file)
    # load keys into dictionary
    version_to_key = load_version_key_map(Path(keys_file))

    # Build PDFs: one per discovered version
    for v in versions:
        key_line = version_to_key.get(v.upper()).replace(" ", ",")
        if not key_line:
            sys.stderr.write(f"[WARN] No key for version '{v.upper()}', skipping.\n")
            continue

        # 1) materialize template with placeholders filled
        out_stem = f"{prefix}-key-{v}"            # e.g., 'example-key-A'
        pretex = f"\\def\\FILE{{{args.prefix}}} \\def\\VERSION{{{v.upper()}}} \\def\\KEY{{{key_line}}} \\def\\SOURCE{{{script_dir}}}"

        # 2) compile to PDF and move/rename as needed (keep produced name)
        produced_pdf = latexmk_pdf(base_key, script_dir, pretex, prefix, v, quiet=True)

        # Ensure final name stays as '<base_key>-<v>.pdf' (latexmk already did that)
        target_pdf = Path(f"{out_stem}.pdf")
        if produced_pdf != target_pdf:
            try:
                if target_pdf.exists():
                    target_pdf.unlink()
                produced_pdf.rename(target_pdf)
                _cprint("✅", "green", f"Renaming {produced_pdf}->{target_pdf}")
            except OSError as e:
                sys.stderr.write(f"[WARN] Could not rename {produced_pdf} → {target_pdf}: {e}\n")

    # Minimal template byproduct cleanup (matches original)
    minimal_cleanup_for_template(base_key)


if __name__ == "__main__":
    main()
