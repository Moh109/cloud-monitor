# What changed, and why

Your original resume was already above average for a UH junior: correct format,
one page, real projects, no filler. This is a sharpening pass, not a rescue.

---

## The accuracy rule

**Every claim on this resume traces to one of two sources:** something your
original resume already said, or something verified by reading the CloudGuard
code in this repo. Nothing is inferred, rounded up, or filled in from what a
project of this shape *usually* involves.

An earlier draft broke that rule in three places. All three are fixed, but
they're recorded here because they're the exact failure mode to watch for if you
ever hand your resume to a tool that "improves" it:

| Claim that was wrong | What the code actually shows |
|---|---|
| "22 tests and a **Docker build** run on every push" | `.github/workflows/ci.yml` has two jobs — `test` (pytest) and `posture-scan`. There's a `Dockerfile` in the repo, but **CI never builds it.** |
| "17 controls… **each mapped** to CIS, MITRE ATT&CK, and NIST 800-53" | Only **11 of 17** map to all three. Six (S3.2, S3.5, IAM.1, IAM.4, CT.2, CT.4) carry no ATT&CK technique. Now reads "with findings mapped to CIS Benchmark, MITRE ATT&CK, and NIST 800-53 controls" — true of the check library, not overclaimed per-check. |
| "selecting the top performer by **backtested accuracy** rather than training fit" (Invesight) | You never said this. It was invented — plausible for the project, but not yours to defend in an interview. Reverted to your original wording. |

Also removed: `scikit-learn` from Skills (you never listed it), `Elasticsearch`
from Databases (its only backing project is no longer on the page), `TypeScript`
from the StudyWise stack line (you listed it under Skills, not that project), and
the `~1,900 lines of Python` figure and repo link from CloudGuard at your request.

Verified and kept: **17 checks**, **22 tests**, **4 services** (S3, IAM, EC2,
CloudTrail), **3 reporters** (console, JSON, HTML), the decorator registry, the
severity-weighted 0–100 score and letter grade, and the `--fail-on` CI gate.

---

## 1. CloudGuard is on the resume now — as the lead project

It wasn't before, and it's your strongest work. A check library with a plug-in
registry, a 22-test suite, a CI pipeline, three output formats and a real
scoring model is not a class project. It also carries the vocabulary that
Houston energy and federal recruiters screen on: AWS, CI/CD, CIS, MITRE ATT&CK,
NIST. And it turns your AttackIQ certification from a line item into evidence.

## 2. Four projects, not five

| Project | The screen it covers |
|---|---|
| CloudGuard | Cloud, DevOps, CI/CD, security, testing rigor |
| StudyWise | Full-stack web, AI/RAG, API design |
| Invesight | Data, ML, Python |
| MedLog | C++, OOP, fundamentals |

**MedLog stayed** despite being a freshman class project — it's the only C++
artifact you have, and a general resume can't afford a hole where systems and
OOP should be. Two bullets is enough to pass that screen.

**Detection-as-Code came off.** It overlaps CloudGuard on CI, Docker and security
framing, so it spent four lines restating a point CloudGuard already made better.
Swap it back in for security-specific applications — see `variant-security.md`.

## 3. Added a Cloud & Infrastructure skills line

Docker, GitHub Actions and Linux were buried under "Developer Tools," and AWS
never appeared at all. Recruiter scans and ATS filters look for a cloud line.

## 4. Smaller fixes

- **Added "Houston, TX"** to the header. Local candidates are cheaper to hire and
  likelier to accept — make it visible in the first line.
- **Cut the Fusion 360 certification.** CAD is noise on a CS resume.
- **Resolved the placeholders.** Code Coogs is a 4-person team. The StudyWise user
  count was dropped entirely rather than guessed.
- **Trimmed the coursework line** to one row.

---

## Compiling

```bash
pdflatex resume-general.tex
```

Or paste into a blank Overleaf project, compiler set to **pdfLaTeX**. Replace
`PHONE-REDACTED` with your number first — it's redacted here because this repo is
public.

**The layout is tuned to the millimetre.** `\textheight`, `\topmargin` and the
negative `\vspace` in `\resumeItem` were set so the page lands at one page with
~0.44in top and ~0.41in bottom margins. Add a bullet and something silently
pushes to page two. Check the page count *and look at the rendered page* before
printing — an earlier draft reported one page while clipping the Certifications
line clean off the bottom edge.

**Then get human eyes on it.** UH Career Services does resume drop-ins. Ten
minutes with someone who reads 200 of these a week will catch something neither
of us can see from here.
