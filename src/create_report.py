
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak
)

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
FIGURES_DIR = BASE_DIR / "figures"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = REPORT_DIR / "report.pdf"

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "CustomTitle",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=20,
    spaceAfter=20
)

heading_style = styles["Heading2"]
body_style = styles["BodyText"]

doc = SimpleDocTemplate(
    str(OUTPUT_FILE),
    pagesize=A4,
    rightMargin=2 * cm,
    leftMargin=2 * cm,
    topMargin=2 * cm,
    bottomMargin=2 * cm
)

story = []

story.append(Paragraph(
    "SIS-2 Data Engineering Project",
    title_style
))

story.append(Paragraph(
    "FDA Adverse Event Data Pipeline",
    ParagraphStyle(
        "Subtitle",
        parent=body_style,
        alignment=TA_CENTER,
        fontSize=13
    )
))

story.append(Spacer(1, 25))

story.append(Paragraph("1. Project Overview", heading_style))
story.append(Paragraph(
    "This project implements a complete data engineering pipeline "
    "for collecting, streaming, validating, cleaning, storing, and "
    "analyzing adverse drug event reports from the OpenFDA API.",
    body_style
))

story.append(Spacer(1, 12))

story.append(Paragraph("2. Technologies", heading_style))
story.append(Paragraph(
    "Python, OpenFDA API, Apache Kafka, Docker Compose, Pandera, "
    "Pandas, NumPy, SQLite, and Matplotlib.",
    body_style
))

story.append(Spacer(1, 12))

story.append(Paragraph("3. Validation Results", heading_style))

validation_data = [
    ["Metric", "Records"],
    ["Original records", "200"],
    ["Artificial test records", "3"],
    ["Original valid records", "195"],
    ["Original invalid records", "5"],
    ["Artificial invalid records detected", "3"],
    ["Total invalid records", "8"]
]

table = Table(validation_data, colWidths=[11 * cm, 4 * cm])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263B59")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("PADDING", (0, 0), (-1, -1), 7),
]))

story.append(table)

story.append(Spacer(1, 15))

story.append(Paragraph("4. Data Cleaning Results", heading_style))
story.append(Paragraph(
    "The cleaning stage processed 195 valid records. "
    "No duplicate records were removed. The final cleaned dataset "
    "contains 195 records. Age values were converted into years, "
    "text fields were normalized, and additional analytical columns "
    "were created.",
    body_style
))

story.append(Spacer(1, 15))

story.append(Paragraph("5. Database Loading", heading_style))
story.append(Paragraph(
    "Cleaned records were loaded into SQLite. The fda_reports table "
    "uses safetyreportid as its primary key. INSERT OR IGNORE "
    "prevents duplicate records during repeated loading.",
    body_style
))

story.append(PageBreak())

story.append(Paragraph("6. Data Analysis", heading_style))
story.append(Paragraph(
    "The analysis was performed on 195 cleaned records.",
    body_style
))

story.append(Spacer(1, 10))

analysis_data = [
    ["Classification", "Count", "Percentage"],
    ["Serious", "139", "71.28%"],
    ["Non-serious", "56", "28.72%"]
]

table = Table(analysis_data, colWidths=[6 * cm, 4 * cm, 4 * cm])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263B59")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("PADDING", (0, 0), (-1, -1), 7),
]))

story.append(table)

charts = [
    ("Reports by Country", "reports_by_country.png"),
    ("Reports Over Time", "reports_over_time.png"),
    ("Serious vs Non-Serious Reports", "serious_vs_non_serious.png")
]

for chart_title, filename in charts:
    chart_path = FIGURES_DIR / filename

    story.append(Spacer(1, 15))
    story.append(Paragraph(chart_title, heading_style))

    if chart_path.exists():
        img = Image(str(chart_path))
        img._restrictSize(16 * cm, 9 * cm)
        story.append(img)
    else:
        story.append(Paragraph(
            f"Chart not found: {filename}. Run analysis.py first.",
            body_style
        ))

story.append(Spacer(1, 20))

story.append(Paragraph("7. Conclusion", heading_style))
story.append(Paragraph(
    "The project demonstrates an end-to-end data engineering "
    "workflow. It integrates API collection, Kafka streaming, "
    "data validation, data transformation, SQLite storage, "
    "and analytical visualization.",
    body_style
))

doc.build(story)

print(f"PDF report created: {OUTPUT_FILE}")
