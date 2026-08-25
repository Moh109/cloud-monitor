# Career fair prep — Sept 2026

Working files for the UH Natural Sciences & Mathematics + Computer Science
Career Fair. **Branch-only — do not merge to `main`.** This repo is a public
portfolio piece; career-fair prep sitting in its root is not the first thing you
want a recruiter to find when they open it.

| File | What it is |
|---|---|
| [`resume/resume-general.tex`](resume/resume-general.tex) | The resume. General-purpose, compiles to exactly one page with pdfLaTeX. |
| [`resume/resume-plaintext.txt`](resume/resume-plaintext.txt) | Extracted from the compiled PDF — paste into application forms |
| [`resume/CHANGES.md`](resume/CHANGES.md) | Every change and the reasoning behind it |
| [`resume/variant-security.md`](resume/variant-security.md) | Three swaps that make a security-targeted version |
| [`PLAYBOOK.md`](PLAYBOOK.md) | Employer tiers, 4-hour route, pitch scripts, follow-up templates, 3-week plan |

## Compiling

```bash
pdflatex resume-general.tex
```

Or paste into a blank Overleaf project with the compiler set to **pdfLaTeX**.

**Before you compile:** replace `PHONE-REDACTED` in the header with your real
number. It's redacted here because this repo is public and phone numbers in
public git history get scraped.

## Layout is tuned to the millimetre

The spacing values (`\textheight`, `\topmargin`, and the negative `\vspace` in
`\resumeItem`) were tuned so the content lands on one page with ~0.44in top and
~0.41in bottom margins. If you add a bullet, something will silently push onto a
second page — recompile and check the page count before you print.
