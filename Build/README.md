# Exam Versions Script (`exam-versions.sh`)

A python script for automatically compiling print and answer PDFs for multiple exam versions using LaTeX.

## Overview

* 🎨 **Colorized output**;
* 🔄 **Automatic version detection:** Detects all versioned `.tex` files (`exam-a.tex`, `exam-b.tex`, …);
* 📄 **Dual PDF generation:** Runs `latexmk` twice per version (producing both *print* and *answers* PDFs);
* 🏷️ **Version labeling:** Injects a `\VERSION` macro (e.g. `A`, `B`, `C`) when compiling the source files;
* 🧹 **Clean workspace:** Uses `-auxdir=AUX` and, on success, cleans the `auxdir`;
* 🐍 **Pure Python:** no bash/Perl;
* 🌐 **Cross-platform support:** pure python;
* 🔇 **Smart output control:** Toggles between `noanswers` and `answers` modes;
* ⚙️ **Command-line configurability:** Check the `-h` command line option;
* 🔒 **Source file preservation:** keeps source files intact.


---

## 🧰 Requirements

- **Python 3.8+**
- **latexmk** available on your system path
- LaTeX sources must:
  - Contain a line including the token `answers` or `noanswers`
  - Accept a `\def\VERSION{...}` macro defined via the `-usepretex` option

## 🚀 Usage

1. **Place all variant `.tex` files in the current directory**, named like `exam-a.tex`, `exam-b.tex`, etc.

2. **Make the script executable**:
    ```
    chmod +x PATH_TO_SCRIPT/exam-versions.py
    ```

3. **Run the script** with the exam prefix:
    ```
    PATH_TO_SCRIPT/exam-versions.py exam
    ```
   This will compile all matching variant files and produce:
   - `exam-a-print.pdf`, `exam-a-answers.pdf`
   - `exam-b-print.pdf`, `exam-b-answers.pdf`
   - etc.

## File Naming Convention

- Valid variant files: `PREFIX-[a-z].tex`
- For example: `exam-a.tex`, `exam-b.tex`, `test-x.tex`

## Troubleshooting

- If you see `ERROR: No version files found for base 'FILE'.`, ensure you passed the correct prefix (not including the variant letter).
- Make sure `latexmk` are available in your shell.
- Use the `-shell-escape` flag for source files using the `minted` package.

## License

The LaTeX Project Public License (LPPL Version 1.3c)

## Author & Credits

Script by[João Lourenço](https://docentes.fct.unl.pt/joao-lourenco).

---

For further customization or help, consult the comments in the script source.
