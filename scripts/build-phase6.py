"""Render the MIS 215 submission PDFs from the report and measured results."""

import argparse
import json
import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DOCS = Path(__file__).resolve().parents[1] / "docs"
WIDTH = A4[0] - 144
NAVY = colors.HexColor("#17324A")
GRAY = colors.HexColor("#4C5E6C")
PALE = colors.HexColor("#E8F0F4")
TEAL = colors.HexColor("#216A67")

BODY = ParagraphStyle("Body", fontName="Times-Roman", fontSize=11.5, leading=15.1, spaceAfter=10)
H1 = ParagraphStyle("Heading", fontName="Helvetica-Bold", fontSize=17, leading=22, spaceAfter=15, textColor=NAVY)
H2 = ParagraphStyle("Subheading", fontName="Helvetica-Bold", fontSize=11.5, leading=15, spaceAfter=7, textColor=NAVY)
TITLE = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=25, leading=30, spaceAfter=18)
CELL = ParagraphStyle("Cell", fontName="Times-Roman", fontSize=11, leading=12.5)
HEAD = ParagraphStyle("Column", fontName="Helvetica-Bold", fontSize=11, leading=12.5, textColor=NAVY)
REF = ParagraphStyle("Reference", parent=BODY, leftIndent=16, firstLineIndent=-16)

SOURCES = [
    ("Department of Education. (2023). <i>Revised guidelines on the utilization of the school maintenance and other operating expenses allocation</i> (DepEd Order No. 001, s. 2023).",
     "https://www.deped.gov.ph/wp-content/uploads/2023/01/DO_s2023_001.pdf"),
    ("Department of Education, Schools Division of Valenzuela. (n.d.). <i>ASSETS.</i>",
     "https://sites.google.com/deped.gov.ph/assetmanagement/s/assets"),
    ("Department of Education, Schools Division of Zambales. (n.d.). <i>Borrowing and returning of supplementary learning resources.</i>",
     "https://zambales.deped.gov.ph/citizens-charter/borrowing-and-returning-lr-from-lh.html"),
    ("Docker Inc. (n.d.). <i>Install Docker Engine on Ubuntu.</i>", "https://docs.docker.com/engine/install/ubuntu/"),
    ("Grafana Labs. (n.d.). <i>Metrics reference.</i> Grafana k6.",
     "https://grafana.com/docs/k6/latest/using-k6/metrics/reference/"),
    ("National Privacy Commission. (2016). <i>Implementing rules and regulations of the Data Privacy Act of 2012.</i>",
     "https://privacy.gov.ph/implementing-rules-regulations-data-privacy-act-2012/"),
    ("Penetrante, F. R. (n.d.). <i>MIS 215 client-server computing term project brief</i> [Course handout]. Bicol University.", ""),
    ("PostgreSQL Global Development Group. (n.d.). <i>PostgreSQL 17 documentation.</i>", "https://www.postgresql.org/docs/17/"),
    ("Republic Act No. 10173, Data Privacy Act of 2012 (2012) (Phil.).", "https://privacy.gov.ph/data-privacy-act/"),
]


def paragraph(value, style=BODY):
    value = escape(str(value)).replace(chr(96), "")
    return Paragraph(re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value), style)


def table(rows, shares=None):
    shares = shares or {2: (.32, .68), 3: (.25, .29, .46), 4: (.19, .25, .20, .36)}[len(rows[0])]
    grid = Table([[paragraph(cell, HEAD if index == 0 else CELL) for cell in row]
                  for index, row in enumerate(rows)], colWidths=[WIDTH * share for share in shares],
                 hAlign="LEFT", repeatRows=1)
    grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8F9")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [grid, Spacer(1, 12)]


def diagram(kind):
    def box(x, y, w, label, detail):
        d.add(Rect(x, y, w, 39, rx=5, ry=5, fillColor=PALE, strokeColor=TEAL, strokeWidth=0.7))
        d.add(String(x + w / 2, y + 23, label, textAnchor="middle", fontName="Helvetica-Bold", fontSize=10, fillColor=NAVY))
        d.add(String(x + w / 2, y + 9, detail, textAnchor="middle", fontSize=8.5, fillColor=GRAY))

    def edge(x, y, nx, ny):
        d.add(Line(x, y, nx, ny, strokeColor=TEAL, strokeWidth=1))
        tail = (nx - 5, ny - 3, nx - 5, ny + 3) if y == ny else (nx - 3, ny + 5, nx + 3, ny + 5)
        d.add(Polygon([nx, ny, *tail], fillColor=TEAL, strokeColor=None))

    d = Drawing(WIDTH, 160 if kind == "erd" else 111)
    if kind == "erd":
        for values in [(5, 108, 125, "Users", "borrower or custodian"),
                       (164, 108, 125, "Requests", "borrower and item FK"),
                       (322, 108, 125, "Loans", "unique request FK"),
                       (5, 35, 125, "Sessions", "user FK and expiry"),
                       (164, 35, 125, "Equipment items", "category FK"),
                       (322, 35, 125, "Categories", "unique name")]:
            box(*values)
        for coords in [(130,127,164,127), (289,127,322,127), (65,108,65,74),
                       (226,108,226,74), (289,54,322,54)]:
            edge(*coords)
        note = "Audit events reference an actor and record a typed entity ID."
    elif kind == "alternative":
        box(16, 45, 153, "Native client", "UI and client logic")
        box(284, 45, 153, "PostgreSQL", "Database and routines")
        edge(169, 64, 284, 64)
        d.add(String(226, 74, "SQL over TLS", textAnchor="middle", fontSize=9, fillColor=TEAL))
        note = "Conceptual alternative for a managed school LAN."
    else:
        box(1, 59, 124, "Presentation", "React and Nginx")
        box(164, 59, 124, "Application", "FastAPI • 8000")
        box(327, 59, 124, "Data", "PostgreSQL • 5432")
        edge(125, 78, 164, 78)
        edge(288, 78, 327, 78)
        d.add(String(5, 34, "Browser via HTTPS 8443 to gateway 443", fontSize=10, fillColor=GRAY))
        note = "Gateway to API uses HTTP/JSON. API to PostgreSQL uses its wire protocol."
    d.add(String(5, 14, note, fontSize=9.5, fillColor=GRAY))
    return [d, Spacer(1, 7)]


def summary_text(data):
    r1, r10, r50, w1, w10, w50 = data["runs"]
    highest = max((r50, w50), key=lambda row: row["p95_ms"])
    cpu = highest["cpu"]
    service = max(("api", "db", "edge"), key=lambda name: cpu[name]["mean"])
    tier = {"api": "application", "db": "data", "edge": "gateway"}[service]
    return {
        "FINDINGS": (
            f"At 50 users the catalog handled {r50['requests_per_second']:.2f} requests/s and submissions handled "
            f"{w50['requests_per_second']:.2f} requests/s. Read p95 was {r1['p95_ms']:.2f}, {r10['p95_ms']:.2f} and "
            f"{r50['p95_ms']:.2f} ms. Write p95 was {w1['p95_ms']:.2f}, {w10['p95_ms']:.2f} and {w50['p95_ms']:.2f} ms. "
            f"The largest observed error rate was {max(row['error_percent'] for row in data['runs']):.2f}%. "
            "Write tail latency had already increased noticeably at 10 users. The largest step for both workloads occurred between 10 and 50 users."
        ),
        "RESOURCE_FINDINGS": (
            f"The 50-user {highest['mode']} trial had the larger high-concurrency p95. Its samples averaged "
            f"{cpu['api']['mean']:.1f}% of one logical CPU for FastAPI, {cpu['db']['mean']:.1f}% for PostgreSQL and "
            f"{cpu['edge']['mean']:.1f}% for Nginx. PostgreSQL showed up to {highest['pg_max_lock_waits']} sampled lock "
            f"waits and {highest['pg_max_io_waits']} sampled I/O waits. The {tier} tier is the first profiling candidate "
            "because it carried the most observed container CPU work. Spot samples can miss short database waits. "
            "Causal attribution requires finer-grained profiling."
        ),
        "COMPARISON_DATA": (
            f"From 1 to 50 users the catalog p95 moved from {r1['p95_ms']:.2f} to {r50['p95_ms']:.2f} ms, and "
            f"request creation p95 moved from {w1['p95_ms']:.2f} to {w50['p95_ms']:.2f} ms. At 50 users PostgreSQL "
            f"confirmed {w50['confirmed_writes']:,} new requests with matching audit entries."
        ),
    }


def elements(marker, data, sections):
    if marker in {"architecture", "erd", "alternative"}:
        return diagram(marker)
    if marker == "results":
        return table([["Trial", "VUs", "Requests", "Req/s", "Mean ms", "p95 ms", "Errors"]] + [
            [row["mode"].title(), row["users"], row["requests"], f"{row['requests_per_second']:.2f}",
             f"{row['average_ms']:.2f}", f"{row['p95_ms']:.2f}", f"{row['error_percent']:.2f}%"]
            for row in data["runs"]], (.14, .08, .14, .13, .17, .17, .17))
    if marker == "environment":
        host = data["windows"]
        cpu = host["processor"]
        linux = data["wsl"]
        db = data["database"]
        limits = "The services share WSL resources without individual CPU or RAM caps."
        return table([["Component", "Measured configuration"],
                      ["Windows host", f"{cpu['Name'].strip()}, {cpu['NumberOfCores']} cores, {cpu['NumberOfLogicalProcessors']} logical CPUs, {host['memoryBytes'] / 2**30:.2f} GiB RAM"],
                      ["WSL2 Ubuntu", f"{linux['os']}, {linux['logical_cpus']} logical CPUs, {linux['memory_bytes'] / 2**30:.2f} GiB visible RAM"],
                      ["Containers", f"Engine {linux['engine']}, Compose 5.7.1. {limits}"],
                      ["Database", f"{db['borrowers']} synthetic borrowers, {db['assets']} assets, {db['database_bytes'] / 2**20:.2f} MiB starting size, {db['shared_buffers']} shared buffers"],
                      ["Test generator", "Grafana k6 OSS 1.8.2, co-located with the isolated application"]],
                     (.27, .73))
    if marker == "references":
        return [Paragraph(body + (f'<br/><link href="{url}" color="#216A67">{url}</link>' if url else ""), REF)
                for body, url in SOURCES]
    if marker == "licenses":
        lines = (DOCS / "STACK_LICENSES.md").read_text(encoding="utf-8").splitlines()
        selected = {"Component", "React / React DOM", "Vite", "FastAPI", "SQLAlchemy", "PostgreSQL", "Nginx",
                    "Docker Engine / CLI", "Compose plugin", "mkcert", "k6 OSS", "curl", "Argon2id implementation"}
        rows = []
        for line in lines:
            if not line.startswith("|") or line.split("|")[1].strip() not in selected:
                continue
            row = [re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", part.strip()) for part in line.strip("|").split("|")]
            row[1] = row[1].removeprefix(row[0] + ": ")
            rows.append(row)
        return table(rows, (.19, .27, .22, .32))
    if marker == "contents":
        entries = [(heading, str(page)) for page, heading in sections if page > 1
                   and heading.split()[0] not in {"Appendix"}]
        return table([["Section", "Page"], *entries], (.86, .14))
    raise ValueError(marker)


def pages(source):
    return [page.strip() for page in re.split(r"^===$", source.strip(), flags=re.MULTILINE)]


def footer(canvas, document, label):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#C4D0D6"))
    canvas.line(72, 51, A4[0] - 72, 51)
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(72, 37, label)
    canvas.drawRightString(A4[0] - 72, 37, str(document.page))
    canvas.restoreState()


def build(source, destination, data, replacements, label):
    for key, value in replacements.items():
        source = source.replace("{{" + key + "}}", value)
    assert "{{" not in source
    planned = pages(source)
    sections = [(n, page.splitlines()[0].removeprefix("# ")) for n, page in enumerate(planned, 1)]
    story = []
    for index, page in enumerate(planned):
        if index:
            story.append(PageBreak())
        lines = page.splitlines()
        story.append(paragraph(lines[0].removeprefix("# "), TITLE if "@cover" in lines else H1))
        block = []
        for line in lines[1:] + [""]:
            if line.startswith("|"):
                block.append([cell.strip() for cell in line.strip("|").split("|")])
                continue
            if block:
                story.extend(table(block))
                block.clear()
            if not line or line == "@cover":
                continue
            if line.startswith("@"):
                story.extend(elements(line[1:], data, sections))
            elif line.startswith("## "):
                story.append(paragraph(line[3:], H2))
            else:
                story.append(paragraph(line))
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, leftMargin=72, rightMargin=72,
                                 topMargin=72, bottomMargin=72, title=label, author=replacements["AUTHOR"])
    decorate = lambda canvas, doc: footer(canvas, doc, label)
    document.build(story, onFirstPage=decorate, onLaterPages=decorate)
    reader = PdfReader(stream)
    if len(reader.pages) != len(planned):
        first_lines = [page.extract_text().splitlines()[2][:75] for page in reader.pages
                       if len(page.extract_text().splitlines()) > 2]
        raise ValueError(f"{label} flowed into {len(reader.pages)} pages instead of {len(planned)}: {first_lines}")
    destination.write_bytes(stream.getvalue())
    print(f"{destination.name}: {len(planned)} pages")


def protocol_source():
    spec = json.loads((DOCS / "openapi.json").read_text(encoding="utf-8"))
    endpoints = [f"| {method.upper()} | {path} | {operation['summary']} |"
                 for path, operations in spec["paths"].items() for method, operation in operations.items()
                 if method in {"get", "post", "put", "patch", "delete"}]
    assert len(endpoints) == 25
    page = "# Protocol endpoint index\n| Method | Route | Operation |\n"
    description = """# EquipTrack REST protocol specification
MIS 215 Client-Server Computing • Option A • API version 0.2.0

The JSON contracts, parameters and schema references are supplied in openapi.json. The deployed service publishes the same contract at /api/openapi.json. Interactive documentation is available at /api/docs.

## Connection and identity
Use the configured HTTPS origin, for example https://localhost:8443, and the /api prefix. POST /api/auth/login takes an email and password. The 200 response sets an opaque Secure, HttpOnly and SameSite cookie and includes a CSRF token in JSON. Send the cookie on authenticated calls and send the exact Origin and X-CSRF-Token headers on authenticated mutations.

## Representative transaction
GET /api/equipment?limit=12 returns an equipment page. Supply both timestamp parameters when checking a period. For a borrowing request, POST /api/requests with equipment_id, borrow_at, due_at and purpose. ISO 8601 timestamps must include an offset. The response is 201 with an ID, equipment metadata and status pending.

The custodian applies a decision using PATCH, releases the item using POST, and records its return using PUT. The routes and field definitions are in OpenAPI. The response's X-Request-ID supports correlation. The returned resource ID identifies the corresponding PostgreSQL record.

## Errors and operations
The JSON error object supplies code, message and request_id. Typical statuses include 400 for malformed JSON, 401 for missing authentication, 403 for denied actions, 404 for inaccessible resources, 409 for state conflicts, 422 for validation, 429 for throttling and 503 for a database outage. The health endpoints distinguish process liveness from database readiness. Case-by-case results ship as phase4-curl-results.json and phase5-protocol-results.json.
"""
    return description + "\n===\n" + page + "\n".join(endpoints[:13]) + "\n===\n" + page + "\n".join(endpoints[13:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", required=True)
    parser.add_argument("--section")
    parser.add_argument("--term")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((DOCS / "phase6-performance.json").read_text(encoding="utf-8"))
    surname = re.sub(r"[^A-Za-z0-9-]", "", args.author.split()[-1])
    replacements = {**summary_text(data), "AUTHOR": args.author,
                    "COVER_DETAILS": " • ".join(part for part in (args.section, args.term) if part),
                    "STATUS": "Academic review copy"}
    report = (DOCS / "phase6-report.md").read_text(encoding="utf-8")
    proposal = (DOCS / "phase6-proposal.md").read_text(encoding="utf-8")
    body = pages(report)
    assert 20 <= sum(not page.startswith("# Appendix ") for page in body) - 1 <= 30
    assert sum(page.startswith("# 11 ") for page in body) == 4
    assert sum(page.startswith("# 12 ") for page in body) == 2
    privacy = "\n===\n".join(page.replace("# 12 ", "# ", 1) for page in body if page.startswith("# 12 "))
    evaluation = "\n===\n".join(page.replace("# 10 ", "# ", 1) for page in body if page.startswith("# 10 "))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, content, label in [
        ("FinalTechnicalReport", report, "EquipTrack Final Technical Report"),
        ("Proposal", proposal, "EquipTrack Term Project Proposal"),
        ("ProtocolSpecification", protocol_source(), "EquipTrack Protocol Specification"),
        ("DataPrivacyNote", privacy, "EquipTrack Data Privacy Compliance Note"),
        ("EvaluationResults", evaluation, "EquipTrack Evaluation Results"),
    ]:
        build(content, args.output / f"MIS215_TP_{surname}_{name}.pdf", data, replacements, label)


if __name__ == "__main__":
    main()
