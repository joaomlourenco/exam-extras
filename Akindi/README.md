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
- LaTeX distribution (with `exam` class);
- `latexmk` installed and available in your PATH;
- Answer key template: `exam-key.tex` in the script directory.


## Usage

### 1. Generate Answer Key PDFs

`python exam-key-pdf.py PREFIX`

- Calls the `exam-extract-key.py PREFIX` script to extract the test/exam KEY and saves the output to `PREFIX.keys`;
- Reads the extracted answers for text/exam from the file `PREFIX.keys`;
- Fills `exam-key.tex` template and compiles PDFs for each version (e.g., `PREFIX-key-a.pdf`).

### 2. Extract Answer Keys (optional)

`python exam-extract-key.py PREFIX`

- Scans current folder for files like `PREFIX-a.tex` and `PREFIX-a-questions.tex` for multiple choice question;
- Outputs tab-separated answer codes for each version (with `-o outfile` writes to `outfile` instead of terminal).


## Output

- Tab-separated text file: `PREFIX.keys`;
- PDF answer keys: `PREFIX-key-a.pdf`, `PREFIX-key-b.pdf`, etc.


## File Patterns Supported

- `PREFIX-a-questions.tex`, `PREFIX-b-questions.tex`;
- Fallback: `PREFIX-a.tex`, `PREFIX-b.tex`.


## Tips and Troubleshooting

- Ensure all required packages are installed (`exam`, `latexmk`);
- Run scripts from the directory containing both Python scripts and your LaTeX sources;
- For PDF errors, check if LaTeX template compiles independently.

## License

The LaTeX Project Public License (LPPL Version 1.3c).

## Authors & Acknowledgments

Scripts by [João Lourenço](https://docentes.fct.unl.pt/joao-lourenco), with the help of ChatGPT.

---

For advanced customization, consult each script’s source for comments and options.
