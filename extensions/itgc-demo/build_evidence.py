"""Generate and deterministically read one synthetic Korean text PDF. No OCR/LLM."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import re

import fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
PDF = ROOT / "퇴사자_계정_회수_확인서.pdf"


def main():
    pdfmetrics.registerFont(TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf"))
    doc = canvas.Canvas(str(PDF), pagesize=(595, 842), invariant=1)
    doc.setTitle("합성 퇴사자 계정 회수 확인서")
    doc.setFont("Malgun", 22)
    doc.drawString(48, 775, "퇴사자 계정 회수 확인서")
    doc.setFont("Malgun", 11)
    rows = [
        "합성 데이터 · 실제 직원 / 고객 / ERP 데이터 아님",
        "Employee ID: DEMO-EMP-001",
        "Account ID: DEMO-ACCOUNT-001",
        "퇴사 시각: 2026-10-01 09:00 KST",
        "회수 시각: 2026-10-01 21:00 KST",
        "계정 상태: 비활성",
        "작성 목적: IT 일반통제의 퇴사자 접근권한 회수 점검 실험",
        "본 문서는 텍스트형 PDF이며 OCR 또는 LLM 평가 자료가 아닙니다.",
        "허용시간 24시간은 데모 가정입니다. 법률 / 회사 규정이 아닙니다.",
    ]
    for i, row in enumerate(rows):
        doc.drawString(48, 715 - i * 35, row)
    doc.save()
    with fitz.open(PDF) as opened:
        extracted_text = "\n".join(page.get_text() for page in opened)
    definitions = {
        "employee_id": "Employee ID",
        "account_id": "Account ID",
        "departure_at": "퇴사 시각",
        "revocation_at": "회수 시각",
        "account_status": "계정 상태",
    }
    fields = {}
    for key, label in definitions.items():
        match = re.search(r"^" + re.escape(label) + r":\s*([^\n]+)$", extracted_text, re.M)
        if not match:
            raise ValueError(f"Missing exact field label: {label}")
        quote = match.group(0)
        assert quote in extracted_text
        fields[key] = {"label": label, "value": match.group(1).strip(), "quote": quote, "page": 1}
    stamp = lambda key: datetime.strptime(fields[key]["value"], "%Y-%m-%d %H:%M KST")
    delay = (stamp("revocation_at") - stamp("departure_at")).total_seconds() / 3600
    assert delay == 12 and fields["account_status"]["value"] == "비활성"
    result = {
        "scope": "synthetic_korean_text_pdf_deterministic_label_extraction",
        "source_file": PDF.name,
        "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "extraction": "PyMuPDF text layer + exact label regex + quoted text verification",
        "ocr_used": False,
        "llm_used": False,
        "fields": fields,
        "baseline": {"delayHours": delay, "limitHours": 24, "accountActive": False, "evidenceMissing": False},
        "text": extracted_text,
    }
    (ROOT / "extracted.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "source-data.js").write_text("window.ITGC_SOURCE = " + json.dumps(result, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    print(json.dumps({"pdf": str(PDF), "fields_verified": len(fields), "delay_hours": delay, "sha256": result["sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
