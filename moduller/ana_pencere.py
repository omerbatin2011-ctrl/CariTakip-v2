from PySide6.QtWidgets import QWidget

from core.config import DB_ADI
from core.validators import telefon_gecerli_mi as ortak_telefon_gecerli_mi
from core.validators import tutar_oku as ortak_tutar_oku
from moduller.ana_pencere_async import AnaPencereAsyncMixin
from moduller.ana_pencere_kurulum import ana_pencereyi_kur
from moduller.ana_pencere_lifecycle import AnaPencereLifecycleMixin
from moduller.ana_pencere_rapor import AnaPencereRaporMixin
from moduller.ana_pencere_session import AnaPencereSessionMixin
from moduller.ana_pencere_shell import AnaPencereShellMixin
from moduller.ana_pencere_theme import AnaPencereThemeMixin
from moduller.ayarlar_ui import AyarlarMixin
from moduller.barkotlu_satis_ui import BarkodluSatisMixin
from moduller.cari_islemler import CariIslemlerMixin
from moduller.cari_ui import CariMixin
from moduller.dashboard_logic import DashboardMixin
from moduller.db import db_ayarla
from moduller.erp_ek_ui import ErpEkMixin
from moduller.kasa_ui import KasaMixin
from moduller.raporlar_ui import RaporlarMixin
from moduller.satis_ui import SatisMixin
from moduller.stok_ui import StokMixin
from moduller.tahsilat_ui import TahsilatMixin
from moduller.teklif_ui import TeklifMixin
from moduller.urun_stok_islemler import UrunStokIslemlerMixin
from moduller.yedekleme_ui import YedeklemeMixin

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

class DashboardDetayMixin:
    """Dashboard detay pencerelerini ihtiyaç anında yükler.

    V42: dashboard_detay_pencereleri ve grafik bağımlılıkları uygulama açılışında
    yüklenmesin
    kullanıcı detay/grafik/rapor penceresi açınca import edilsin.
    """

    def _dashboard_detay_impl(self):
        from moduller.dashboard_detay_pencereleri import DashboardDetayMixin as _Impl
        return _Impl

    def _detay_pencere_olustur(self, *args, **kwargs):
        return self._dashboard_detay_impl()._detay_pencere_olustur(self, *args, **kwargs)

    def dashboard_grafik_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_grafik_penceresi_ac(self, *args, **kwargs)

    def _tablo_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl()._tablo_penceresi_ac(self, *args, **kwargs)

    def dashboard_son_islemler_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_son_islemler_penceresi_ac(self, *args, **kwargs)

    def dashboard_son_satislar_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_son_satislar_penceresi_ac(self, *args, **kwargs)

    def dashboard_kritik_stok_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_kritik_stok_penceresi_ac(self, *args, **kwargs)

    def dashboard_cok_satanlar_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_cok_satanlar_penceresi_ac(self, *args, **kwargs)

    def dashboard_rapor_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_rapor_penceresi_ac(self, *args, **kwargs)

    def dashboard_ayarlar_penceresi_ac(self, *args, **kwargs):
        return self._dashboard_detay_impl().dashboard_ayarlar_penceresi_ac(self, *args, **kwargs)




db_ayarla(DB_ADI)






# Ana pencere sınıfı main.py içinden ayrıldı.
# Bu dosya uygulama iskeletini, sidebar/stack yönetimini ve eski gömülü metotları barındırır.

class AnaPencere(AnaPencereAsyncMixin, AnaPencereThemeMixin, AnaPencereShellMixin, AnaPencereSessionMixin, AnaPencereRaporMixin, AnaPencereLifecycleMixin, DashboardMixin, DashboardDetayMixin, CariMixin, CariIslemlerMixin, StokMixin, UrunStokIslemlerMixin, TahsilatMixin, RaporlarMixin, SatisMixin, BarkodluSatisMixin, KasaMixin, AyarlarMixin, YedeklemeMixin, TeklifMixin, ErpEkMixin, QWidget):

    @staticmethod
    def tutar_oku(metin, varsayilan=None):
        return ortak_tutar_oku(metin, varsayilan)

    @staticmethod
    def telefon_gecerli_mi(telefon):
        return ortak_telefon_gecerli_mi(telefon)

    def __init__(self):
        super().__init__()
        ana_pencereyi_kur(self)
