from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

pdf_filename = "ResolveIQ_Project_Overview.pdf"
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    rightMargin=45,
    leftMargin=45,
    topMargin=45,
    bottomMargin=45
)

styles = getSampleStyleSheet()

# Color definitions
PRIMARY = colors.HexColor("#0f172a")    # Slate 900
ACCENT = colors.HexColor("#0284c7")     # Sky 600
MUTED = colors.HexColor("#64748b")      # Slate 500
BORDER_COL = colors.HexColor("#cbd5e1") # Slate 300
BG_HEADER = colors.HexColor("#f1f5f9")  # Slate 100

# Custom Typography
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=20,
    leading=24,
    textColor=PRIMARY
)

subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica-Oblique',
    fontSize=10.5,
    leading=14,
    textColor=MUTED
)

h1_style = ParagraphStyle(
    'SectionH1',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=13,
    leading=17,
    textColor=PRIMARY,
    spaceBefore=10,
    spaceAfter=4
)

body_style = ParagraphStyle(
    'BodyTextCustom',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=13.5,
    textColor=PRIMARY
)

bullet_style = ParagraphStyle(
    'BulletCustom',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=13,
    textColor=PRIMARY,
    leftIndent=14
)

table_header_style = ParagraphStyle(
    'TableHeader',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=9,
    leading=12,
    textColor=PRIMARY
)

table_cell_style = ParagraphStyle(
    'TableCell',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.5,
    leading=11.5,
    textColor=PRIMARY
)

elements = []

# Title & Subtitle
elements.append(Paragraph("🚨 ResolveIQ: SRE Incident Response & Memory Agent", title_style))
elements.append(Paragraph("Autonomous Incident Memory Architecture & Operational Workflow", subtitle_style))
elements.append(Spacer(1, 8))
elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COL, spaceAfter=12))

# 1. Executive Summary
elements.append(Paragraph("1. Executive Summary", h1_style))
elements.append(Paragraph(
    "<b>ResolveIQ</b> is an autonomous Site Reliability Engineering (SRE) incident triage agent built to resolve recurring microservice downtime. While standard AI models operate statelessly and treat identical infrastructure failures as unprecedented events, ResolveIQ bridges live alerts with accumulated organizational memory. Powered by <b>Hindsight persistent memory</b> and <b>Groq LLM inference</b>, ResolveIQ recalls past post-mortems, verified root causes, and runbook remediations across deployment cycles. When a recurring error occurs, it eliminates lengthy investigation cycles by immediately prescribing proven resolutions.",
    body_style
))
elements.append(Spacer(1, 8))

# 2. System Architecture Table
elements.append(Paragraph("2. System Architecture & Technical Specifications", h1_style))
table_data = [
    [
        Paragraph("Component", table_header_style),
        Paragraph("Technology", table_header_style),
        Paragraph("Implementation Role", table_header_style)
    ],
    [
        Paragraph("<b>Memory Bank</b>", table_cell_style),
        Paragraph("Hindsight Cloud (Bank: <code>resolveiq</code>)", table_cell_style),
        Paragraph("Semantic vector retrieval of historical post-mortems (<code>recall</code>) and storage of validated operational fixes (<code>retain</code>).", table_cell_style)
    ],
    [
        Paragraph("<b>Reasoning Engine</b>", table_cell_style),
        Paragraph("Groq (Llama-3.3 / Qwen)", table_cell_style),
        Paragraph("Low-latency synthesis of incoming telemetry with recalled institutional memory.", table_cell_style)
    ],
    [
        Paragraph("<b>Operations Console</b>", table_cell_style),
        Paragraph("Streamlit", table_cell_style),
        Paragraph("Dual-pane interface for active incident investigation and real-time memory inspection.", table_cell_style)
    ],
    [
        Paragraph("<b>Data Schemas</b>", table_cell_style),
        Paragraph("JSON Pipelines", table_cell_style),
        Paragraph("Standardized structures for microservice symptoms, root causes, runbooks, and metadata.", table_cell_style)
    ]
]

arch_table = Table(table_data, colWidths=[110, 150, 260])
arch_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), BG_HEADER),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
elements.append(arch_table)
elements.append(Spacer(1, 10))

# 3. Closed-Loop Memory Lifecycle
elements.append(Paragraph("3. The Closed-Loop Memory Lifecycle", h1_style))
elements.append(Paragraph("• <b>Stage 1: Semantic Recall (Pre-Fix)</b> — On incoming alerts (e.g., HTTP 503 on auth-service), the agent queries the 'resolveiq' Hindsight bank, extracting related post-mortems and past successful interventions.", bullet_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("• <b>Stage 2: Contextual Triage</b> — The Groq LLM receives live error logs and retrieved memories. It bypasses generic troubleshooting, identifying past failure patterns (e.g., INC-102 ConfigMap key mismatch) and prescribing exact recovery steps.", bullet_style))
elements.append(Spacer(1, 4))
elements.append(Paragraph("• <b>Stage 3: Retain & Continuous Learning</b> — Once an engineer confirms the fix, ResolveIQ writes the post-mortem back into Hindsight with metadata tags, making it instantly retrievable for future outages.", bullet_style))
elements.append(Spacer(1, 10))

# 4. Official Project Links
elements.append(Paragraph("4. Project Repository & Documentation Links", h1_style))
elements.append(Paragraph("• <b>Official GitHub Repo:</b> https://github.com/praveen1098-tech/resolveIQ", bullet_style))
elements.append(Spacer(1, 2))
elements.append(Paragraph("• <b>ResolveIQ Architecture Guide:</b> https://github.com/praveen1098-tech/resolveIQ#readme", bullet_style))
elements.append(Spacer(1, 2))
elements.append(Paragraph("• <b>Hindsight Memory Console:</b> https://ui.hindsight.vectorize.io/banks/resolveiq", bullet_style))
elements.append(Spacer(1, 2))
elements.append(Paragraph("• <b>Hindsight GitHub:</b> https://github.com/vectorize-io/hindsight", bullet_style))
elements.append(Spacer(1, 2))
elements.append(Paragraph("• <b>Hindsight Documentation:</b> https://hindsight.vectorize.io/", bullet_style))
elements.append(Spacer(1, 2))
elements.append(Paragraph("• <b>Vectorize Agent Memory:</b> https://vectorize.io/what-is-agent-memory", bullet_style))

# Build Document
doc.build(elements)
print("✅ ResolveIQ_Project_Overview.pdf successfully created!")
