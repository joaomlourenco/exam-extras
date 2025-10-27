# Exam Answer Key Generation Scripts

A toolkit for extracting and compiling answer keys for multi-version LaTeX exams.

## Overview

This toolkit streamlines two workflows:
- Extracting correct answers from LaTeX exam files across multiple versions.
- Generating PDF answer sheets using a custom LaTeX template.

It comprises:
- `exam-extract-key.py`: Extracts tabulated answer keys from versioned LaTeX exam files.
- `exam-key-pdf.py`: Automates PDF creation for answer keys (uses the extracted data).

## Prerequisites

- Python 3.x
- LaTeX distribution (with `exam` class)
- `latexmk` installed and available in your PATH
- Answer key template: `exam-key.tex` in the script directory

## Usage

### 1. Extract Answer Keys

`python exam-extract-key.py PREFIX`

- Scans files like `PREFIX-a-questions.tex`, etc.
- Outputs tab-separated answer codes for each version.

### 2. Generate Answer Key PDFs

`python exam-key-pdf.py PREFIX`

- Reads extracted answers
- Fills `exam-key.tex` template and compiles PDFs for each version (e.g., `PREFIX-key-a.pdf`).


## Output

- Tab-separated text file: `PREFIX.keys`
- PDF answer keys: `PREFIX-key-a.pdf`, `PREFIX-key-b.pdf`, etc.

## File Patterns Supported

- `PREFIX-a-questions.tex`, `PREFIX-b-questions.tex`
- `PREFIXa-questions.tex`, `PREFIXb-questions.tex`
- Fallback: `PREFIX-a.tex`, `PREFIX-b.tex`

## Template Requirements

- Template must define commands: `\FILE`, `\VERSION`, `\KEY`
- Example snippet:

```latex
\def\FILE{exam}
\def\VERSION{A}
\def\KEY{A,C,AC,D,*,…}
```


## Tips and Troubleshooting

- Ensure all required packages are installed (`exam`, `latexmk`)
- Run scripts from the directory containing both Python scripts and your LaTeX sources
- For PDF errors, check if LaTeX template compiles independently

## License

MIT or similar permissive license recommended

## Authors & Acknowledgments

Scripts by [Your Name], extended from exam class workflow.  
Thanks to contributors to the `exam` LaTeX class.

---

For advanced customization, consult each script’s source for comments and options.
