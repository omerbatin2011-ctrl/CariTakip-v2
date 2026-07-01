
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QLabel

from moduller.ui_theme import apply_theme, normalize_inline_styles

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

class AnaPencereThemeMixin:
    def _temaya_gore_inline_stilleri_temizle(self):
        """v145: Eski sürümlerden kalan sabit beyaz/koyu inline stilleri temizler.

        Qt'de widget.setStyleSheet(...) ile verilen stil, uygulama genelindeki temadan
        daha baskındır. Bu yüzden koyu temada bazı alanlar beyaz kalabiliyordu ve
        koyu -> açık geçişinde bazı kontroller eski rengini koruyabiliyordu.
        """
        try:
            from PySide6.QtWidgets import (
                QComboBox,
                QDateEdit,
                QDoubleSpinBox,
                QFrame,
                QLineEdit,
                QSpinBox,
                QTableView,
                QTableWidget,
                QTextEdit,
                QWidget,
            )
            temizlenecek_siniflar = (QFrame, QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTableWidget, QTableView)
            renk_kalintilari = (
                '#FFFFFF', '#ffffff', 'white', '#F8FAFC', '#f8fafc', '#F5F7FA',
                '#0F172A', '#111827', '#1E293B', '#334155', '#475569'
            )
            guvenli_object_names = {
                'ERPPage', 'TopBar', 'MainCard', 'PanelCard', 'InfoCard', 'FormCard',
                'ThemePanel', 'NextContentShell', 'NextTopBar', 'NextStatusBar',
                'GlobalSearch', 'TahsilatSelectedCari', 'MetricCard', 'QuickButton',
                'StatusCard', 'ERPPanel', 'ERPStatCard', 'ERPToolbar'
            }
            for w in self.findChildren(QWidget):
                try:
                    st = w.styleSheet() or ''
                    obj = w.objectName() or ''
                    if obj in guvenli_object_names or (isinstance(w, temizlenecek_siniflar) and any(x in st for x in renk_kalintilari)):
                        # Özel buton stilleri korunur; sadece tema ile çakışan alanlar temizlenir.
                        if w.__class__.__name__ != 'QPushButton':
                            w.setStyleSheet('')
                except Exception:
                    pass
        except Exception:
            pass

    def _temayi_yeniden_polisle(self):
        """v145: Tüm widget'ların yeni QSS stilini yeniden hesaplamasını sağlar."""
        try:
            from PySide6.QtWidgets import QApplication, QWidget
            app = QApplication.instance()
            widgets = []
            if app:
                widgets.extend(app.allWidgets())
            else:
                widgets.extend(self.findChildren(QWidget))
            for w in widgets:
                try:
                    w.style().unpolish(w)
                    w.style().polish(w)
                    w.update()
                except Exception:
                    pass
        except Exception:
            pass

    def tema_degistir(self, koyu=False):
        """Program genelinde açık/gece tema değiştirir ve seçimi kaydeder.

        v145: Koyu -> açık geçişi ve koyu temadaki beyaz alan kalıntıları düzeltildi.
        """
        self.koyu_tema_aktif = bool(koyu)
        self._temaya_gore_inline_stilleri_temizle()
        normalize_inline_styles(self)
        apply_theme(self, self.koyu_tema_aktif)
        try:
            QSettings("DAL", "DAL ERP").setValue("tema/koyu", self.koyu_tema_aktif)
            QSettings("DAL", "DAL ERP").sync()
        except Exception:
            pass
        try:
            if hasattr(self, 'btnTemaToggle'):
                # Önceki sürümlerden kalmış inline stil varsa temizle; renkleri global tema versin.
                self.btnTemaToggle.setStyleSheet('')
                self.btnTemaToggle.setText('☀' if self.koyu_tema_aktif else '🌙')
                self.btnTemaToggle.setToolTip('Açık temaya geç' if self.koyu_tema_aktif else 'Gece temasına geç')
                self.btnTemaToggle.setObjectName('ThemeToggleButton')
            if hasattr(self, 'txtGlobalArama'):
                self.txtGlobalArama.setStyleSheet('')
                self.txtGlobalArama.setObjectName('GlobalSearch')

            baslik_rengi = '#F8FAFC' if self.koyu_tema_aktif else '#1F2937'
            ikincil = '#CBD5E1' if self.koyu_tema_aktif else '#4F5F5A'
            ucuncul = '#94A3B8' if self.koyu_tema_aktif else '#6B7C77'
            if hasattr(self, 'lblDashboardBaslik'):
                self.lblDashboardBaslik.setStyleSheet(f"font-size:24px;font-weight:900;color:{baslik_rengi};background:transparent;")
            if hasattr(self, 'lblFirmaAltBilgi'):
                self.lblFirmaAltBilgi.setStyleSheet(f"font-size:12px;color:{ikincil};font-weight:700;background:transparent;")
            try:
                for lbl in self.findChildren(QLabel):
                    ad = lbl.objectName()
                    if ad == 'MetricTitle':
                        lbl.setStyleSheet(f"font-size:12px;color:{ikincil};font-weight:800;background:transparent;")
                    elif ad == 'MetricValue':
                        lbl.setStyleSheet(f"font-size:19px;color:{baslik_rengi};font-weight:900;background:transparent;")
                    elif ad == 'MetricSub':
                        lbl.setStyleSheet(f"font-size:10px;color:{ucuncul};background:transparent;")
            except Exception:
                pass
            if hasattr(self, 'lblDurumCubugu'):
                tema = 'Gece Tema' if self.koyu_tema_aktif else 'Açık Tema'
                renk = '#CBD5E1' if self.koyu_tema_aktif else '#64748B'
                self.lblDurumCubugu.setText(f'DAL ERP Next v145    Tema: {tema}    Veritabanı: Bağlı    Kullanıcı: admin')
                self.lblDurumCubugu.setStyleSheet(f"background:transparent;border:none;padding:4px 2px;color:{renk};font-size:11px;font-weight:700;")
            normalize_inline_styles(self)
            self._temayi_yeniden_polisle()
        except Exception:
            pass

    def tema_toggle(self):
        self.tema_degistir(not bool(getattr(self, 'koyu_tema_aktif', False)))

