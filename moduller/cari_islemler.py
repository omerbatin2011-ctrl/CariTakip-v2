import os
import urllib.parse
import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from core.config import BASE_DIR, MAKS_TUTAR
from moduller.db import baglan
from moduller.erp_ek_moduller import audit_yaz
from moduller.erp_utils import telefon_temizle
from moduller.perf_utils import fill_table_fast
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import para_yaz


class CariIslemlerMixin:
    def cari_liste_yukle(self, tablo, arama=""):
        """Cari listesini hızlı/paginated yükler.

        V149: Büyük veride tüm carileri tek seferde çizmek yerine ilk 120 kayıt
        getirilir. Arama yapıldığında yine ilk 120 eşleşme gösterilir. Bu,
        menü geçişlerini ve arama yazmayı ciddi şekilde hızlandırır.
        """
        arama = (arama or "").strip()
        limit = int(getattr(self, "cari_liste_limit", 120) or 120)
        conn = baglan()
        cur = conn.cursor()

        where = "WHERE COALESCE(c.aktif,1)=1"
        params = []
        if arama:
            like = f"%{arama}%"
            where += " AND (c.ad LIKE ? OR c.telefon LIKE ? OR c.adres LIKE ? OR COALESCE(c.vergi_no,'') LIKE ?)"
            params.extend([like, like, like, like])

        cur.execute(f"""
            SELECT COUNT(*)
            FROM cariler c
            {where}
        """, params)
        toplam_kayit = int(cur.fetchone()[0] or 0)

        cur.execute(f"""
            SELECT
                c.id,
                c.ad,
                c.telefon,
                c.adres,
                COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END), 0) AS bakiye
            FROM cariler c
            LEFT JOIN hareketler h ON h.cari_id = c.id AND COALESCE(h.aktif,1)=1
            {where}
            GROUP BY c.id, c.ad, c.telefon, c.adres
            ORDER BY c.ad
            LIMIT ?
        """, params + [limit])
        veriler = cur.fetchall()
        conn.close()

        rows = []
        for satir, (cari_id, ad, telefon, adres, bakiye) in enumerate(veriler, start=1):
            rows.append((cari_id, satir, ad or "", telefon or "", adres or "", para_yaz(float(bakiye or 0))))

        fill_table_fast(tablo, rows, id_column=0)
        if hasattr(self, "_cari_liste_toplam_kayit"):
            self._cari_liste_toplam_kayit = toplam_kayit
        else:
            setattr(self, "_cari_liste_toplam_kayit", toplam_kayit)

    def cari_bilgisi_getir_id(self, cari_id):
        conn = baglan()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ad, telefon, adres, vergi_dairesi, vergi_no FROM cariler WHERE COALESCE(aktif,1)=1 AND id=?",
            (cari_id,)
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            QMessageBox.warning(self, "Hata", "Cari bulunamadı.")
            return None

        return {
            "id": int(row[0]),
            "ad": row[1] or "",
            "telefon": row[2] or "",
            "adres": row[3] or "",
            "vergi_dairesi": row[4] or "",
            "vergi_no": row[5] or ""
        }

    def cari_satir_sec(self, tablo, cari_id):
        for satir in range(tablo.rowCount()):
            item = tablo.item(satir, 0)
            if item is None:
                continue

            gizli_id = item.data(1000)

            if gizli_id is not None and int(gizli_id) == int(cari_id):
                tablo.selectRow(satir)
                tablo.setCurrentCell(satir, 1)
                return True

        return False

    def secili_cari_bilgisi(self, tablo):
        secili = tablo.currentRow()

        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cari seçin.")
            return None

        id_item = tablo.item(secili, 0)
        cari_id = id_item.data(1000) if id_item is not None else None

        if cari_id is None:
            QMessageBox.warning(self, "Hata", "Cari ID bulunamadı. Listeyi yenileyip tekrar deneyin.")
            return None

        cari_detay = self.cari_bilgisi_getir_id(int(cari_id))
        if cari_detay:
            return cari_detay

        return {
            "id": int(cari_id),
            "ad": tablo.item(secili, 1).text() if tablo.item(secili, 1) else "",
            "telefon": tablo.item(secili, 2).text() if tablo.columnCount() > 2 and tablo.item(secili, 2) else "",
            "adres": tablo.item(secili, 3).text() if tablo.columnCount() > 3 and tablo.item(secili, 3) else "",
            "vergi_dairesi": "",
            "vergi_no": ""
        }

    def yeni_cari(self, tablo=None):
        pencere = QDialog(self)
        pencere.setWindowTitle("Yeni Cari - Vergi Bilgileri")
        pencere.resize(480, 500)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Cari Adı / Firma Ünvanı"))
        txtAd = QLineEdit()
        layout.addWidget(txtAd)

        layout.addWidget(QLabel("Telefon"))
        txtTelefon = QLineEdit()
        txtTelefon.setPlaceholderText("Örn: 5467937000 / 05467937000 / +905467937000")
        layout.addWidget(txtTelefon)

        layout.addWidget(QLabel("Adres"))
        txtAdres = QTextEdit()
        layout.addWidget(txtAdres)

        layout.addWidget(QLabel("Vergi Dairesi"))
        txtVergiDairesi = QLineEdit()
        txtVergiDairesi.setPlaceholderText("Örn: Osmaniye")
        layout.addWidget(txtVergiDairesi)

        layout.addWidget(QLabel("Vergi No / T.C. No"))
        txtVergiNo = QLineEdit()
        txtVergiNo.setPlaceholderText("Örn: 1234567890")
        layout.addWidget(txtVergiNo)

        btnKaydet = QPushButton("Kaydet")
        layout.addWidget(btnKaydet)

        def kaydet():
            ad = txtAd.text().strip()
            telefon = self.telefon_temizle(txtTelefon.text().strip())
            adres = txtAdres.toPlainText().strip()
            vergi_dairesi = txtVergiDairesi.text().strip()
            vergi_no = txtVergiNo.text().strip()

            if ad == "":
                QMessageBox.warning(pencere, "Hata", "Ad Soyad boş olamaz.")
                return
            if not self.telefon_gecerli_mi(telefon):
                QMessageBox.warning(pencere, "Hata", "Telefon numarası Türkiye formatında olmalı. Örnek: 5467937000")
                return

            conn = baglan()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO cariler(ad, telefon, adres, vergi_dairesi, vergi_no) VALUES (?, ?, ?, ?, ?)",
                (ad, telefon, adres, vergi_dairesi, vergi_no)
            )
            yeni_id = cur.lastrowid
            conn.commit()
            conn.close()

            QMessageBox.information(pencere, "Başarılı", "Cari kaydedildi.")

            if tablo is not None:
                self.cari_liste_yukle(tablo)
                self.cari_satir_sec(tablo, yeni_id)

            self.ozet_yukle()
            pencere.yeni_cari_id = yeni_id
            pencere.accept()

        btnKaydet.clicked.connect(kaydet)

        pencere.yeni_cari_id = None
        pencere.setLayout(layout)
        pencere.exec()
        self.ozet_yukle()

        return getattr(pencere, "yeni_cari_id", None)

    def cari_duzenle(self, tablo):
        cari = self.secili_cari_bilgisi(tablo)
        if cari is None:
            return

        cari_detay = self.cari_bilgisi_getir_id(cari["id"])
        if cari_detay:
            cari = cari_detay

        pencere = QDialog(self)
        pencere.setWindowTitle(f"Cari Düzenle - {cari['ad']}")
        pencere.resize(480, 500)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Cari Adı / Firma Ünvanı"))
        txtAd = QLineEdit()
        txtAd.setText(cari["ad"])
        layout.addWidget(txtAd)

        layout.addWidget(QLabel("Telefon"))
        txtTelefon = QLineEdit()
        txtTelefon.setText(cari["telefon"])
        txtTelefon.setPlaceholderText("Örn: 5467937000 / 05467937000 / +905467937000")
        layout.addWidget(txtTelefon)

        layout.addWidget(QLabel("Adres"))
        txtAdres = QTextEdit()
        txtAdres.setPlainText(cari["adres"])
        layout.addWidget(txtAdres)

        layout.addWidget(QLabel("Vergi Dairesi"))
        txtVergiDairesi = QLineEdit()
        txtVergiDairesi.setText(cari.get("vergi_dairesi", ""))
        layout.addWidget(txtVergiDairesi)

        layout.addWidget(QLabel("Vergi No / T.C. No"))
        txtVergiNo = QLineEdit()
        txtVergiNo.setText(cari.get("vergi_no", ""))
        layout.addWidget(txtVergiNo)

        btnGuncelle = QPushButton("Güncelle")
        layout.addWidget(btnGuncelle)

        def guncelle():
            ad = txtAd.text().strip()
            telefon = self.telefon_temizle(txtTelefon.text().strip())
            adres = txtAdres.toPlainText().strip()
            vergi_dairesi = txtVergiDairesi.text().strip()
            vergi_no = txtVergiNo.text().strip()

            if ad == "":
                QMessageBox.warning(pencere, "Hata", "Ad Soyad boş olamaz.")
                return
            if not self.telefon_gecerli_mi(telefon):
                QMessageBox.warning(pencere, "Hata", "Telefon numarası Türkiye formatında olmalı. Örnek: 5467937000")
                return

            conn = baglan()
            cur = conn.cursor()
            cur.execute(
                "UPDATE cariler SET ad=?, telefon=?, adres=?, vergi_dairesi=?, vergi_no=? WHERE id=?",
                (ad, telefon, adres, vergi_dairesi, vergi_no, cari["id"])
            )
            conn.commit()
            conn.close()

            self.cari_liste_yukle(tablo)
            pencere.accept()

        btnGuncelle.clicked.connect(guncelle)

        pencere.setLayout(layout)
        pencere.exec()

    def cari_sil(self, tablo):
        cari = self.secili_cari_bilgisi(tablo)
        if cari is None:
            return

        cevap = QMessageBox.question(
            self,
            "Silme Onayı",
            f"{cari['ad']} adlı cariyi silmek istiyor musunuz?\nBu cariye ait hareketler de silinir."
        )

        if cevap != QMessageBox.Yes:
            return

        conn = baglan()
        cur = conn.cursor()
        cur.execute("UPDATE hareketler SET aktif=0 WHERE cari_id=?", (cari["id"],))
        cur.execute("UPDATE cariler SET aktif=0 WHERE id=?", (cari["id"],))
        audit_yaz("cari_pasife_alindi", "cariler", cari["id"], {"ad": cari["ad"]})
        conn.commit()
        conn.close()

        self.cari_liste_yukle(tablo)
        self.ozet_yukle()

    def islem_ekle(self, tablo, tip):
        cari = self.secili_cari_bilgisi(tablo)
        if cari is None:
            return False

        pencere = QDialog(self)
        pencere.setWindowTitle(f"{tip} Ekle - {cari['ad']}")
        pencere.resize(420, 320)

        layout = QVBoxLayout()

        lblCari = QLabel(f"Cari: {cari['ad']}")
        lblCari.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(lblCari)

        layout.addWidget(QLabel("Tutar"))
        txtTutar = QLineEdit()
        txtTutar.setPlaceholderText("Örn: 1500")
        layout.addWidget(txtTutar)

        layout.addWidget(QLabel("Açıklama"))
        txtAciklama = QTextEdit()
        layout.addWidget(txtAciklama)

        btnKaydet = QPushButton("Kaydet")
        layout.addWidget(btnKaydet)

        def kaydet():
            tutar = self.tutar_oku(txtTutar.text())
            if tutar is None:
                QMessageBox.warning(pencere, "Hata", "Tutar sayısal olmalı.")
                return

            if tutar <= 0:
                QMessageBox.warning(pencere, "Hata", "Tutar 0'dan büyük olmalı.")
                return

            if tutar > MAKS_TUTAR:
                QMessageBox.warning(pencere, "Hata", f"Tutar {para_yaz(MAKS_TUTAR)} değerinden büyük olamaz.")
                return

            aciklama = txtAciklama.toPlainText().strip()
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")

            conn = baglan()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih) VALUES (?, ?, ?, ?, ?)",
                (cari["id"], tip, tutar, aciklama, tarih)
            )
            conn.commit()
            conn.close()

            if tablo is not None:
                self.cari_liste_yukle(tablo)

            self.ozet_yukle()
            pencere.islem_kaydedildi = True
            pencere.accept()

        btnKaydet.clicked.connect(kaydet)

        pencere.islem_kaydedildi = False
        pencere.setLayout(layout)
        pencere.exec()

        return getattr(pencere, "islem_kaydedildi", False)

    def pdf_ekstre_olustur(self, cari):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            QMessageBox.warning(
                self,
                "Eksik Paket",
                "PDF oluşturmak için reportlab gerekli.\n\nTerminale şunu yaz:\npip install reportlab"
            )
            return

        dosya_yolu, _ = QFileDialog.getSaveFileName(
            self,
            "PDF Ekstre Kaydet",
            f"{cari['ad']}_Cari_Ekstre.pdf",
            "PDF Dosyası (*.pdf)"
        )

        if not dosya_yolu:
            return

        if not dosya_yolu.lower().endswith(".pdf"):
            dosya_yolu += ".pdf"

        conn = baglan()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, tarih, tip, tutar, aciklama FROM hareketler WHERE COALESCE(aktif,1)=1 AND cari_id=? ORDER BY id",
            (cari["id"],)
        )
        hareketler = cur.fetchall()
        conn.close()

        try:
            font_path = "C:/Windows/Fonts/arial.ttf"
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            font_adi = "Arial"
        except Exception:
            font_adi = "Helvetica"

        doc = SimpleDocTemplate(
            dosya_yolu,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        styles["Title"].fontName = font_adi
        styles["Normal"].fontName = font_adi

        elemanlar = []
        firma = firma_bilgisi_getir()
        elemanlar.append(Paragraph(firma["firma_adi"], styles["Title"]))
        elemanlar.append(Paragraph(firma["telefon"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["adres"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["vergi_no"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["vergi_dairesi"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["eposta"], styles["Normal"]))
        elemanlar.append(Spacer(1, 12))
        elemanlar.append(Paragraph("CARİ EKSTRE", styles["Title"]))
        elemanlar.append(Spacer(1, 12))
        elemanlar.append(Paragraph(f"Cari: {cari['ad']}", styles["Normal"]))
        elemanlar.append(Spacer(1, 12))

        tablo_veri = [["Tarih", "Tip", "Tutar", "Açıklama", "Bakiye"]]
        bakiye = 0.0

        for hareket in hareketler:
            if len(hareket) == 5:
                _, tarih, tip, tutar, aciklama = hareket
            else:
                tarih, tip, tutar, aciklama = hareket

            tutar = float(tutar or 0)
            if tip == "BORÇ":
                bakiye += tutar
            elif tip == "TAHSİLAT":
                bakiye -= tutar

            tablo_veri.append([
                str(tarih),
                str(tip),
                para_yaz(tutar),
                str(aciklama or ""),
                para_yaz(bakiye)
            ])

        if len(tablo_veri) == 1:
            tablo_veri.append(["", "Hareket yok", "", "", ""])

        pdf_tablo = Table(tablo_veri, repeatRows=1)
        pdf_tablo.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_adi),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1976D2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))

        elemanlar.append(pdf_tablo)
        elemanlar.append(Spacer(1, 18))
        elemanlar.append(Paragraph(f"KALAN BAKİYE: {para_yaz(bakiye)}", styles["Title"]))

        try:
            doc.build(elemanlar)
        except PermissionError:
            QMessageBox.warning(self, "Hata", "PDF dosyası açık olabilir. Kapatıp tekrar deneyin.")
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"PDF oluşturulamadı:\n{hata}")

    def secili_hareket_id(self, tabloH):
        for satir in range(tabloH.rowCount()):
            item = tabloH.item(satir, 0)
            if item is not None and item.checkState() == Qt.Checked:
                return int(tabloH.item(satir, 1).text())

        secili = tabloH.currentRow()

        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir işlem satırı seçin.")
            return None

        id_sutun = 1 if tabloH.columnCount() >= 7 else 0
        return int(tabloH.item(secili, id_sutun).text())

    def islem_duzenle(self, tabloH, cari):
        hareket_id = self.secili_hareket_id(tabloH)
        if hareket_id is None:
            return

        conn = baglan()
        cur = conn.cursor()
        cur.execute(
            "SELECT tip, tutar, aciklama FROM hareketler WHERE COALESCE(aktif,1)=1 AND id=?",
            (hareket_id,)
        )
        hareket = cur.fetchone()
        conn.close()

        if not hareket:
            QMessageBox.warning(self, "Hata", "İşlem bulunamadı.")
            return

        eski_tip, eski_tutar, eski_aciklama = hareket

        pencere = QDialog(self)
        pencere.setWindowTitle("İşlem Düzenle")
        pencere.resize(420, 360)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("İşlem Tipi"))
        txtTip = QLineEdit()
        txtTip.setText(eski_tip)
        txtTip.setPlaceholderText("BORÇ veya TAHSİLAT")
        layout.addWidget(txtTip)

        layout.addWidget(QLabel("Tutar"))
        txtTutar = QLineEdit()
        txtTutar.setText(str(eski_tutar))
        layout.addWidget(txtTutar)

        layout.addWidget(QLabel("Açıklama"))
        txtAciklama = QTextEdit()
        txtAciklama.setPlainText(eski_aciklama or "")
        layout.addWidget(txtAciklama)

        btnGuncelle = QPushButton("Güncelle")
        layout.addWidget(btnGuncelle)

        def guncelle():
            tip = txtTip.text().strip().upper()
            if tip not in ["BORÇ", "TAHSİLAT"]:
                QMessageBox.warning(pencere, "Hata", "Tip sadece BORÇ veya TAHSİLAT olabilir.")
                return

            tutar = self.tutar_oku(txtTutar.text())
            if tutar is None:
                QMessageBox.warning(pencere, "Hata", "Tutar sayısal olmalı.")
                return

            if tutar <= 0:
                QMessageBox.warning(pencere, "Hata", "Tutar 0'dan büyük olmalı.")
                return

            if tutar > MAKS_TUTAR:
                QMessageBox.warning(pencere, "Hata", f"Tutar {para_yaz(MAKS_TUTAR)} değerinden büyük olamaz.")
                return

            aciklama = txtAciklama.toPlainText().strip()

            conn = baglan()
            cur = conn.cursor()
            cur.execute(
                "UPDATE hareketler SET tip=?, tutar=?, aciklama=? WHERE id=?",
                (tip, tutar, aciklama, hareket_id)
            )
            conn.commit()
            conn.close()

            pencere.islem_guncellendi = True
            pencere.accept()

        btnGuncelle.clicked.connect(guncelle)

        pencere.islem_guncellendi = False
        pencere.setLayout(layout)
        pencere.exec()

        return getattr(pencere, "islem_guncellendi", False)

    def islem_sil(self, tabloH):
        hareket_id = self.secili_hareket_id(tabloH)
        if hareket_id is None:
            return

        cevap = QMessageBox.question(
            self,
            "Silme Onayı",
            "Seçili işlemi silmek istiyor musunuz?"
        )

        if cevap != QMessageBox.Yes:
            return

        conn = baglan()
        cur = conn.cursor()
        cur.execute("UPDATE hareketler SET aktif=0 WHERE id=?", (hareket_id,))
        audit_yaz("hareket_pasife_alindi", "hareketler", hareket_id)
        conn.commit()
        conn.close()

        return True

    def cari_ekstre(self, tablo):
        cari = self.secili_cari_bilgisi(tablo)
        if cari is None:
            return

        pencere = QDialog(self)
        pencere.setWindowTitle(f"Cari Ekstre - {cari['ad']}")
        pencere.resize(850, 550)

        layout = QVBoxLayout()

        baslik = QLabel(f"CARİ EKSTRE: {cari['ad']}")
        baslik.setStyleSheet("font-size:22px;font-weight:bold;padding:10px;")
        layout.addWidget(baslik)

        tabloH = QTableWidget()
        tabloH.setColumnCount(7)
        tabloH.setHorizontalHeaderLabels(["Seç", "ID", "Tarih", "Tip", "Tutar", "Açıklama", "Bakiye"])
        tabloH.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabloH.setSelectionBehavior(QTableWidget.SelectRows)
        tabloH.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloH.verticalHeader().setVisible(False)

        conn = baglan()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, tarih, tip, tutar, aciklama FROM hareketler WHERE COALESCE(aktif,1)=1 AND cari_id=? ORDER BY id",
            (cari["id"],)
        )
        hareketler = cur.fetchall()
        conn.close()

        tabloH.setRowCount(len(hareketler))

        bakiye = 0.0

        for satir, hareket in enumerate(hareketler):
            hareket_id, tarih, tip, tutar, aciklama = hareket

            if tip == "BORÇ":
                bakiye += float(tutar)
            elif tip == "TAHSİLAT":
                bakiye -= float(tutar)

            sec_item = QTableWidgetItem()
            sec_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            sec_item.setCheckState(Qt.Unchecked)
            tabloH.setItem(satir, 0, sec_item)

            veriler = [hareket_id, tarih, tip, para_yaz(float(tutar)), aciklama, para_yaz(bakiye)]

            for sutun, alan in enumerate(veriler, start=1):
                tabloH.setItem(satir, sutun, QTableWidgetItem(str(alan)))

        layout.addWidget(tabloH)

        lblBakiye = QLabel(f"KALAN BAKİYE: {para_yaz(bakiye)}")
        lblBakiye.setStyleSheet("font-size:20px;font-weight:bold;padding:12px;color:#0D47A1;")
        layout.addWidget(lblBakiye)

        butonlar = QHBoxLayout()

        def ekstre_yenile():
            self.cari_liste_yukle(tablo)
            self.cari_satir_sec(tablo, cari["id"])
            pencere.close()
            self.cari_ekstre(tablo)

        def duzenle_ve_yenile():
            sonuc = self.islem_duzenle(tabloH, cari)
            if sonuc:
                ekstre_yenile()

        def sil_ve_yenile():
            sonuc = self.islem_sil(tabloH)
            if sonuc:
                ekstre_yenile()

        btnDuzenle = QPushButton("İşlem Düzenle")
        btnDuzenle.clicked.connect(duzenle_ve_yenile)
        butonlar.addWidget(btnDuzenle)

        btnSil = QPushButton("İşlem Sil")
        btnSil.clicked.connect(sil_ve_yenile)
        butonlar.addWidget(btnSil)

        btnYenile = QPushButton("Yenile")
        btnYenile.clicked.connect(ekstre_yenile)
        butonlar.addWidget(btnYenile)

        btnPdf = QPushButton("PDF Oluştur")
        btnPdf.clicked.connect(lambda: self.pdf_ekstre_olustur(cari))
        butonlar.addWidget(btnPdf)

        btnWhatsapp = QPushButton("PDF + WhatsApp")
        btnWhatsapp.clicked.connect(lambda: self.whatsapp_mesaj_gonder(cari))
        butonlar.addWidget(btnWhatsapp)

        btnKapat = QPushButton("Kapat")
        btnKapat.clicked.connect(pencere.close)
        butonlar.addWidget(btnKapat)

        layout.addLayout(butonlar)

        pencere.setLayout(layout)
        pencere.exec()






    def telefon_temizle(self, telefon):
        return telefon_temizle(telefon)

    def pdf_ekstre_otomatik_olustur(self, cari):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ImportError:
            QMessageBox.warning(
                self,
                "Eksik Paket",
                "PDF oluşturmak için reportlab gerekli.\n\nTerminale şunu yaz:\npip install reportlab"
            )
            return None

        os.makedirs(os.path.join(BASE_DIR, "pdfler"), exist_ok=True)

        temiz_ad = "".join(ch for ch in cari["ad"] if ch.isalnum() or ch in (" ", "_", "-")).strip()
        temiz_ad = temiz_ad.replace(" ", "_")
        tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dosya_yolu = os.path.join(BASE_DIR, "pdfler", f"{temiz_ad}_Cari_Ekstre_{tarih}.pdf")

        conn = baglan()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, tarih, tip, tutar, aciklama FROM hareketler WHERE COALESCE(aktif,1)=1 AND cari_id=? ORDER BY id",
            (cari["id"],)
        )
        hareketler = cur.fetchall()
        conn.close()

        try:
            font_path = "C:/Windows/Fonts/arial.ttf"
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            font_adi = "Arial"
        except Exception:
            font_adi = "Helvetica"

        doc = SimpleDocTemplate(
            dosya_yolu,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        styles["Title"].fontName = font_adi
        styles["Normal"].fontName = font_adi

        elemanlar = []
        firma = firma_bilgisi_getir()

        elemanlar.append(Paragraph(firma["firma_adi"], styles["Title"]))
        elemanlar.append(Paragraph(firma["telefon"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["adres"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["vergi_no"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["vergi_dairesi"], styles["Normal"]))
        elemanlar.append(Paragraph(firma["eposta"], styles["Normal"]))
        elemanlar.append(Spacer(1, 12))
        elemanlar.append(Paragraph("CARİ EKSTRE", styles["Title"]))
        elemanlar.append(Spacer(1, 12))
        elemanlar.append(Paragraph(f"Cari: {cari['ad']}", styles["Normal"]))
        elemanlar.append(Spacer(1, 12))

        tablo_veri = [["Tarih", "Tip", "Tutar", "Açıklama", "Bakiye"]]
        bakiye = 0.0

        for hareket in hareketler:
            if len(hareket) == 5:
                _, tarih_text, tip, tutar, aciklama = hareket
            else:
                tarih_text, tip, tutar, aciklama = hareket

            tutar = float(tutar or 0)

            if tip == "BORÇ":
                bakiye += tutar
            elif tip == "TAHSİLAT":
                bakiye -= tutar

            tablo_veri.append([
                str(tarih_text),
                str(tip),
                para_yaz(tutar),
                str(aciklama or ""),
                para_yaz(bakiye)
            ])

        if len(tablo_veri) == 1:
            tablo_veri.append(["", "Hareket yok", "", "", ""])

        pdf_tablo = Table(tablo_veri, repeatRows=1)
        pdf_tablo.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_adi),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1976D2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))

        elemanlar.append(pdf_tablo)
        elemanlar.append(Spacer(1, 18))
        elemanlar.append(Paragraph(f"KALAN BAKİYE: {para_yaz(bakiye)}", styles["Title"]))

        try:
            doc.build(elemanlar)
            return dosya_yolu
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"PDF oluşturulamadı:\n{hata}")
            return None

    def whatsapp_mesaj_gonder(self, cari):
        telefon = self.telefon_temizle(cari.get("telefon", ""))

        if not telefon:
            QMessageBox.warning(self, "Uyarı", "Bu carinin telefon numarası yok.")
            return

        conn = baglan()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN tip='BORÇ' THEN tutar ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN tip='TAHSİLAT' THEN tutar ELSE 0 END), 0)
            FROM hareketler
            WHERE cari_id=?
        """, (cari["id"],))

        toplam_borc, toplam_tahsilat = cur.fetchone()
        conn.close()

        toplam_borc = float(toplam_borc or 0)
        toplam_tahsilat = float(toplam_tahsilat or 0)
        kalan = toplam_borc - toplam_tahsilat

        pdf_yolu = self.pdf_ekstre_otomatik_olustur(cari)

        firma = firma_bilgisi_getir()

        mesaj = (
            f"Merhaba {cari['ad']},\n\n"
            f"{firma['firma_adi']} cari hesap özetiniz:\n"
            f"Toplam Borç: {para_yaz(toplam_borc)}\n"
            f"Toplam Tahsilat: {para_yaz(toplam_tahsilat)}\n"
            f"Kalan Bakiye: {para_yaz(kalan)}\n\n"
            f"Detaylı cari ekstrenizi PDF olarak gönderiyorum.\n\n"
            f"İyi çalışmalar."
        )

        url = f"https://wa.me/{telefon}?text={urllib.parse.quote(mesaj)}"

        webbrowser.open(url)

        if pdf_yolu:
            try:
                os.startfile(os.path.join(BASE_DIR, "pdfler"))
            except Exception:
                pass

            QMessageBox.information(
                self,
                "WhatsApp Açıldı",
                f"PDF oluşturuldu:\n{pdf_yolu}\n\n"
                "WhatsApp Web açıldı.\n"
                "Mesajı kontrol edin, ardından PDF dosyasını WhatsApp'a ekleyip gönderin."
            )
        else:
            QMessageBox.information(
                self,
                "WhatsApp Açıldı",
                "WhatsApp Web açıldı.\nMesajı kontrol edip gönder tuşuna siz basın."
            )

    def cari_detay_penceresi(self, tablo=None, cari_id=None):
        if cari_id is None:
            if tablo is None:
                QMessageBox.warning(self, "Uyarı", "Cari seçimi bulunamadı.")
                return
            cari = self.secili_cari_bilgisi(tablo)
        else:
            cari = self.cari_bilgisi_getir_id(cari_id)

        if cari is None:
            QMessageBox.warning(self, "Hata", "Cari bulunamadı.")
            return

        conn = baglan()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN tip='BORÇ' THEN tutar ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN tip='TAHSİLAT' THEN tutar ELSE 0 END), 0)
            FROM hareketler
            WHERE cari_id=?
        """, (cari["id"],))

        toplam_borc, toplam_tahsilat = cur.fetchone()
        toplam_borc = float(toplam_borc or 0)
        toplam_tahsilat = float(toplam_tahsilat or 0)
        kalan = toplam_borc - toplam_tahsilat

        cur.execute("""
            SELECT tarih, tip, tutar, aciklama
            FROM hareketler
            WHERE cari_id=?
            ORDER BY id DESC
            LIMIT 10
        """, (cari["id"],))

        son_islemler = cur.fetchall()
        conn.close()

        pencere = QDialog(self)
        pencere.setWindowTitle(f"Cari Detay - {cari['ad']}")
        pencere.resize(850, 620)

        layout = QVBoxLayout()

        baslik = QLabel("CARİ DETAY KARTI")
        baslik.setStyleSheet("font-size:24px;font-weight:bold;padding:10px;color:#0D47A1;")
        layout.addWidget(baslik)

        bilgi_kutu = QFrame()
        bilgi_layout = QVBoxLayout()

        bilgi = QLabel(
            f"Ad Soyad: {cari['ad']}\n"
            f"Telefon: {cari['telefon']}\n"
            f"Adres: {cari['adres']}\n"
            f"Vergi Dairesi: {cari.get('vergi_dairesi', '') or '-'}\n"
            f"Vergi No: {cari.get('vergi_no', '') or '-'}"
        )
        bilgi.setStyleSheet("font-size:16px;font-weight:bold;padding:8px;")
        bilgi_layout.addWidget(bilgi)

        bilgi_kutu.setLayout(bilgi_layout)
        layout.addWidget(bilgi_kutu)

        kartlar = QHBoxLayout()

        def detay_kart(baslik_text, deger_text):
            kutu = QFrame()
            kutu_layout = QVBoxLayout()
            lbl1 = QLabel(baslik_text)
            lbl1.setStyleSheet("font-size:14px;color:#555;")
            lbl2 = QLabel(deger_text)
            lbl2.setStyleSheet("font-size:20px;font-weight:bold;color:#0D47A1;")
            kutu_layout.addWidget(lbl1)
            kutu_layout.addWidget(lbl2)
            kutu.setLayout(kutu_layout)
            kartlar.addWidget(kutu)

        detay_kart("Toplam Borç", para_yaz(toplam_borc))
        detay_kart("Toplam Tahsilat", para_yaz(toplam_tahsilat))
        detay_kart("Kalan Bakiye", para_yaz(kalan))

        layout.addLayout(kartlar)

        lblSon = QLabel("SON 10 İŞLEM")
        lblSon.setStyleSheet("font-size:18px;font-weight:bold;padding:8px;")
        layout.addWidget(lblSon)

        tabloSon = QTableWidget()
        tabloSon.setColumnCount(4)
        tabloSon.setHorizontalHeaderLabels(["Tarih", "Tip", "Tutar", "Açıklama"])
        tabloSon.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabloSon.setSelectionBehavior(QTableWidget.SelectRows)
        tabloSon.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloSon.verticalHeader().setVisible(False)

        tabloSon.setRowCount(len(son_islemler))

        for satir, islem in enumerate(son_islemler):
            tarih, tip, tutar, aciklama = islem
            veriler = [tarih, tip, para_yaz(float(tutar or 0)), aciklama or ""]
            for sutun, alan in enumerate(veriler):
                tabloSon.setItem(satir, sutun, QTableWidgetItem(str(alan)))

        layout.addWidget(tabloSon)

        butonlar = QHBoxLayout()

        def detay_yenile():
            self.cari_liste_yukle(tablo)
            self.cari_satir_sec(tablo, cari["id"])
            pencere.close()
            self.cari_detay_penceresi(tablo, cari["id"])

        def borc_ekle_ve_yenile():
            if self.islem_ekle(tablo, "BORÇ"):
                detay_yenile()

        def tahsilat_ekle_ve_yenile():
            if self.islem_ekle(tablo, "TAHSİLAT"):
                detay_yenile()

        btnBorc = QPushButton("Borç Ekle")
        btnBorc.clicked.connect(borc_ekle_ve_yenile)
        butonlar.addWidget(btnBorc)

        btnTahsilat = QPushButton("Tahsilat Ekle")
        btnTahsilat.clicked.connect(tahsilat_ekle_ve_yenile)
        butonlar.addWidget(btnTahsilat)

        btnEkstre = QPushButton("Ekstre Aç")
        btnEkstre.clicked.connect(lambda: self.cari_ekstre(tablo))
        butonlar.addWidget(btnEkstre)

        btnWhatsapp = QPushButton("PDF + WhatsApp")
        btnWhatsapp.clicked.connect(lambda: self.whatsapp_mesaj_gonder(cari))
        butonlar.addWidget(btnWhatsapp)

        btnKapat = QPushButton("Kapat")
        btnKapat.clicked.connect(pencere.close)
        butonlar.addWidget(btnKapat)

        layout.addLayout(butonlar)

        pencere.setLayout(layout)
        pencere.exec()

    def islem_silme_penceresi(self, tablo):
        cari = self.secili_cari_bilgisi(tablo)
        if cari is None:
            return

        pencere = QDialog(self)
        pencere.setWindowTitle(f"İşlem Sil - {cari['ad']}")
        pencere.resize(850, 520)

        layout = QVBoxLayout()

        baslik = QLabel(f"İŞLEM SİL: {cari['ad']}")
        baslik.setStyleSheet("font-size:22px;font-weight:bold;padding:10px;color:#0D47A1;")
        layout.addWidget(baslik)

        tabloH = QTableWidget()
        tabloH.setColumnCount(6)
        tabloH.setHorizontalHeaderLabels(["Seç", "ID", "Tarih", "Tip", "Tutar", "Açıklama"])
        tabloH.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabloH.setSelectionBehavior(QTableWidget.SelectRows)
        tabloH.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloH.verticalHeader().setVisible(False)
        layout.addWidget(tabloH)

        def hareketleri_yukle():
            conn = baglan()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, tarih, tip, tutar, aciklama
                FROM hareketler
                WHERE cari_id=?
                ORDER BY id DESC
            """, (cari["id"],))
            hareketler = cur.fetchall()
            conn.close()

            tabloH.setRowCount(len(hareketler))

            for satir, hareket in enumerate(hareketler):
                hareket_id, tarih, tip, tutar, aciklama = hareket
                sec_item = QTableWidgetItem()
                sec_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                sec_item.setCheckState(Qt.Unchecked)
                tabloH.setItem(satir, 0, sec_item)

                veriler = [
                    hareket_id,
                    tarih,
                    tip,
                    para_yaz(float(tutar or 0)),
                    aciklama or ""
                ]

                for sutun, alan in enumerate(veriler, start=1):
                    tabloH.setItem(satir, sutun, QTableWidgetItem(str(alan)))

        def secili_hareketi_sil():
            secili = tabloH.currentRow()

            hareket_id = None
            secili_satir = secili

            for satir in range(tabloH.rowCount()):
                item = tabloH.item(satir, 0)
                if item is not None and item.checkState() == Qt.Checked:
                    hareket_id = int(tabloH.item(satir, 1).text())
                    secili_satir = satir
                    break

            if hareket_id is None:
                if secili < 0:
                    QMessageBox.warning(pencere, "Uyarı", "Lütfen silmek için bir işlem seçin veya kutucuğu işaretleyin.")
                    return
                hareket_id = int(tabloH.item(secili, 1).text())

            tip = tabloH.item(secili_satir, 3).text()
            tutar = tabloH.item(secili_satir, 4).text()

            cevap = QMessageBox.question(
                pencere,
                "Silme Onayı",
                f"Seçili işlemi silmek istiyor musunuz?\n\nTip: {tip}\nTutar: {tutar}"
            )

            if cevap != QMessageBox.Yes:
                return

            conn = baglan()
            cur = conn.cursor()
            cur.execute("UPDATE hareketler SET aktif=0 WHERE id=?", (hareket_id,))
            audit_yaz("hareket_pasife_alindi", "hareketler", hareket_id)
            conn.commit()
            conn.close()

            hareketleri_yukle()
            self.cari_liste_yukle(tablo)
            self.cari_satir_sec(tablo, cari["id"])
            self.ozet_yukle()

        butonlar = QHBoxLayout()

        btnSil = QPushButton("Seçili İşlemi Sil")
        btnSil.clicked.connect(secili_hareketi_sil)
        butonlar.addWidget(btnSil)

        btnYenile = QPushButton("Yenile")
        btnYenile.clicked.connect(hareketleri_yukle)
        butonlar.addWidget(btnYenile)

        btnKapat = QPushButton("Kapat")
        btnKapat.clicked.connect(pencere.close)
        butonlar.addWidget(btnKapat)

        layout.addLayout(butonlar)

        hareketleri_yukle()

        pencere.setLayout(layout)
        pencere.exec()

    def cari_penceresi(self):
        pencere = QDialog(self)
        pencere.setWindowTitle("Cari Kartları")
        pencere.resize(1000, 620)

        layout = QVBoxLayout()

        baslik = QLabel("CARİ KARTLARI")
        baslik.setStyleSheet("font-size:24px;font-weight:bold;padding:10px;")
        layout.addWidget(baslik)

        arama_layout = QHBoxLayout()
        arama_layout.addWidget(QLabel("Cari Ara:"))

        txtArama = QLineEdit()
        txtArama.setPlaceholderText("Ad, telefon veya adres yaz...")
        arama_layout.addWidget(txtArama)

        lblKayit = QLabel("Toplam Kayıt: 0")
        lblKayit.setStyleSheet("font-weight:bold;")
        arama_layout.addWidget(lblKayit)

        layout.addLayout(arama_layout)

        tablo = QTableWidget()
        tablo.setColumnCount(5)
        tablo.setHorizontalHeaderLabels(["No", "Ad Soyad", "Telefon", "Adres", "Bakiye"])
        tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tablo.setSelectionBehavior(QTableWidget.SelectRows)
        tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        tablo.verticalHeader().setVisible(False)

        def liste_yenile():
            self.cari_liste_yukle(tablo, txtArama.text())
            lblKayit.setText(f"Toplam Kayıt: {tablo.rowCount()}")

        txtArama.textChanged.connect(liste_yenile)
        tablo.cellDoubleClicked.connect(lambda row, col: self.cari_detay_penceresi(tablo))

        butonlar1 = QHBoxLayout()

        def yeni_cari_ekle_listeyi_yenile():
            yeni_id = self.yeni_cari(tablo)
            if yeni_id:
                self.cari_liste_yukle(tablo)
                self.cari_satir_sec(tablo, yeni_id)
                lblKayit.setText(f"Toplam Kayıt: {tablo.rowCount()}")

        btnYeni = QPushButton("Yeni Cari")
        btnYeni.clicked.connect(yeni_cari_ekle_listeyi_yenile)
        butonlar1.addWidget(btnYeni)

        btnDuzenle = QPushButton("Düzenle")
        btnDuzenle.clicked.connect(lambda: self.cari_duzenle(tablo))
        butonlar1.addWidget(btnDuzenle)

        btnSil = QPushButton("Sil")
        btnSil.clicked.connect(lambda: self.cari_sil(tablo))
        butonlar1.addWidget(btnSil)

        btnDetay = QPushButton("Cari Detay")
        btnDetay.clicked.connect(lambda: self.cari_detay_penceresi(tablo))
        butonlar1.addWidget(btnDetay)

        btnKapat = QPushButton("Kapat")
        btnKapat.clicked.connect(pencere.close)
        butonlar1.addWidget(btnKapat)

        butonlar2 = QHBoxLayout()

        def borc_ekle_listeyi_yenile():
            cari = self.secili_cari_bilgisi(tablo)
            if cari is None:
                return

            sonuc = self.islem_ekle(tablo, "BORÇ")

            if sonuc:
                self.cari_liste_yukle(tablo, txtArama.text())
                self.cari_satir_sec(tablo, cari["id"])
                lblKayit.setText(f"Toplam Kayıt: {tablo.rowCount()}")
                self.ozet_yukle()

        def tahsilat_ekle_listeyi_yenile():
            cari = self.secili_cari_bilgisi(tablo)
            if cari is None:
                return

            sonuc = self.islem_ekle(tablo, "TAHSİLAT")

            if sonuc:
                self.cari_liste_yukle(tablo, txtArama.text())
                self.cari_satir_sec(tablo, cari["id"])
                lblKayit.setText(f"Toplam Kayıt: {tablo.rowCount()}")
                self.ozet_yukle()

        btnBorc = QPushButton("Borç Ekle")
        btnBorc.clicked.connect(borc_ekle_listeyi_yenile)
        butonlar2.addWidget(btnBorc)

        btnTahsilat = QPushButton("Tahsilat Ekle")
        btnTahsilat.clicked.connect(tahsilat_ekle_listeyi_yenile)
        butonlar2.addWidget(btnTahsilat)

        btnIslemSil = QPushButton("İşlem Sil")
        btnIslemSil.clicked.connect(lambda: self.islem_silme_penceresi(tablo))
        butonlar2.addWidget(btnIslemSil)

        btnEkstre = QPushButton("Cari Ekstre")
        btnEkstre.clicked.connect(lambda: self.cari_ekstre(tablo))
        butonlar2.addWidget(btnEkstre)

        layout.addLayout(butonlar1)
        layout.addLayout(butonlar2)
        layout.addWidget(tablo)

        liste_yenile()

        pencere.setLayout(layout)
        pencere.exec()

    def _sayi_oku(self, metin):
        """Türkçe para/sayı girişlerini güvenli şekilde float'a çevirir."""
        try:
            metin = str(metin or "0").replace("₺", "").strip()
            metin = metin.replace(".", "").replace(",", ".")
            return float(metin)
        except Exception:
            return 0.0

    def _whatsapp_ac(self, telefon, mesaj):
        tel = "".join(ch for ch in str(telefon or "") if ch.isdigit())
        if tel.startswith("0"):
            tel = "90" + tel[1:]
        elif tel and not tel.startswith("90"):
            tel = "90" + tel
        url = "https://wa.me/" + tel + "?text=" + urllib.parse.quote(mesaj)
        webbrowser.open(url)

