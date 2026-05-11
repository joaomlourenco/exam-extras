#!/usr/bin/env python3
import argparse
import os
import re
import sys
from typing import Dict, List, Tuple, Optional

# If a question has zero correct options, what token should we emit?
# Spec ambiguity: latest spec doesn't mention it, earlier you used "?".
NO_CORRECT_TOKEN = "?"

# \include{...} or \input{...}
INCLUDE_INPUT_RE = re.compile(r"\\(include|input)\{([^}]+)\}")

# \begin{choices} or \begin{choices}[...]
BEGIN_CHOICES_RE = re.compile(r"\\begin\{choices\}(?:\[[^\]]*\])?")
END_CHOICES_RE = re.compile(r"\\end\{choices\}")

# Questions start at \question
QUESTION_SPLIT_RE = re.compile(r"(\\question\b)")

# choice commands inside choices environment
CHOICE_CMD_RE = re.compile(r"\\(CorrectChoice|CHOICE|choice)\b")


def debug_print(enabled: bool, msg: str) -> None:
    if enabled:
        print(f"[debug] {msg}", file=sys.stderr)


def debug_path(path: str) -> str:
    """
    Return relative path if inside current working directory,
    otherwise return absolute path.
    """
    cwd = os.getcwd()
    abs_path = os.path.abspath(path)
    try:
        if os.path.commonpath([cwd, abs_path]) == cwd:
            return os.path.relpath(abs_path, cwd)
    except ValueError:
        # Different drives on Windows
        pass
    return abs_path
    
    
def strip_comments_preserve_lines(text: str) -> str:
    """
    Removes LaTeX comments starting with % unless escaped as \\%.
    Keeps line breaks to avoid disrupting scanning too much.
    """
    out_lines: List[str] = []
    for line in text.splitlines(True):  # keepends=True
        i = 0
        cut = None
        while True:
            j = line.find("%", i)
            if j == -1:
                break
            # escaped \\% should not start a comment
            if j > 0 and line[j - 1] == "\\":
                i = j + 1
                continue
            cut = j
            break
        if cut is None:
            out_lines.append(line)
        else:
            out_lines.append(line[:cut] + ("\n" if line.endswith("\n") else ""))
    return "".join(out_lines)


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def resolve_tex_path(base_dir: str, target: str) -> str:
    """
    Resolve include/input target relative to base_dir.
    Accept both "file" and "file.tex".
    """
    t = target.strip()

    # Try exactly as written first
    p1 = os.path.join(base_dir, t)
    if os.path.isfile(p1):
        return p1

    # If no .tex extension, try adding it
    if not t.endswith(".tex"):
        p2 = os.path.join(base_dir, t + ".tex")
        if os.path.isfile(p2):
            return p2

    # Return the "as written" path for a clear error message
    return p1


def expand_includes_inputs(
    main_path: str,
    debug: bool = False,
    _stack: Tuple[str, ...] = (),
    _cache: Optional[Dict[str, str]] = None,
) -> str:
    """
    Recursively expand \\include{...} and \\input{...} by inlining contents.
    Avoids cycles and caches expansions.
    Resolves \\jobname macro to the basename of the main file.
    """
    if _cache is None:
        _cache = {}

    abs_main = os.path.abspath(main_path)

    if abs_main in _stack:
        cycle = " -> ".join(list(_stack) + [abs_main])
        raise RuntimeError(f"Include/Input cycle detected: {cycle}")

    if abs_main in _cache:
        debug_print(debug, f"cache hit: {debug_path(abs_main)}")
        return _cache[abs_main]

    debug_print(debug, f"reading: {debug_path(abs_main)}")
    base_dir = os.path.dirname(abs_main)
    
    # Get the jobname (basename without extension)
    jobname = os.path.splitext(os.path.basename(abs_main))[0]

    raw = read_text_file(abs_main)
    text = strip_comments_preserve_lines(raw)
    
    # Replace \jobname with the actual jobname
    text = text.replace(r"\jobname", jobname)

    def repl(m: re.Match) -> str:
        cmd = m.group(1)
        target = m.group(2)

        inc_path = resolve_tex_path(base_dir, target)
        if not os.path.exists(inc_path):
            raise FileNotFoundError(
                f"{cmd} target not found: '{target}' (resolved to '{inc_path}')"
            )

        debug_print(debug, f"{cmd}: {debug_path(inc_path)}")
        inner = expand_includes_inputs(
            inc_path, debug=debug, _stack=_stack + (abs_main,), _cache=_cache
        )
        label = os.path.basename(inc_path)
        return (
            f"\n% --- begin {cmd}d: {label} ---\n"
            f"{inner}\n"
            f"% --- end {cmd}d: {label} ---\n"
        )

    expanded = INCLUDE_INPUT_RE.sub(repl, text)
    _cache[abs_main] = expanded
    return expanded


def find_main_files(prefix: str, debug: bool = False) -> List[Tuple[str, str]]:
    """
    Find main files in current directory matching:
      P-[a-z] or P[a-z], optional .tex

    Returns list of (version_letter, filename), sorted by version.
    """
    files = os.listdir(os.getcwd())
    p = re.escape(prefix)
    pat = re.compile(rf"^{p}-?([a-z])(?:\.tex)?$")

    matches: List[Tuple[str, str]] = []
    for fn in files:
        m = pat.match(fn)
        if m:
            matches.append((m.group(1), fn))

    matches.sort(key=lambda t: t[0])
    debug_print(debug, f"main files: {matches}")
    return matches


def split_into_questions(text: str) -> List[str]:
    """
    Split document into chunks starting at each \\question.
    Returns list where each element begins with '\\question'.
    """
    parts = QUESTION_SPLIT_RE.split(text)
    if len(parts) <= 1:
        return []

    # parts: [preamble, '\\question', body1, '\\question', body2, ...]
    out: List[str] = []
    it = iter(parts[1:])
    for qtok, body in zip(it, it):
        out.append(qtok + body)
    return out


def extract_first_choices_block(question_text: str) -> Optional[str]:
    """
    Find and return the inner text of the FIRST choices environment in a question.
    """
    m = BEGIN_CHOICES_RE.search(question_text)
    if not m:
        return None
    start = m.end()
    n = END_CHOICES_RE.search(question_text, start)
    if not n:
        # Unclosed choices: treat rest as the block
        return question_text[start:]
    return question_text[start:n.start()]


def key_for_choices_block(block: str) -> tuple[str, int]:
    """
    Compute key token for one choices block.
    Returns (token, total_number_of_choices).
    """
    option_index = 0
    correct_indices = set()

    for m in CHOICE_CMD_RE.finditer(block):
        cmd = m.group(1)
        if cmd in ("CorrectChoice", "CHOICE"):
            correct_indices.add(option_index)
        option_index += 1

    total = option_index

    if total == 0:
        return (NO_CORRECT_TOKEN, 0)
    if len(correct_indices) == 0:
        return (NO_CORRECT_TOKEN, total)
    if len(correct_indices) == total:
        return ("*", total)

    letters = [chr(ord("A") + i) for i in sorted(correct_indices)]
    return ("".join(letters), total)


def generate_keys(expanded_text: str, debug: bool = False) -> List[str]:
    """
    Generate one key token per \\question.
    Uses the FIRST choices environment inside each question.

    Debug output (if enabled):
        [debug] qN: key=TOKEN / TOTAL_CHOICES
    """
    questions = split_into_questions(expanded_text)
    debug_print(debug, f"found {len(questions)} questions")

    keys: List[str] = []
    for qi, qtext in enumerate(questions, start=1):
        block = extract_first_choices_block(qtext)
        if block is None:
            keys.append(NO_CORRECT_TOKEN)
            debug_print(debug, f"q{qi}: no choices -> {NO_CORRECT_TOKEN} / 0")
            continue

        token, total = key_for_choices_block(block)
        keys.append(token)
        debug_print(debug, f"{qi:2} [{total}] -> {token}")

    return keys


def output_filename_from_prefix(prefix: str) -> str:
    out_prefix = prefix[:-1] if prefix.endswith("-") else prefix
    return f"{out_prefix}-keys.txt"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate answer keys from exam LaTeX files.")
    ap.add_argument("prefix", help='Prefix like "P" used to match main files (P-a, P-b, Pa, Pb, ...).')
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="Print results to STDOUT (do not write output file).")
    ap.add_argument("-d", "--debug", action="store_true",
                    help="Print debug info to STDERR.")
    args = ap.parse_args()

    mains = find_main_files(args.prefix, debug=args.debug)
    if not mains:
        print(f"ERROR: no main files found for prefix '{args.prefix}'", file=sys.stderr)
        return 2

    lines: List[str] = []
    for version, fn in mains:
        debug_print(args.debug, f"processing version={version} file={fn}")
        expanded = expand_includes_inputs(fn, debug=args.debug)
        keys = generate_keys(expanded, debug=args.debug)

        # TAB-separated output: [VERSION]<TAB>KEY1<TAB>KEY2...
        line = "\t".join([f"[{version.upper()}]"] + keys)
        lines.append(line)

    output = "\n".join(lines) + "\n"

    if args.dry_run:
        sys.stdout.write(output)
        return 0

    # When NOT in dry-run, output goes to stdout for the caller to capture
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



# Make me a python script that receives:
# Option "-n" "--dry-run" prints the results to the output without storing into a file
# Option "-d" "--debug" prints debug information on the multiple steps of the process to understand whatis happening.
#
# 1) receive a prefix "P" from the command line
# 2) search the current directory for files "P-[a-z]" or P[a-z]".  The additional letter is the version. The are the main files Mi.
# 3) For each Mi, do:
# 3.1) load Mi into memory
# 3.2) scan Mi for "\include{file}" or "\input{file"}.
# 3.3) in memory, replace the "\include{…}" with the file contents (consider both "file" and "file.tex")
# 3.4) do this recursively, as "file" may also contains "\include{another-file}" and so on
#
# At this point, you should have a representation of the main file in memory os a LaTeX file with no "\include{…}" commands.
# Now, this file is an "exam" class file, with the following extensions:
# a) \CHOICE is a synonymous for "\CorrectChoice"
# b) "\begin{choices}" may have an optics argument as "\begin{choices}[…]"
#
# \CHOICE is synonymous for \CorrectChoice. that means:
#     •    \CHOICE ... (no braces) marks correct, and
#     •    \CorrectChoice ... marks correct
# …and plain \choice ... (lowercase) is incorrect
#
#
# Scan the file in memory to generate the answer key for this file.
# Each question starts with a "\question".  Follows some text. Then "\begin{quesitons}[…]" (the "[…]") is optional, followed by the options/answers, followed by "\end{questions}".
# Ignore all standard LaTeX commented areas.
#
# One question may have more than one correct answer/option.
#
# Process the next main file Mi
#
# Print the key to the STDOUT (-n) or to the file "prefix-keys.txt" (drop the final "-" in prefix is exists).
#
# Output format for multiple correct answers in one question:
# Format (output in caps lock):
# [VERSION1] KEY1 KEY2 KEY3 …
# [VERSION2] KEY1 KEY2 KEY3 …
#
# Separator is <TAB> and not space.
#
# If both A and C are correct, the token is "AC".
# If both A and C and D are correct, the token is "ACD".
# If all options are correct, use "*"
#
#
#
# IMPORTANT:  do not assume stuff. If the specification is not clear, ask before proposing a solution!
