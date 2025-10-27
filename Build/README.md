# Exam Versions Script (`exam-versions.sh`)

A shell script for automatically compiling print and answer PDFs for multiple exam versions using LaTeX.

## Overview

This script automates the batch compilation of versioned exam LaTeX files given a prefix, producing:
- A student-ready print PDF (`PREFIX-X-print.pdf`)
- A PDF answer key (`PREFIX-X-answers.pdf`)
for each variant (`X = a, b, c, ...`).

## Features

- Handles any number of exam variants with one-letter suffixes (e.g., `exam-a.tex`, `exam-b.tex`)
- Generates two PDFs for each exam variant: one with answers hidden, one with answers visible
- Uses Perl for efficient toggling of answer modes in source files
- Uses `latexmk` for robust, dependency-respecting compilation
- Sets `\VERSION` LaTeX macro for each variant
- Cleans up unnecessary auxiliary files after completion

## Usage

1. **Place all variant `.tex` files in the current directory**, named like `exam-a.tex`, `exam-b.tex`, etc.

2. **Make the script executable**:
    ```
    chmod +x exam-versions.sh
    ```

3. **Run the script** with the exam prefix:
    ```
    ./exam-versions.sh exam
    ```
   This will compile all matching variant files and produce:
   - `exam-a-print.pdf`, `exam-a-answers.pdf`
   - `exam-b-print.pdf`, `exam-b-answers.pdf`
   - etc.

## Requirements

- Bash shell
- Perl (for answer toggling)
- `latexmk` (for automated compilation)
- LaTeX distribution with packages required by your exam source (e.g., `exam`, `minted`, etc.)

## File Naming Convention

- Valid variant files: `PREFIX-[a-z].tex`
- For example: `exam-a.tex`, `exam-b.tex`, `test-x.tex`

## How It Works

- For each variant `.tex` file:
  1. The script sets up the print (no answers) version.
  2. Uses Perl to ensure the exam is set to `noanswers` mode.
  3. Runs LaTeX compilation and renames the resulting PDF to `-print.pdf`.
  4. Switches to `answers` mode.
  5. Recompiles and renames the resulting PDF to `-answers.pdf`.
  6. Cleans up temp files and auxiliary directories.

## Customization

- You can modify the definitions of `PRINT` and `ANSWERS` inside the script for custom output naming.
- Pass additional options to `latexmk` as needed via the `OPTS` variable.

## Troubleshooting

- If you see `Usage: exam-versions.sh LATEX_FILE (without '-V.tex')`, ensure you passed the correct prefix (not including the variant letter).
- Make sure Perl and `latexmk` are available in your shell.
- Use the `-shell-escape` flag for source files using the `minted` package.

## License

The LaTeX Project Public License (LPPL Version 1.3c)

## Author & Credits

Script by[João Lourenço](https://docentes.fct.unl.pt/joao-lourenco).

---

For further customization or help, consult the comments in the script source.
