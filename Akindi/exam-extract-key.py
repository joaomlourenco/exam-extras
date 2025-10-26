#!/usr/bin/env python3
import argparse
import glob
import os
import re
import sys
from string import ascii_lowercase

# ----------------------------
# File discovery helpers
# ----------------------------

def find_candidate_files(prefix: str):
    primary = []
    for ch in ascii_lowercase:
        primary.append(f"{prefix}-{ch}-questions.tex")
        primary.append(f"{prefix}{ch}-questions.tex")
    files = [f for pat in primary for f in glob.glob(pat)]
    if files:
        return sorted(set(files), key=str.lower)

    fallback = []
    for ch in ascii_lowercase:
        fallback.append(f"{prefix}-{ch}.tex")
        fallback.append(f"{prefix}{ch}.tex")
    files = [f for pat in fallback for f in glob.glob(pat)]
    return sorted(set(files), key=str.lower)

def extract_variant_letter(prefix: str, filename: str) -> str:
    base = os.path.basename(filename)
    pre = re.escape(prefix)
    m = re.match(rf'^{pre}-?([a-z])(?:-questions)?\.tex$', base)
    return m.group(1) if m else "?"

# ----------------------------
# Parsing utilities
# ----------------------------

def strip_tex_comments(s: str) -> str:
    # Remove unescaped % to end of line
    return re.sub(r'(?<!\\)%.*', '', s)

def iter_choice_envs(tex: str):
    """
    Yield environment bodies for each choices/oneparchoices in order.
    Supports optional [N] argument in \begin{choices}.
    """
    tex = strip_tex_comments(tex)
    pats = [
        re.compile(r'\\begin\{choices\}\s*(?:\[[^\]]*\])?\s*(?P<body>.*?)\\end\{choices\}', re.DOTALL),
        re.compile(r'\\begin\{oneparchoices\}\s*(?P<body>.*?)\\end\{oneparchoices\}', re.DOTALL),
    ]
    matches = []
    for pat in pats:
        matches += [(m.start(), m.group('body')) for m in pat.finditer(tex)]
    matches.sort(key=lambda t: t[0])
    for _, body in matches:
        yield body

def scan_commands(env_body: str):
    """
    Yields command names (\\choice, \\CHOICE, etc.) in order.
    Handles arbitrary spacing, line breaks, optional *, [args].
    """
    i, n = 0, len(env_body)
    while i < n:
        if env_body[i] == '\\':
            j = i + 1
            while j < n and env_body[j].isalpha():
                j += 1
            cmd = env_body[i+1:j]
            if j < n and env_body[j] == '*':
                j += 1
            k = j
            while k < n and env_body[k].isspace():
                k += 1
            if k < n and env_body[k] == '[':
                depth = 0
                while k < n:
                    if env_body[k] == '[':
                        depth += 1
                    elif env_body[k] == ']':
                        depth -= 1
                        if depth == 0:
                            k += 1
                            break
                    k += 1
            yield cmd
            i = max(k, j)
        else:
            i += 1

def find_all_positions(env_body: str):
    """
    Return list of (index, is_correct) for each choice/CHOICE command.
    """
    positions = []
    idx = 0
    for cmd in scan_commands(env_body):
        if cmd in ('choice', 'CHOICE'):
            idx += 1
            positions.append((idx, cmd == 'CHOICE'))
    return positions

# ----------------------------
# Output encoding helpers
# ----------------------------

def pos_to_letter(n: int) -> str:
    return chr(ord('A') + n - 1) if n >= 1 else "?"

def encode_answer(positions):
    """
    Convert positions to encoded form:
      - if all are CHOICE → "*"
      - if none → "?"
      - else → glued letters (e.g., "BD")
    """
    if not positions:
        return "?"
    if all(flag for _, flag in positions):
        return "*"
    letters = [pos_to_letter(idx) for idx, flag in positions if flag]
    return "".join(letters) if letters else "?"

# ----------------------------
# Core logic
# ----------------------------

def process_file(prefix: str, path: str):
    with open(path, 'r', encoding='utf-8') as f:
        tex = f.read()
    variant = extract_variant_letter(prefix, path).upper()
    encoded = [encode_answer(find_all_positions(body))
               for body in iter_choice_envs(tex)]
    # Return TAB-separated line: V<TAB>N1<TAB>N2...
    return "\t".join([variant] + encoded)

# ----------------------------
# Main CLI
# ----------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Summarize \\CHOICE positions per file (TAB-separated; multiple CHOICE glued; '*' if all)."
    )
    ap.add_argument("prefix", help="File name prefix X")
    ap.add_argument(
        "-o", "--output",
        help="Output file name. If omitted, results are printed to stdout."
    )
    args = ap.parse_args()

    files = find_candidate_files(args.prefix)
    if not files:
        print("No matching files found.", file=sys.stderr)
        sys.exit(1)

    results = [process_file(args.prefix, path) for path in files]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            for line in results:
                out.write(line + "\n")
    else:
        for line in results:
            print(line)

if __name__ == "__main__":
    main()
