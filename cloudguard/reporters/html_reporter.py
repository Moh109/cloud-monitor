"""HTML reporter - a self-contained dashboard suitable for screenshots/sharing."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, select_autoescape

from ..models import ScanResult, Status
from ..scoring import compute_score

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CloudGuard Report</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         background: #0d1117; color: #e6edf3; }
  header { padding: 28px 32px; border-bottom: 1px solid #21262d;
           background: linear-gradient(135deg, #161b22, #0d1117); }
  header h1 { margin: 0 0 4px; font-size: 22px; letter-spacing: .3px; }
  header .meta { color: #8b949e; font-size: 13px; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 24px 32px 64px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
           gap: 16px; margin: 24px 0; }
  .card { background: #161b22; border: 1px solid #21262d; border-radius: 10px;
          padding: 18px 20px; }
  .card .label { color: #8b949e; font-size: 12px; text-transform: uppercase;
                 letter-spacing: .6px; }
  .card .value { font-size: 30px; font-weight: 700; margin-top: 6px; }
  .score-card { display: flex; align-items: center; gap: 20px; }
  .gauge { --v: {{ summary.score }}; width: 110px; height: 110px; border-radius: 50%;
           background: conic-gradient({{ gauge_color }} calc(var(--v) * 1%), #21262d 0);
           display: grid; place-items: center; flex: 0 0 auto; }
  .gauge .inner { width: 84px; height: 84px; border-radius: 50%; background: #161b22;
                  display: grid; place-items: center; }
  .gauge .num { font-size: 26px; font-weight: 800; }
  .grade { font-size: 40px; font-weight: 800; color: {{ gauge_color }}; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #21262d;
           vertical-align: top; }
  th { color: #8b949e; font-weight: 600; text-transform: uppercase; font-size: 11px;
       letter-spacing: .5px; }
  tr:hover td { background: #12171e; }
  .pill { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 11px;
          font-weight: 700; }
  .CRITICAL { background: #7d1a1a; color: #ffdada; }
  .HIGH { background: #8a3b0d; color: #ffe0c7; }
  .MEDIUM { background: #7a5c00; color: #fff3c4; }
  .LOW { background: #0d4a6b; color: #cdeeff; }
  .INFORMATIONAL { background: #30363d; color: #c9d1d9; }
  .fw { color: #8b949e; font-size: 11px; }
  .remediation { color: #adbac7; font-size: 12px; margin-top: 4px; }
  h2 { font-size: 16px; margin: 34px 0 4px; }
  .muted { color: #8b949e; font-size: 13px; }
  code { background: #21262d; padding: 1px 5px; border-radius: 4px; font-size: 12px; }
  footer { color: #8b949e; font-size: 12px; padding: 24px 32px; border-top: 1px solid #21262d; }
</style>
</head>
<body>
<header>
  <h1>&#128737;&#65039; CloudGuard &mdash; Cloud Security Posture Report</h1>
  <div class="meta">
    Provider <b>{{ result.provider|upper }}</b> &middot;
    Account <b>{{ result.account_id or "n/a" }}</b> &middot;
    Regions <b>{{ result.regions|join(", ") }}</b> &middot;
    Generated <b>{{ result.finished_at }}</b>
  </div>
</header>
<div class="wrap">

  <div class="cards">
    <div class="card score-card">
      <div class="gauge"><div class="inner"><span class="num">{{ summary.score }}</span></div></div>
      <div>
        <div class="label">Posture score</div>
        <div class="grade">{{ summary.grade }}</div>
      </div>
    </div>
    <div class="card"><div class="label">Controls passed</div>
      <div class="value" style="color:#3fb950">{{ summary.passed_controls }}</div></div>
    <div class="card"><div class="label">Controls failed</div>
      <div class="value" style="color:#f85149">{{ summary.failed_controls }}</div></div>
    <div class="card"><div class="label">Critical / High</div>
      <div class="value">{{ summary.failed_by_severity.CRITICAL }} / {{ summary.failed_by_severity.HIGH }}</div></div>
  </div>

  <h2>Failing controls ({{ failed|length }})</h2>
  <div class="muted">Sorted by severity. Each finding maps to the controls it violates.</div>
  {% if failed %}
  <table>
    <thead><tr>
      <th>Severity</th><th>Check</th><th>Service</th><th>Resource</th>
      <th>Finding &amp; remediation</th><th>Frameworks</th>
    </tr></thead>
    <tbody>
    {% for f in failed %}
      <tr>
        <td><span class="pill {{ f.severity.value }}">{{ f.severity.value }}</span></td>
        <td><code>{{ f.check_id }}</code></td>
        <td>{{ f.service }}</td>
        <td>{{ f.resource_id }}</td>
        <td>
          <div><b>{{ f.title }}</b></div>
          {% if f.evidence %}<div class="muted">{{ f.evidence }}</div>{% endif %}
          <div class="remediation">&#128295; {{ f.remediation }}</div>
        </td>
        <td class="fw">
          {% for name, ctrl in f.frameworks.items() %}{{ name }} {{ ctrl }}<br>{% endfor %}
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="muted">No failing controls. &#9989;</p>
  {% endif %}

  <h2>Passing controls ({{ passed|length }})</h2>
  <table>
    <thead><tr><th>Check</th><th>Service</th><th>Resource</th><th>Title</th></tr></thead>
    <tbody>
    {% for f in passed %}
      <tr><td><code>{{ f.check_id }}</code></td><td>{{ f.service }}</td>
          <td>{{ f.resource_id }}</td><td>{{ f.title }}</td></tr>
    {% endfor %}
    </tbody>
  </table>

</div>
<footer>Generated by CloudGuard {{ version }} &middot; Checks mapped to CIS AWS Foundations Benchmark, MITRE ATT&amp;CK, and NIST 800-53.</footer>
</body>
</html>
"""


def _gauge_color(score: int) -> str:
    if score >= 80:
        return "#3fb950"
    if score >= 60:
        return "#d29922"
    return "#f85149"


def render_html(result: ScanResult) -> str:
    from .. import __version__

    score = compute_score(result)
    env = Environment(autoescape=select_autoescape(["html", "xml"]))
    template = env.from_string(_TEMPLATE)

    failed = sorted(result.failed, key=lambda f: (f.severity.rank, f.check_id))
    passed = sorted(result.passed, key=lambda f: f.check_id)

    return template.render(
        result=result,
        summary=score,
        failed=failed,
        passed=passed,
        gauge_color=_gauge_color(score.score),
        version=__version__,
    )


def write_html(result: ScanResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(result), encoding="utf-8")
    return path
