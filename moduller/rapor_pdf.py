from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.config import BASE_DIR

from .db import db_baglan
from .loglama import log_yaz


def _rapor_klasoru() -> Path:
    klasor = Path(BASE_DIR) / "rapor_ciktilari"
    klasor.mkdir(parents=True, exist_ok=True)
    return klasor


def _pdf_yaz(dosya: Path, baslik: str, kolonlar: list[str], satirlar: list[tuple]) -> str:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as hata:
        raise RuntimeError("PDF rapor için reportlab gerekli: pip install reportlab") from hata

    doc = SimpleDocTemplate(str(dosya), pagesize=landscape(A4), rightMargin=18, leftMargin=18, topMargin=18, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = [Paragraph(baslik, styles["Title"]), Paragraph(datetime.now().strftime("%d.%m.%Y %H:%M"), styles["Normal"]), Spacer(1, 12)]
    data = [kolonlar] + [["" if v is None else str(v) for v in row] for row in satirlar]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(table)
    doc.build(elements)
    log_yaz(f"PDF rapor oluşturuldu: {dosya.name}", "RAPOR")
    return str(dosya)


def cari_bakiye_pdf() -> str:
    dosya = _rapor_klasoru() / f"cari_bakiye_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    with db_baglan() as conn:
        rows = conn.execute("""
            SELECT c.ad,
                   printf('%.2f', COALESCE(SUM(CASE
                     WHEN h.tip IN ('BORÇ','BORC','SATIŞ','SATIS') THEN h.tutar
                     WHEN h.tip IN ('ALACAK','TAHSİLAT','TAHSILAT') THEN -h.tutar
                     ELSE 0 END), 0)) AS bakiye
            FROM cariler c LEFT JOIN hareketler h ON h.cari_id=c.id
            WHERE COALESCE(c.aktif,1)=1
            GROUP BY c.id, c.ad ORDER BY CAST(bakiye AS REAL) DESC, c.ad
        """).fetchall()
    return _pdf_yaz(dosya, "Cari Bakiye Raporu", ["Cari", "Bakiye"], rows)


def stok_pdf() -> str:
    dosya = _rapor_klasoru() / f"stok_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    with db_baglan() as conn:
        rows = conn.execute("""
            SELECT COALESCE(g.ad,''), u.ad, COALESCE(u.barkod,''), printf('%.2f', COALESCE(u.stok,0)), printf('%.2f', COALESCE(u.varsayilan_fiyat,0))
            FROM urunler u LEFT JOIN urun_gruplari g ON g.id=u.grup_id
            WHERE COALESCE(u.aktif,1)=1 ORDER BY g.ad, u.ad
        """).fetchall()
    return _pdf_yaz(dosya, "Stok Raporu", ["Grup", "Ürün", "Barkod", "Stok", "Fiyat"], rows)
