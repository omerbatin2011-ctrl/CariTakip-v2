import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.config import BASE_DIR, YEDEK_KLASOR_ADI
from moduller.db import db_baglan
from moduller.loglama import log_yaz
from moduller.yardimci import para_yaz
from moduller.yetki import aktif_kullanici_getir


class DashboardMixin:
    def modern_kart_olustur(self, grid, row, col, ikon, baslik, deger, alt_metin, ikon_bg, ikon_color):
        """Dashboard KPI kartı.

        v125: Kartlar ideal genişlikte kalacak şekilde yeniden düzenlendi;
        metin alanı esnek yapıldı, ikon alanı küçültüldü ve tutar etiketi
        kart genişliğine göre font küçültebilecek şekilde hazırlandı.
        """
        from PySide6.QtWidgets import QSizePolicy

        kart = QFrame()
        kart.setObjectName("MetricCard")
        kart.setMinimumHeight(92)
        kart.setMaximumHeight(102)
        kart.setMinimumWidth(238)
        kart.setMaximumWidth(315)
        kart.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QHBoxLayout()
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(11)

        lblIkon = QLabel(ikon)
        lblIkon.setAlignment(Qt.AlignCenter)
        lblIkon.setFixedSize(38, 38)
        lblIkon.setStyleSheet(
            f"background:{ikon_bg};color:{ikon_color};border-radius:11px;"
            "font-size:18px;font-weight:900;"
        )

        yazi = QVBoxLayout()
        yazi.setContentsMargins(0, 0, 0, 0)
        yazi.setSpacing(2)

        lblBaslik = QLabel(baslik)
        lblBaslik.setObjectName("MetricTitle")
        lblBaslik.setStyleSheet("font-size:12px;color:#475569;font-weight:800;")
        lblBaslik.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lblDeger = QLabel(deger)
        lblDeger.setObjectName("MetricValue")
        lblDeger.setMinimumWidth(118)
        lblDeger.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lblDeger.setWordWrap(False)
        lblDeger.setTextInteractionFlags(Qt.NoTextInteraction)
        lblDeger.setStyleSheet("font-size:19px;color:#0B1220;font-weight:900;")

        lblAlt = QLabel(alt_metin)
        lblAlt.setObjectName("MetricSub")
        lblAlt.setStyleSheet("font-size:10px;color:#64748B;")
        lblAlt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        yazi.addWidget(lblBaslik)
        yazi.addWidget(lblDeger)
        yazi.addWidget(lblAlt)

        layout.addWidget(lblIkon, 0, Qt.AlignVCenter)
        layout.addLayout(yazi, 1)
        kart.setLayout(layout)
        grid.addWidget(kart, row, col)
        return lblDeger

    def dashboard_kpi_font_ayarla(self):
        """Uzun tutarlarda KPI değer fontunu otomatik küçültür."""
        labels = [
            "lblBugunSatisKart", "lblDashboardTahsilat", "lblDashboardAylikSatis",
            "lblDashboardBorc", "lblDashboardKasaToplam", "lblKritikStokKart",
        ]
        for name in labels:
            lbl = getattr(self, name, None)
            if not lbl:
                continue
            text = lbl.text() or ""
            # TL tutarları uzunlaştığında taşmayı engelle.
            if len(text) >= 18:
                fs = 14
            elif len(text) >= 14:
                fs = 15
            elif len(text) >= 11:
                fs = 17
            else:
                fs = 19
            lbl.setStyleSheet(f"font-size:{fs}px;color:#0B1220;font-weight:900;")

    def satis_grafik_guncelle(self):
        """v64: Son 30 gün satışlarını gerçek grafik olarak gösterir; matplotlib yoksa metin grafik kullanır."""
        rows = []
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT substr(tarih, 1, 10) AS gun, COALESCE(SUM(toplam),0) AS toplam
                    FROM satislar
                    WHERE belge_turu='SATIŞ'
                    GROUP BY substr(tarih, 1, 10)
                    ORDER BY gun DESC
                    LIMIT 30
                """)
                rows = list(reversed(cur.fetchall()))
        except Exception as hata:
            try:
                log_yaz(f"Satış grafiği hesaplanamadı: {hata}")
            except Exception:
                pass
            rows = []

        # Matplotlib canvas varsa gerçek çizgi grafik çiz.
        if hasattr(self, "figSatis") and hasattr(self, "canvasSatis"):
            try:
                self.figSatis.clear()
                ax = self.figSatis.add_subplot(111)

                if rows:
                    gunler = [str(gun)[-5:] for gun, _ in rows]
                    tutarlar = [float(toplam or 0) for _, toplam in rows]
                    ax.plot(gunler, tutarlar, marker="o", linewidth=2)
                    ax.fill_between(gunler, tutarlar, alpha=0.10)
                    ax.set_title("Son 30 Gün Satış", fontsize=10, fontweight="bold")
                    ax.set_ylabel("₺")
                    ax.tick_params(axis="x", labelrotation=45, labelsize=8)
                    ax.tick_params(axis="y", labelsize=8)
                    ax.grid(True, alpha=0.25)
                else:
                    ax.text(
                        0.5, 0.5,
                        "Henüz satış verisi yok\nİlk satıştan sonra grafik oluşacak",
                        ha="center", va="center", fontsize=10, color="#64748B"
                    )
                    ax.set_xticks([])
                    ax.set_yticks([])

                self.figSatis.tight_layout(pad=1.4)
                self.canvasSatis.draw()
                return
            except Exception as hata:
                try:
                    log_yaz(f"Matplotlib grafik çizilemedi: {hata}")
                except Exception:
                    pass

        # Matplotlib yoksa eski metin grafik çalışsın.
        if not hasattr(self, "lblSatisGrafik"):
            return
        try:
            if not rows:
                self.lblSatisGrafik.setText(
                    "Henüz satış verisi yok.\n"
                    "İlk satıştan sonra bu bölüm günlük satış trendini gösterecek."
                )
                return
            maks = max(float(t or 0) for _, t in rows) or 1
            son = rows[-10:]
            satirlar = []
            toplam_10 = sum(float(t or 0) for _, t in son)
            satirlar.append(f"Son {len(son)} gün toplam: {para_yaz(toplam_10)}")
            satirlar.append("─" * 48)
            for gun, toplam in son:
                toplam = float(toplam or 0)
                bar_len = int((toplam / maks) * 24) if toplam > 0 else 0
                bar = "█" * max(1, bar_len) if toplam > 0 else "·"
                satirlar.append(f"{str(gun)[-5:]} │ {bar:<24} │ {para_yaz(toplam)}")
            self.lblSatisGrafik.setText("\n".join(satirlar))
        except Exception:
            self.lblSatisGrafik.setText("Satış grafiği şu an hesaplanamadı.")

    def dashboard_ek_bilgileri_yukle(self, force=False):
        """Dashboard sağ özet paneli: satış, kâr, stok, tahsilat alarmı ve en çok satan ürünler.

        v147 performans: Menü geçişlerinde aynı ağır sorguları peş peşe
        çalıştırmamak için kısa süreli cache/throttle kullanılır.
        """
        try:
            import time
            if not force:
                son = float(getattr(self, "_dashboard_son_yukleme", 0) or 0)
                if time.time() - son < 3.0:
                    return
            self._dashboard_son_yukleme = time.time()
            simdi = datetime.now()
            bugun = simdi.strftime("%d.%m.%Y")
            ay_like_tr = simdi.strftime("%.%m.%Y%")
            ay_like_iso = simdi.strftime("%Y-%m-%")
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COALESCE(SUM(toplam),0) FROM satislar WHERE tarih LIKE ? AND belge_turu='SATIŞ'", (bugun + "%",))
                bugun_satis = float(cur.fetchone()[0] or 0)

                cur.execute("SELECT COALESCE(SUM(tutar),0) FROM hareketler WHERE tarih LIKE ? AND tip='TAHSİLAT'", (bugun + "%",))
                bugun_tahsilat = float(cur.fetchone()[0] or 0)

                cur.execute("""
                    SELECT COALESCE(SUM(toplam),0)
                    FROM satislar
                    WHERE belge_turu='SATIŞ' AND (tarih LIKE ? OR tarih LIKE ?)
                """, (ay_like_tr, ay_like_iso))
                aylik_satis = float(cur.fetchone()[0] or 0)

                # Eski sürümde burada her satış kalemi için ayrı alış fiyatı
                # alt sorgusu çalışıyordu. Büyük veride açılışı ciddi yavaşlatır.
                # Kâr detayı rapor ekranında hesaplanabilir; dashboard hızlı açılmalı.
                bugun_kar = 0.0

                cur.execute("SELECT COUNT(*) FROM urunler WHERE COALESCE(stok,0) <= 5")
                kritik = int(cur.fetchone()[0] or 0)
                cur.execute("SELECT COUNT(*) FROM urunler")
                toplam_urun = int(cur.fetchone()[0] or 0)

                cur.execute("SELECT COUNT(*) FROM cariler WHERE COALESCE(aktif,1)=1")
                toplam_cari = int(cur.fetchone()[0] or 0)

                cur.execute("""
                    SELECT c.ad,
                           COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END),0) -
                           COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END),0) AS bakiye
                    FROM cariler c
                                    LEFT JOIN hareketler h ON h.cari_id = c.id
                    GROUP BY c.id, c.ad
                    HAVING bakiye > 0
                    ORDER BY bakiye DESC
                    LIMIT 3
                """)
                borclular = cur.fetchall()
                acik_alacak = sum(float(bakiye or 0) for _, bakiye in borclular)

                cur.execute("""
                    SELECT sk.urun_adi, COALESCE(SUM(sk.adet),0) AS adet, COALESCE(SUM(sk.tutar),0) AS toplam
                    FROM satislar s
                    JOIN satis_kalemleri sk ON sk.satis_id = s.id
                    WHERE s.belge_turu='SATIŞ'
                    GROUP BY sk.urun_adi
                    ORDER BY adet DESC, toplam DESC
                    LIMIT 6
                """)
                cok_satanlar = cur.fetchall()

                cur.execute("""
                    SELECT COALESCE(c.ad, 'İsimsiz Cari') AS cari,
                           COALESCE(SUM(s.toplam),0) AS toplam,
                           COUNT(*) AS islem_sayisi
                    FROM satislar s
                    LEFT JOIN cariler c ON c.id = s.cari_id
                    WHERE COALESCE(s.aktif,1)=1 AND s.belge_turu='SATIŞ'
                    GROUP BY s.cari_id, c.ad
                    ORDER BY toplam DESC
                    LIMIT 10
                """)
                top_musteriler = cur.fetchall()

                cur.execute("""
                    SELECT s.tarih, COALESCE(c.ad, '-'), COALESCE(s.teklif_no, '-'), COALESCE(s.toplam,0)
                    FROM satislar s
                    LEFT JOIN cariler c ON c.id = s.cari_id
                    WHERE COALESCE(s.aktif,1)=1 AND s.belge_turu='SATIŞ'
                    ORDER BY s.id DESC
                    LIMIT 6
                """)
                son_satislar = cur.fetchall()

                cur.execute("""
                    SELECT tarih, 'Satış', COALESCE(c.ad, '-'), COALESCE(s.toplam,0)
                    FROM satislar s
                    LEFT JOIN cariler c ON c.id = s.cari_id
                    WHERE COALESCE(s.aktif,1)=1 AND s.belge_turu='SATIŞ'
                    UNION ALL
                    SELECT h.tarih, h.tip, COALESCE(c.ad, COALESCE(h.aciklama, '-')), COALESCE(h.tutar,0)
                    FROM hareketler h
                    LEFT JOIN cariler c ON c.id = h.cari_id
                    ORDER BY tarih DESC
                    LIMIT 8
                """)
                son_islemler = cur.fetchall()

                cur.execute("""
                    SELECT COUNT(*)
                    FROM satislar
                    WHERE belge_turu='TEKLİF' AND COALESCE(teklif_durumu,'BEKLEMEDE')='BEKLEMEDE'
                """)
                bekleyen_teklif = int(cur.fetchone()[0] or 0)

                cur.execute("""
                    SELECT ad, COALESCE(stok,0), COALESCE(varsayilan_fiyat,0)
                    FROM urunler
                    WHERE COALESCE(aktif,1)=1 AND COALESCE(stok,0) <= 5
                    ORDER BY COALESCE(stok,0) ASC, ad ASC
                    LIMIT 6
                """)
                kritik_stoklar = cur.fetchall()

                try:
                    cur.execute("""
                        SELECT
                            COALESCE(SUM(CASE WHEN tip='GIRIS' AND odeme_tipi='NAKİT' THEN tutar WHEN tip='CIKIS' AND odeme_tipi='NAKİT' THEN -tutar ELSE 0 END),0),
                            COALESCE(SUM(CASE WHEN tip='GIRIS' AND odeme_tipi!='NAKİT' THEN tutar WHEN tip='CIKIS' AND odeme_tipi!='NAKİT' THEN -tutar ELSE 0 END),0)
                        FROM kasa_hareketleri
                    """)
                    kasa_nakit, kasa_kart = cur.fetchone()
                except Exception:
                    kasa_nakit, kasa_kart = 0, 0
                kasa_toplam = float(kasa_nakit or 0) + float(kasa_kart or 0)

            self.lblBugunSatis.setText(f"Bugün Satış\n{para_yaz(bugun_satis)}")
            if hasattr(self, "lblBildirimBugunSatis"):
                self.lblBildirimBugunSatis.setText(f"Bugünkü Satış\n{para_yaz(bugun_satis)}")
            if hasattr(self, "lblBugunKar"):
                self.lblBugunKar.setText(f"Bugünkü Kâr\n{para_yaz(bugun_kar)}")
            self.lblKritikStok.setText(f"Kritik Stok\n{kritik} ürün")
            if hasattr(self, "lblBugunSatisKart"):
                self.lblBugunSatisKart.setText(para_yaz(bugun_satis))
            if hasattr(self, "lblDashboardTahsilat"):
                self.lblDashboardTahsilat.setText(para_yaz(bugun_tahsilat))
            if hasattr(self, "lblDashboardKasaNakit"):
                self.lblDashboardKasaNakit.setText(f"Nakit Kasa\n{para_yaz(float(kasa_nakit or 0))}")
            if hasattr(self, "lblDashboardKasaKart"):
                self.lblDashboardKasaKart.setText(f"Kart Tahsilat\n{para_yaz(float(kasa_kart or 0))}")
            if hasattr(self, "lblDashboardAylikSatis"):
                self.lblDashboardAylikSatis.setText(para_yaz(aylik_satis))
            if hasattr(self, "lblKritikStokKart"):
                self.lblKritikStokKart.setText(f"{kritik} ürün")
            if hasattr(self, "lblToplamUrun"):
                self.lblToplamUrun.setText(f"Toplam Ürün\n{toplam_urun}")
            if hasattr(self, "lblDashboardKasaToplam"):
                self.lblDashboardKasaToplam.setText(para_yaz(kasa_toplam))
            if hasattr(self, "dashboard_kpi_font_ayarla"):
                self.dashboard_kpi_font_ayarla()
            if hasattr(self, "lblToplamCari"):
                self.lblToplamCari.setText(str(toplam_cari))
            if hasattr(self, "lblTahsilatAlarmi"):
                if borclular:
                    satirlar = [f"{ad or '-'}: {para_yaz(float(bakiye or 0))}" for ad, bakiye in borclular]
                    self.lblTahsilatAlarmi.setText("Tahsilat Alarmı\n" + "\n".join(satirlar))
                else:
                    self.lblTahsilatAlarmi.setText("Tahsilat Alarmı\nBorçlu cari yok")
            if hasattr(self, "lblBildirimKritikStok"):
                self.lblBildirimKritikStok.setText(f"Kritik Stok\n{kritik} ürün")
            if hasattr(self, "lblBildirimVade"):
                self.lblBildirimVade.setText(f"Açık Alacak\n{para_yaz(acik_alacak)}")
            if hasattr(self, "lblBildirimTeklif"):
                self.lblBildirimTeklif.setText(f"Bekleyen Teklif\n{bekleyen_teklif}")

            def tablo_doldur(tbl, rows):
                tbl.setRowCount(0)
                for r, row in enumerate(rows):
                    tbl.insertRow(r)
                    for c, value in enumerate(row):
                        item = QTableWidgetItem(str(value if value is not None else "-"))
                        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                        tbl.setItem(r, c, item)

            if hasattr(self, "tblDashboardSonSatislar"):
                tablo_doldur(self.tblDashboardSonSatislar, [(str(t)[:16], cari, belge, para_yaz(float(toplam or 0))) for t, cari, belge, toplam in son_satislar])
            if hasattr(self, "tblDashboardKritikStok"):
                tablo_doldur(self.tblDashboardKritikStok, [(ad, f"{float(stok or 0):g}", para_yaz(float(fiyat or 0))) for ad, stok, fiyat in kritik_stoklar])
            if hasattr(self, "tblDashboardCokSatan"):
                tablo_doldur(self.tblDashboardCokSatan, [(urun or "-", f"{float(adet or 0):g}", para_yaz(float(toplam or 0))) for urun, adet, toplam in cok_satanlar])
            if hasattr(self, "tblDashboardSonIslemler"):
                tablo_doldur(self.tblDashboardSonIslemler, [(str(t)[:16], tip, aciklama, para_yaz(float(tutar or 0))) for t, tip, aciklama, tutar in son_islemler])
            if hasattr(self, "lblSonSatislarOzet"):
                if son_satislar:
                    self.lblSonSatislarOzet.setText("Son satışlar\n" + "\n".join([f"{str(t)[:10]} • {cari or '-'} • {para_yaz(float(toplam or 0))}" for t, cari, belge, toplam in son_satislar[:3]]))
                else:
                    self.lblSonSatislarOzet.setText("Son satışlar\nHenüz satış yok")
            if hasattr(self, "lblKritikStokOzetPanel"):
                if kritik_stoklar:
                    self.lblKritikStokOzetPanel.setText("Kritik stoklar\n" + "\n".join([f"{ad or '-'} • Stok: {float(stok or 0):g}" for ad, stok, fiyat in kritik_stoklar[:3]]))
                else:
                    self.lblKritikStokOzetPanel.setText("Kritik stoklar\nKritik seviyede ürün yok")
            if hasattr(self, "lblCokSatanOzetPanel"):
                if cok_satanlar:
                    self.lblCokSatanOzetPanel.setText("En çok satanlar\n" + "\n".join([f"{urun or '-'} • {float(adet or 0):g} adet" for urun, adet, toplam in cok_satanlar[:3]]))
                else:
                    self.lblCokSatanOzetPanel.setText("En çok satanlar\nHenüz satış yok")
            if hasattr(self, "lblSonIslemOzet"):
                if son_islemler:
                    satirlar = []
                    for t, tip, aciklama, tutar in son_islemler[:4]:
                        satirlar.append(f"{str(t)[:16]}  •  {tip or '-'}  •  {para_yaz(float(tutar or 0))}")
                    self.lblSonIslemOzet.setText("\n".join(satirlar))
                else:
                    self.lblSonIslemOzet.setText("Henüz işlem yok")

            if hasattr(self, "lblDashboardTopMusteriler"):
                if top_musteriler:
                    satirlar = []
                    for i, (cari, toplam, islem_sayisi) in enumerate(top_musteriler[:10], start=1):
                        satirlar.append(f"{i}. {cari or '-'}  •  {para_yaz(float(toplam or 0))}  •  {int(islem_sayisi or 0)} işlem")
                    self.lblDashboardTopMusteriler.setText("\n".join(satirlar))
                else:
                    self.lblDashboardTopMusteriler.setText("Henüz satış verisi yok")

            if hasattr(self, "lblCokSatan"):
                if cok_satanlar:
                    satirlar = [f"{urun or '-'}: {float(adet or 0):g} adet" for urun, adet, toplam in cok_satanlar]
                    self.lblCokSatan.setText("En Çok Satan\n" + "\n".join(satirlar))
                else:
                    self.lblCokSatan.setText("En Çok Satan\nHenüz satış yok")
        except Exception as hata:
            try:
                log_yaz(f"Dashboard ek bilgileri yüklenemedi: {hata}")
            except Exception:
                pass

    def global_arama_yap(self):
        """Üst bardaki global arama: cari/stok sayfasına yönlendirir ve filtreyi uygular."""
        arama = self.txtGlobalArama.text().strip() if hasattr(self, "txtGlobalArama") else ""
        if not arama:
            return
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                like = f"%{arama}%"
                cur.execute("SELECT COUNT(*) FROM cariler WHERE COALESCE(aktif,1)=1 AND (ad LIKE ? OR telefon LIKE ? OR adres LIKE ? OR vergi_no LIKE ?)", (like, like, like, like))
                cari_sayisi = int(cur.fetchone()[0] or 0)
                cur.execute("""
                    SELECT COUNT(*)
                    FROM urunler u
                    LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                    WHERE u.ad LIKE ? OR g.ad LIKE ?
                """, (like, like))
                urun_sayisi = int(cur.fetchone()[0] or 0)
        except Exception as hata:
            QMessageBox.warning(self, "Arama", f"Arama yapılamadı:\n{hata}")
            return

        if cari_sayisi >= urun_sayisi and cari_sayisi > 0:
            self.sayfa_goster("cari")
            if hasattr(self, "txtCariSayfaAra"):
                self.txtCariSayfaAra.setText(arama)
        elif urun_sayisi > 0:
            self.sayfa_goster("stok")
            if hasattr(self, "txtStokAra"):
                self.txtStokAra.setText(arama)
        else:
            QMessageBox.information(self, "Arama", "Cari veya ürün bulunamadı.")

    def durum_cubugu_guncelle(self):
        if not hasattr(self, "lblDurumCubugu"):
            return
        try:
            yedek_klasor = os.path.join(BASE_DIR, YEDEK_KLASOR_ADI)
            son = "yok"
            if os.path.isdir(yedek_klasor):
                dosyalar = [os.path.join(yedek_klasor, x) for x in os.listdir(yedek_klasor)]
                dosyalar = [x for x in dosyalar if os.path.isfile(x)]
                if dosyalar:
                    son_dosya = max(dosyalar, key=os.path.getmtime)
                    son = datetime.fromtimestamp(os.path.getmtime(son_dosya)).strftime("%d.%m.%Y %H:%M")
            kullanici = getattr(self, "aktif_kullanici", aktif_kullanici_getir())
            self.lblDurumCubugu.setText(f"DAL ERP Next v139  •  Veritabanı: Bağlı  •  Son yedek: {son}  •  Kullanıcı: {kullanici}")
        except Exception:
            kullanici = getattr(self, "aktif_kullanici", "")
            self.lblDurumCubugu.setText(f"DAL ERP Next v139  •  Veritabanı: Bağlı  •  Kullanıcı: {kullanici}")

