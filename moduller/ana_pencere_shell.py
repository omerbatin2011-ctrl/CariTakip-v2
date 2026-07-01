import time

from PySide6.QtWidgets import QMessageBox

from moduller.next_shell import set_page_title
from moduller.ui_theme import apply_theme, normalize_inline_styles
from moduller.yetki import yetki_var_mi

try:
    from kur_modulu import tcmb_usd_kuru_al, tl_karsiligi_hesapla
except Exception:
    tcmb_usd_kuru_al = None
    def tl_karsiligi_hesapla(tutar, para_birimi="TL", kur=1):
        try:
            tutar = float(tutar or 0)
            kur = float(kur or 1)
        except Exception:
            return 0.0
        return tutar if str(para_birimi).upper() == "TL" else tutar * kur

class AnaPencereShellMixin:
    def resizeEvent(self, event):
        """v76: Pencere boyutuna göre sidebar ve dashboard alanını otomatik rahatlatır."""
        try:
            w = self.width()
            if hasattr(self, "sidebar") and not getattr(self, "sidebar_collapsed", False):
                if w < 980:
                    self.sidebar_daralt_genislet()
                elif w < 1200:
                    self.sidebar.setMinimumWidth(226)
                    self.sidebar.setMaximumWidth(236)
                elif w < 1500:
                    self.sidebar.setMinimumWidth(238)
                    self.sidebar.setMaximumWidth(252)
                else:
                    self.sidebar.setMinimumWidth(248)
                    self.sidebar.setMaximumWidth(268)
            if hasattr(self, "dashboard_reflow"):
                self.dashboard_reflow()
            if hasattr(self, "lblDurumCubugu"):
                self.lblDurumCubugu.setWordWrap(w < 1300)
        except Exception:
            pass
        return super().resizeEvent(event)

    def sidebar_daralt_genislet(self):
        """Sol menüyü küçük ekranlar için 70px ikon moduna alır / geri açar."""
        self.sidebar_collapsed = not getattr(self, "sidebar_collapsed", False)
        if self.sidebar_collapsed:
            self.sidebar.setMinimumWidth(72)
            self.sidebar.setMaximumWidth(72)
            if hasattr(self, "lblFirmaAdi"):
                self.lblFirmaAdi.setVisible(False)
            if hasattr(self, "lblFirmaAltSidebar"):
                self.lblFirmaAltSidebar.setVisible(False)
            if getattr(self, "btnSidebarToggle", None):
                self.btnSidebarToggle.setText("☰")
            for lbl in getattr(self, "sidebar_grup_basliklari", []):
                lbl.setVisible(False)
            for btn, _ in getattr(self, "sidebar_butonlari", []):
                full = btn.property("full_text") or btn.text() or ""
                btn.setProperty("full_text", full)
                btn.setText(full.strip().split()[0] if full.strip() else "•")
                btn.setToolTip(full)  # ikon modunda tooltip açık
            if hasattr(self, "lblSidebarFooter"):
                self.lblSidebarFooter.setVisible(False)
            if hasattr(self, "btnYardim"):
                self.btnYardim.setText("?")
                self.btnYardim.setToolTip("Yardım")
            if hasattr(self, "btnCikis"):
                self.btnCikis.setText("↪")
                self.btnCikis.setToolTip("Çıkış")
        else:
            self.sidebar.setMinimumWidth(248)
            self.sidebar.setMaximumWidth(268)
            if hasattr(self, "lblFirmaAdi"):
                self.lblFirmaAdi.setVisible(True)
            if hasattr(self, "lblFirmaAltSidebar"):
                self.lblFirmaAltSidebar.setVisible(True)
            if getattr(self, "btnSidebarToggle", None):
                self.btnSidebarToggle.setText("☰")
            for lbl in getattr(self, "sidebar_grup_basliklari", []):
                lbl.setVisible(True)
            for btn, _ in getattr(self, "sidebar_butonlari", []):
                btn.setText(btn.property("full_text") or btn.text())
            if hasattr(self, "lblSidebarFooter"):
                self.lblSidebarFooter.setVisible(True)
            if hasattr(self, "btnYardim"):
                self.btnYardim.setText("?  Yardım")
                self.btnYardim.setToolTip("")
            if hasattr(self, "btnCikis"):
                self.btnCikis.setText(self.btnCikis.property("full_text") or "↪  Çıkış")
                self.btnCikis.setToolTip("")

    def sayfa_goster(self, sayfa_adi):
        """Sol menüden sayfa değiştirir. v147: lazy sayfa + hafif yenileme."""
        if not hasattr(self, "stack") or sayfa_adi not in self.sayfalar:
            return
        if not yetki_var_mi(sayfa_adi, "goruntule", getattr(self, "aktif_kullanici", None)):
            QMessageBox.warning(self, "Yetki Yok", "Bu ekranı görüntüleme yetkiniz yok.")
            return

        yeni_olustu = False
        sayfa_widget = self.sayfalar[sayfa_adi]
        if str(sayfa_widget.objectName()).startswith("LazyPage_"):
            fabrika = getattr(self, "sayfa_fabrikalari", {}).get(sayfa_adi)
            if fabrika:
                yeni_widget = fabrika()
                index = self.stack.indexOf(sayfa_widget)
                self.stack.removeWidget(sayfa_widget)
                sayfa_widget.deleteLater()
                self.stack.insertWidget(index, yeni_widget)
                self.sayfalar[sayfa_adi] = yeni_widget
                sayfa_widget = yeni_widget
                yeni_olustu = True

        if self.stack.currentWidget() is sayfa_widget and not yeni_olustu:
            return

        self.stack.setCurrentWidget(sayfa_widget)
        set_page_title(self, sayfa_adi)
        for btn, ad in getattr(self, "sidebar_butonlari", []):
            if ad:
                yeni_ad = "SidebarActive" if ad == sayfa_adi else "SidebarButton"
                if btn.objectName() != yeni_ad:
                    btn.setObjectName(yeni_ad)
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)

        # Sayfa yenilemeleri pahalı olabiliyor. Aynı ekrana kısa sürede tekrar
        # dönülürse veriyi yeniden çekme; bu menü geçişlerini hissedilir hızlandırır.
        now = time.time()
        sonlar = getattr(self, "_sayfa_son_yenileme", {})
        yenile = yeni_olustu or (now - float(sonlar.get(sayfa_adi, 0)) > 15.0)
        if yenile:
            if sayfa_adi == "dashboard":
                self.ozet_yukle()
            elif sayfa_adi == "cari":
                self.cari_sayfa_yenile()
            elif sayfa_adi == "stok":
                self.stok_sayfa_yenile()
            elif sayfa_adi == "tahsilat":
                self.tahsilat_sayfa_yenile()
            elif sayfa_adi == "raporlar":
                self.raporlar_sayfa_yenile()
            elif sayfa_adi == "kasa" and hasattr(self, "kasa_sayfa_yenile"):
                self.kasa_sayfa_yenile()
            elif sayfa_adi == "teklifler" and hasattr(self, "teklifler_sayfa_yenile"):
                self.teklifler_sayfa_yenile()
            elif sayfa_adi == "siparis" and hasattr(self, "siparis_sayfa_yenile"):
                self.siparis_sayfa_yenile()
            elif sayfa_adi == "satin_alma" and hasattr(self, "satin_alma_sayfa_yenile"):
                self.satin_alma_sayfa_yenile()
            elif sayfa_adi == "kar_zarar" and hasattr(self, "kar_zarar_sayfa_yenile"):
                self.kar_zarar_sayfa_yenile()
            elif sayfa_adi == "bildirimler" and hasattr(self, "bildirim_sayfa_yenile"):
                self.bildirim_sayfa_yenile()
            sonlar[sayfa_adi] = now
            self._sayfa_son_yenileme = sonlar

        # Tüm uygulamaya tema tekrar basmak menü geçişlerinde yavaşlık yapıyordu.
        # Sadece yeni oluşturulan sayfada bir kere uygula.
        if yeni_olustu:
            try:
                normalize_inline_styles(sayfa_widget)
                apply_theme(sayfa_widget, getattr(self, "koyu_tema_aktif", False))
            except Exception:
                pass

