from io import BytesIO
from xml.sax.saxutils import escape

from django.http import FileResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from rest_framework import serializers
from rest_framework.views import APIView

NAVY = colors.HexColor("#102643")
BLUE = colors.HexColor("#2457A6")
INK = colors.HexColor("#172942")
MUTED = colors.HexColor("#50627A")


class AssistantReportSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    title = serializers.CharField(max_length=120)
    summary = serializers.CharField(max_length=4000)
    columns = serializers.ListField(child=serializers.CharField(max_length=48), max_length=7)
    rows = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField(max_length=300, allow_blank=True), max_length=7),
        max_length=500,
    )

    def validate(self, attrs):
        if any(len(row) != len(attrs["columns"]) for row in attrs["rows"]):
            raise serializers.ValidationError("Every row must match the report columns.")
        return attrs


def report_pdf(report):
    output = BytesIO()
    page_size = landscape(A4)
    document = SimpleDocTemplate(
        output, pagesize=page_size, title=report["title"], author="SMS Motor Driving School",
        leftMargin=36, rightMargin=36, topMargin=64, bottomMargin=45,
    )
    styles = {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=NAVY),
        "question": ParagraphStyle("question", fontName="Helvetica-Bold", fontSize=11, leading=16, textColor=BLUE),
        "body": ParagraphStyle("body", fontSize=10, leading=15, textColor=INK),
        "cell": ParagraphStyle("cell", fontSize=9, leading=13, textColor=INK),
        "header": ParagraphStyle("header", fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=colors.white),
    }

    def paragraph(value, style):
        value = value.replace("₹", "INR ").replace("–", "-").replace("—", "-")
        value = "".join(char for char in value if char.isprintable() or char in "\n\t")
        return Paragraph(escape(value).replace("\n", "<br/>"), styles[style])

    def page(canvas, doc):
        width, height = page_size
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - 45, width, 45, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(36, height - 28, "SMS MOTOR DRIVING SCHOOL")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 36, height - 28, "STAFF ASSISTANT")
        canvas.setStrokeColor(colors.HexColor("#DDE5EF"))
        canvas.line(36, 32, width - 36, 32)
        canvas.setFillColor(MUTED)
        canvas.drawString(36, 19, "Generated " + timezone.localdate().strftime("%d %b %Y") + " | Staff use")
        canvas.drawRightString(width - 36, 19, f"Page {doc.page}")

    content = [
        paragraph(report["title"], "title"), Spacer(1, 10),
        paragraph("Question: " + report["question"], "question"), Spacer(1, 7),
        paragraph(report["summary"], "body"),
    ]
    if report["columns"]:
        content.append(Spacer(1, 15))
        cells = [[paragraph(label, "header") for label in report["columns"]]]
        cells.extend([paragraph(value, "cell") for value in row] for row in report["rows"])
        table = LongTable(cells, colWidths=[document.width / len(report["columns"])] * len(report["columns"]), repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5FA")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -1), .35, colors.HexColor("#DDE5EF")),
        ]))
        content.append(table)
    document.build(content, onFirstPage=page, onLaterPages=page)
    output.seek(0)
    return output


class AssistantPdfAPIView(APIView):
    def post(self, request):
        serializer = AssistantReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = FileResponse(
            report_pdf(serializer.validated_data), as_attachment=True,
            filename="sms-assistant-report.pdf", content_type="application/pdf",
        )
        response["Cache-Control"] = "no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
