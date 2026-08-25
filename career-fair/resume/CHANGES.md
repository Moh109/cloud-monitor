# What changed in the resume, and why

Your original resume was already above average for a UH junior: correct format,
one page, real projects, no fluff. The rewrite is not a rescue job — it's a
sharpening pass aimed at one specific audience: **Houston energy, enterprise, and
government recruiters hiring Summer 2027 CS interns.**

---

## 1. Added CloudGuard as the lead project — the single biggest upgrade

Your `Moh109/cloud-monitor` repo is not on your resume. It should be the first
thing on it.

Concretely, it is ~1,900 lines of Python, 22 passing tests, a GitHub Actions CI
pipeline, a Dockerfile, 17 security checks across 4 AWS services, three output
formats including an HTML dashboard, and a mock-AWS offline demo so anyone can
reproduce a full scan in one command. That is not a class project. That is a
small product.

Why it matters at *this* fair specifically:

- **AWS** is the keyword every energy digital org filters resumes on.
- **CI/CD + Docker** is what "we need people who can automate things" means.
- **CIS / MITRE ATT&CK / NIST 800-53** is the exact vocabulary of Exxon, Chevron
  and CenterPoint security teams — and of the FBI cyber track.
- It pairs with your AttackIQ MITRE ATT&CK certification, so the cert stops
  looking like a line item and starts looking like evidence.

Almost every student at that fair will describe a class project. You can describe
a tool with a test suite. Lead with it every single time.

## 2. Cut MedLog and the Fusion 360 certification

Five projects on one page means none of them get read. MedLog (C++ OOP, one month,
spring of freshman year) is the weakest of the five now that CloudGuard is on
there, and Autodesk Fusion 360 is CAD — irrelevant noise on a CS resume.

**Keep the C++ signal** through the Languages line and through NOV/SLB
conversations verbally. If you're standing in front of NOV or SLB and they start
talking about embedded or simulation work, that's the moment to say "I also built
a C++ inventory system on an inheritance hierarchy with file-based persistence" —
it doesn't need a resume slot to be useful. See `variant-security.md` for the
swap table if you want a C++-forward printed version.

## 3. Rewrote the IT Technician bullets out of job-description voice

Your originals described the *duties of the role*, not what *you* did with it:

> "Diagnose and resolve hardware, operating system, and network faults across
> Windows 10/11 and Chrome OS endpoints, isolating root cause through systematic
> elimination before escalating"

That sentence would be true of anyone holding that badge. The rewrite leads with
ownership and scale ("Own classroom technology across 50+ rooms"), names the
outcome, and — critically — reframes your cable-management bullet from a task
into a **diagnosis**: you noticed repeat tickets shared a physical root cause and
fixed the cause instead of the symptom. That's engineering judgment, and it's the
most interesting thing in that job. It was buried at the bottom as a throwaway.

## 4. Added a "Cloud & Infrastructure" skills line

Your original skills section buried Docker, GitHub Actions, and Linux inside
"Developer Tools," and never said AWS at all. Recruiter keyword scans and ATS
filters look for a cloud line. Now there is one, and it names actual AWS services
rather than just "AWS."

## 5. Quantified with numbers you can actually defend

Every number now on the resume is one I pulled from your real code or your
existing resume: 50+ rooms, 17 checks, 22 tests, ~1,900 lines, 4 AWS services,
3 frameworks, 7 ML models, 20+ indicators.

**Two `[[N]]` placeholders remain.** Fill them before you print:

| Placeholder | Where | What to put |
|---|---|---|
| `[[N]] active users` | StudyWise | Real usage number. If it's under ~20 or you don't track it, **delete the phrase** — don't invent one. |
| `[[N]]-person` | Code Coogs | How many people you actually lead. |

Rule for both: if a recruiter asks "how did you measure that?" and you don't have
an answer, the number is a liability, not an asset. Delete rather than guess.

## 6. Smaller fixes

- **Added "Houston, TX" to the header.** Every company on this list is local or
  Houston-headquartered. Local candidates cost less to hire and are less likely
  to decline. Make it obvious in the first line.
- **Made the CloudGuard repo link inline on the project.** A recruiter who wants
  to look shouldn't have to go find your profile and guess which repo you meant.
- **Fixed weak verbs.** "Developed a stock analysis platform" → "Trained and
  benchmarked 7 ML models... selecting the top performer by backtested accuracy."
  The second version tells me you understand overfitting. The first tells me you
  used Flask.
- **Removed the StudyWise duplication.** It appeared in both Projects and
  Leadership saying nearly the same thing. Now Projects covers *what it is* and
  Leadership covers *how you ran the team* — no overlap.
- **Kept present participles ("Building", "Containerizing") only on
  Detection-as-Code**, because it genuinely is in progress and the honest tense
  is the right one there.

---

## Compiling

No LaTeX in this environment, so the PDF isn't built. Fastest path:

1. Go to [overleaf.com](https://overleaf.com) → New Project → Blank Project.
2. Paste `resume-general.tex` in.
3. Set the compiler to **pdfLaTeX** (Menu → Compiler).
4. Fill the `[[N]]` placeholders and restore your phone number — it's redacted in
   this file because this repo is public and phone numbers in public git history
   get scraped. Put it back in the local copy you compile.
5. Compile, export PDF, name it `Muhammad_Shaikh_Resume.pdf`.

**Then get human eyes on it.** UH Career Services does resume drop-ins — go once
before September 7th. Ten minutes with someone who reads 200 of these a week will
catch something I can't see from here.

---

# Final decisions (general-purpose version)

The goal shifted to one resume that works for **any** software or internship
position, rather than a fair-targeted pair. What that changed:

**Four projects, not five.** CloudGuard, StudyWise, Invesight, MedLog. The
selection is deliberate — each one covers a different screen:

| Project | Covers |
|---|---|
| CloudGuard | Cloud, DevOps, CI/CD, security, testing rigor |
| StudyWise | Full-stack web, AI/RAG, API design |
| Invesight | Data, ML, Python |
| MedLog | C++, OOP, systems fundamentals |

**MedLog came back in.** It's a freshman class project and it's the weakest of
the five on its own merits — but it's the only C++ artifact you have, and a
general-purpose resume can't afford a hole where systems and OOP should be.
Plenty of employers (SLB, NOV, anything embedded or quant-adjacent) screen for
C++ before they read anything else. Two bullets is enough to pass that screen.

**Detection-as-Code came off.** It overlaps CloudGuard heavily — same CI, same
Docker, same security framing — so on a general resume it spends four lines
saying something CloudGuard already said better. It's also still in progress,
and "Building…" reads weaker than a finished project. Swap it back in for
security-specific applications; see `variant-security.md`.

**Placeholders resolved.** Code Coogs is a 4-person team. The StudyWise user
count came out entirely rather than carrying a number that couldn't be defended.

**Prose tightened throughout** to fit one page without shrinking the font —
roughly a dozen bullets lost their filler words. That was a quality win
independent of the space: "auditing accounts against 17 controls" is better than
"that audits an account against 17 security controls" regardless of page count.

## One loose thread

**Elasticsearch** is still on the Databases line, but the only project that used
it (Detection-as-Code) is no longer on the page. It's honest — you are genuinely
building with it — so it can stay. Just be ready for "where did you use
Elasticsearch?" and have the Detection-as-Code answer loaded. If you'd rather not
field that question, delete the word.
