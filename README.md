# exam-extras.sty & scripts

The `exam-extras.sty` package is a comprehensive LaTeX style file designed to enhance the functionality of the `exam` document class for creating multiple-choice exams and assessments. Below is a detailed listing of its key functionalities, organized by category.

This package is particularly well-suited for **computer science and technical exams** where code snippets, boolean logic, and precise formatting are essential. Its modular design allows instructors to adopt individual features without requiring wholesale changes to existing exam templates.

Find detailed information aboth the `exam-extras.sty` package in the [`TeX` folder](TeX)

This repository also includes scripts for:
* handling multiple versions of the same test/exam, in files `PREFIX-<X>.tex` (where `<X>` is a single letter), automatizing the generation of printable and answers versions of each version (see the [Build folder](Build])); and
* automatized key extractions from `.tex` files and generation of KEY-PDFs to submit to [Akindi](https://akindi.com) (see the [Akindi folder](Akindi])).


***

## Summary

The `exam-extras.sty` package is a **feature-rich extension** for the LaTeX `exam` class, offering:

1. **Enhanced visual design** with circled choice labels and horizontal separators
2. **Flexible choice layouts** supporting both single- and multi-column formats
3. **Robust question tracking** with persistent counters across compilations
4. **Answer key enhancements** including colored correct answers and Bloom's taxonomy annotations
5. **Structural tools** for organizing exams into parts with continuous numbering
6. **Code listing support** with syntax highlighting via `minted`
7. **Side-by-side layouts** for questions with accompanying visuals
8. **Multilingual boBuilolean keywords** for true/false questions

Find detailed information in the [TeX folder](TeX)

***

## License

The LaTeX Project Public License (LPPL Version 1.3c)

## Authors & Acknowledgments

LaTeX extensions by [João Lourenço](https://docentes.fct.unl.pt/joao-lourenco).

Shell script by  [João Lourenço](https://docentes.fct.unl.pt/joao-lourenco).
Python scripts by [João Lourenço](https://docentes.fct.unl.pt/joao-lourenco), with the help of ChatGPT.

Thanks to the author of the `exam` LaTeX class.
