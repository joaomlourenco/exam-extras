# exam-extras.sty

The `exam-extras.sty` package is a comprehensive LaTeX style file designed to enhance the functionality of the `exam` document class for creating multiple-choice exams and assessments. Below is a detailed listing of its key functionalities, organized by category.

The package includes scripts for automatic processing multiple versions of the same test/exam, and automatic key generation to submit to [Akindi](https://akindi.com).

This package is particularly well-suited for **computer science and technical exams** where code snippets, boolean logic, and precise formatting are essential. Its modular design allows instructors to adopt individual features without requiring wholesale changes to existing exam templates.


***

## Summary

The `exam-extras.sty` package is a **feature-rich extension** for the LaTeX `exam` class, offering:

1. **Enhanced visual design** with circled choice labels and horizontal separators;
2. **Flexible choice layouts** supporting both single- and multi-column formats;
3. **Robust question tracking** with persistent counters across compilations;
4. **Answer key enhancements** including colored correct answers and Bloom's taxonomy annotations;
5. **Structural tools** for organizing exams into parts with continuous numbering;
6. **Code listing support** with syntax highlighting via `minted`;
7. **Side-by-side layouts** for questions with accompanying visuals; and
8. **Multilingual boBuilolean keywords** for true/false questions.

Find detailed information below…

***

## 1. **Package Dependencies and Initial Setup**

The package loads several essential LaTeX packages to provide its extended functionality:

- **`tcolorbox[most]`**: Enables colored boxes for code listings and visual elements;
- **`multicol`**: Supports multi-column layouts for choices;
- **`enumitem[inline,shortlabels]`**: Provides customizable enumeration with inline and short label options;
- **`tikz`**: Used for drawing circled choice labels.

These dependencies establish the foundation for the visual and structural enhancements throughout the package.

## 2. **Choice Environment Customization**

### Circled Choice Labels

The package redefines how choice labels appear by encircling them with TikZ graphics:

```latex
\newcommand\encircle{%
\tikz[baseline=(X.base)]
\node (X) [draw, shape=circle, inner sep=0] {\strut #1};}
\renewcommand\choicelabel{\encircle{\textsf{\thechoice}}}
```

This creates **visually distinctive circled labels** (e.g., ①, ②, ③) in sans-serif font, improving readability and aesthetics.

<!--
### Indentation Control

The package prevents unwanted indentation of choices by setting a consistent left margin:

```latex
\def\choiceshook{\setlength{\leftmargin}{2em}}
```
-->

### Multi-Column vs. Single-Column Choices

The redefined `choices` environment supports **optional multi-column layouts**:

- **Without argument**: Displays choices in a single column;
- **With `[N]` argument**: Arranges choices in `N` columns using `multicols` with ragged-right alignment.

```latex
\renewenvironment{choices}[]{%
  \stepcounter{exam@numquestionsmcq}
  \multicolsfalse
  \ifx\relax#1\relax\else
    \multicolstrue
    \begin{multicols}{#1}\raggedright
  \fi
  \oldchoices
}{%
  \endoldchoices
  \ifmulticols
    \end{multicols}
  \fi
}
```

This provides flexibility for formatting questions with short choices (multi-column) vs. long explanatory choices (single-column).

## 3. **Question Counting and Tracking**

### Custom Counters

The package defines macros to access question counts safely:

- **`\mynumquestions`**: Returns total number of questions, defaulting to 0 if undefined;
- **`\mynumquestionsmcq`**: Returns number of multiple-choice questions, defaulting to 1 if undefined;
- **`exam@numquestionsmcq` counter**: Tracks MCQ questions and increments with each `choices` environment.

### Persistent Count Storage

At the end of the document, the MCQ count is written to the `.aux` file for use in subsequent compilations:

```latex
\AtEndDocument{%
\immediate\write\@mainaux
{\string\gdef\string\exam@numquestionsmcq{\theexam@numquestionsmcq}}%
}
```

This enables features like "Question 5 of 20" displays.

## 4. **Visual Separators and Section Markers**

### Question Separators

The package introduces **horizontal rules** to visually separate questions:

```latex
\newcommand\myrule[1pt]{\makebox[0pt]{\raisebox{2.5ex}{\rule{3\textwidth}{#1}}}}
\renewcommand\questionlabel{\questionseparator\\\oldquestionlabel}
```

### Section Headers

The `\examnewsection[title]` command allows inserting **prominent section dividers** in answer keys:

```latex
\newcommand{\examnewsection}[]{%
  \@newsectiontrue
  \def\@newsectiontitle{\MakeUppercase{#1}}
}
```

When printing answers, a **thicker cyan rule** with the section title appears above the first question of each new section:

```latex
\newcommand{\questionseparator}[cyan!90!black]{{%
  \ifprintanswers%
    \if@newsection%
      \global\@newsectionfalse%
      \color{#1}%
      \myrule[2pt]%
      {\centering\makebox[0pt][l]{\raisebox{3.5ex}{\hspace*{-\leftmargin}\@newsectiontitle}}}%
    \else\myrule\fi
  \else\myrule\fi%
}}
```

This helps organize exams into thematic sections (e.g., "Part A: Theory", "Part B: Programming").

## 5. **Answer Key Formatting**

### Correct Answer Emphasis

The package highlights correct answers in red when printing answer keys:

```latex
\CorrectChoiceEmphasis{\color{red!80!black}}
```

### `\CHOICE` Alias

A convenient alias for marking correct choices:

```latex
\newcommand{\CHOICE}{\CorrectChoice}
```

This allows using `\CHOICE` instead of `\CorrectChoice` for brevity.

## 6. **Boolean Keywords for True/False Questions**

The package defines **pre-formatted boolean keywords** in multiple languages using the `\defcapb` macro:

```latex
\newcommand{\defcapb}[2][]{%
  \ifx\relax#1\relax
    \expandafter\newcommand\csname#2\endcsname{\textbf{#2}\xspace}%
  \else
    \expandafter\newcommand\csname#2\endcsname{\textbf{#1}\xspace}%
  \fi
}
```

**Available commands**:
- English: `\TRUE`, `\FALSE`, `\IS`, `\ISNOT`, `\DOESNOT`
- Portuguese: `\NAO`, `\SIM`, `\NAOE`, `\VERDADEIRA`, `\VERDADEIRO`, `\FALSA`, `\FALSO`

These ensure consistent, bold formatting of boolean values throughout the exam.

## 7. **Bloom's Taxonomy Annotation**

The `\BLOOM{level}` command (alias `\Bloom`) adds **blue, bold annotations** indicating Bloom's taxonomy levels when printing answers:

```latex
\newcommand{\BLOOM}{\ifprintanswers\textcolor{blue}{\textbf{[#1] }}\fi}
```

**Example usage**:
```latex
\question \BLOOM{Remember} What is the capital of France?
```

This appears as **[Remember]** in blue only in answer keys, helping instructors assess cognitive complexity.

## 8. **Exam Parts with Continuous Numbering**

The `\exampart{title}` command creates **visually distinct part dividers** while maintaining continuous question numbering:

```latex
\newcommand{\exampart}{
  \end{questions}
  \setcounter{XXX}{\value{numquestions}}
  \begin{center}
  \LARGE
  \vspace{2ex}
  \begin{tabular}{p{\linewidth}}
  \toprule
  \centering Part #1\\
  \end{tabular}
  \end{center}
  \begin{questions}
  \setcounter{question}{\value{XXX}}
}
```

This temporarily closes the `questions` environment, displays a large centered title in a table, then reopens `questions` with the same question count.

## 9. **Code Listing Environment**

The package defines a **syntax-highlighted code blcok environment** using `tcolorbox` and `minted`:

```latex
\DeclareTCBListing{code}{ m O{} }{
  colback=white,
  colframe=black!70,
  listing only,
  listing remove caption=true,
  minted language=#1,
  listing engine=minted,
  minted style=material,
  minted options={
    linenos,
    breaklines,
    numbersep=3mm
  },
  width=\linewidth,
  breakable,
  enhanced jigsaw,
  #2
}
```

**Usage**:
```latex
\begin{codesnippet}{python}[title=Example]
def hello():
    print("Hello, World!")
\end{codesnippet}
```

Features include **line numbers, syntax highlighting** (Material style), **automatic line breaking**, and **breakable boxes** across pages.

## 10. **Split Question Layout**

The `splitquestion` environment creates **side-by-side layouts** for questions with figures or code alongside text:

```latex
\newenvironment{splitquestion}[2][4em]{%
  \par%
  \preto{\choices}{\medskip}%
  \newcommand{\nextpart}{%
    \end{minipage}\hfill%
    \begin{minipage}[t]{\sizeright}%
  }%
  \def\sizeleft{\dimexpr\fpeval{(1-#2)}\textwidth-#1\relax}%
  \def\sizeright{#2\textwidth}%
  \begin{minipage}[t]{\sizeleft}%
}{%
  \end{minipage}%
}
```

**Parameters**:
- `#1` (optional, default `4em`): Separation between columns;
- `#2` (mandatory): Fraction of `\textwidth` for the right column.

**Usage**:
```latex
\begin{splitquestion}{0.4}
  Question text and choices...
\nextpart
  \includegraphics{figure.png}
\end{splitquestion}
```

This creates a 60%-40% split with the question on the left and figure on the right.

<!--
## 11. **Utility Commands and Adjustments**

### Caption Spacing

Tighter spacing around captions for figures and tables:

```latex
\setlength{\abovecaptionskip}{2pt plus 0pt minus 2pt}
\setlength{\belowcaptionskip}{2pt plus 0pt minus 2pt}
```

### Unicode Character Support

Ensures the approximate symbol renders correctly:

```latex
\DeclareUnicodeCharacter{2248}{\ensuremath{\approx}}
```

### List Manipulation Helpers

The package defines `\appto` and `\preto` macros for **appending** and **prepending** content to existing macros:

```latex
\protected\long\def\appto#1#2{%
  \edef#1{%
    \unexpanded\expandafter{#1#2}%
  }%
}

\protected\long\def\preto#1#2{%
  \edef#1{%
    \unexpanded{#2}%
    \unexpanded\expandafter{#1}%
  }%
}
```

These are used internally to modify hooks and commands without overwriting them.

## 12. **Spacing Adjustments**

The package fine-tunes spacing in multi-column environments:

```latex
\premulticols=0pt       % No extra space before multicols
\multicolsep=\itemsep   % Match multicol separation to item separation
```

This ensures consistent vertical spacing between choices in both single- and multi-column layouts.
-->

## License

The LaTeX Project Public License (LPPL Version 1.3c)

## Authors & Acknowledgments

LaTeX extensions by [João Lourenço](https://docentes.fct.unl.pt/joao-lourenco).

Thanks to the author of the `exam` LaTeX class.
