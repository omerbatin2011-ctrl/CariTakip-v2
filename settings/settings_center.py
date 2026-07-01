from PySide6.QtWidgets import QFrame, QLabel, QTabWidget, QVBoxLayout, QWidget


def _page(title, lines):
    frame = QFrame()
    frame.setObjectName("MainCard")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    lbl = QLabel(title)
    lbl.setObjectName("CardTitle")
    lay.addWidget(lbl)
    for text in lines:
        item = QLabel(text)
        item.setWordWrap(True)
        item.setObjectName("DialogSubtitle")
        lay.addWidget(item)
    lay.addStretch(1)
    return frame


def build_settings_center(parent_app=None):
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setContentsMargins(0, 0, 0, 0)
    tabs = QTabWidget()
    tabs.addTab(_page("Genel Ayarlar", ["Firma bilgileri, para birimi, varsayılan çalışma tercihleri."]), "Genel")
    tabs.addTab(_page("Tema", ["Açık/Koyu tema seçimi ve arayüz tercihleri burada yönetilecek."]), "Tema")
    tabs.addTab(_page("Kullanıcılar", ["Kullanıcı, rol ve yetki altyapısı sonraki sürümlerde bu sekmeye taşınacak."]), "Kullanıcılar")
    tabs.addTab(_page("Yedekleme", ["Otomatik yedekleme, yedek klasörü ve geri yükleme işlemleri."]), "Yedekleme")
    tabs.addTab(_page("Veritabanı", ["Bakım, optimizasyon ve bağlantı bilgileri."]), "Veritabanı")
    tabs.addTab(_page("Lisans", ["Lisans durumu, sürüm bilgisi ve güncelleme kontrolleri."]), "Lisans")
    lay.addWidget(tabs, 1)
    return root
