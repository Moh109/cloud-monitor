# Print two versions, not one

Print **20 copies of the software/data resume** and **5 copies of a security
variant**. Clip the 5 to the back of your padfolio. It costs you one extra
Overleaf compile and it changes the conversation at four booths.

## Who gets the security variant

**FBI**, **LZ Technology**, **CenterPoint Energy** (grid/OT security), and
whichever of Exxon/Chevron says the word "cyber" first when you ask what their
intern teams work on.

## The swap

Take `resume-software.tex` and make exactly three changes:

**1. Move Detection-as-Code up**, directly under CloudGuard. Those two projects
tell one coherent story — *I write security controls as code, test them in CI, and
map them to ATT&CK* — and that story is worth more to a security team than
breadth is.

**2. Drop Invesight**, or cut it to one bullet. It's your least relevant project
for a security audience and you need the vertical space.

**3. Promote the certification.** Move it out of the skills block into its own
two-line section right under Education:

```latex
\section{Certifications}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Foundations of Operationalizing MITRE ATT\&CK v13}{Oct 2025}
      {AttackIQ Academy}{}
    \resumeSubheading
      {IT Specialist: Java}{May 2024}
      {Certiport}{}
  \resumeSubHeadingListEnd
```

For a federal or defense-adjacent reader, a named security certification above
the fold is a filter you pass rather than a nice-to-have.

## The C++ variant (optional, 2 copies)

If **NOV** or **SLB** starts talking embedded systems, drilling telemetry, or
simulation, C++ becomes the thing they care about. If you want a printed version
for that: restore MedLog in Detection-as-Code's slot, cut to two bullets, and move
`C/C++` to the front of the Languages line.

Honestly though — this one is optional. You can carry the C++ story verbally and
it lands just as well. Don't make yourself manage three stacks of paper at your
first fair if it's going to stress you out. Two is plenty.

## Before you print

Print on plain white 24lb paper. Skip the cream résumé stock and the fancy
texture — it reads as trying too hard, and half these recruiters are scanning your
sheet to PDF at the end of the day anyway.
