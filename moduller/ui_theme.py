LIGHT_STYLE = """
QWidget {
    background: #F8FAFC;
    font-size: 13px;
    color: #0F172A;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
QLabel { color: #0F172A; background: transparent; }
QDialog, QMainWindow, QScrollArea, QTabWidget::pane { background: #F8FAFC; border: none; }
QScrollArea { border: none; }
QScrollArea#SidebarNavScroll, QWidget#SidebarNavContainer { background: transparent; border: none; }
QScrollArea#SidebarNavScroll QScrollBar:vertical { background: transparent; width: 6px; margin: 2px 0px 2px 2px; }
QScrollArea#SidebarNavScroll QScrollBar::handle:vertical { background: #CBD5E1; min-height: 24px; border-radius: 3px; }
QScrollArea#SidebarNavScroll QScrollBar::add-line:vertical, QScrollArea#SidebarNavScroll QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:vertical { background: #EEF2F7; width: 10px; margin: 2px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #CBD5E1; min-height: 26px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #94A3B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QFrame#Sidebar { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
QFrame#TopBar { background: transparent; border: none; }
QFrame#MetricCard, QFrame#MainCard, QFrame#QuickButton, QFrame#StatusCard,
QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
}
QFrame#MetricCard:hover, QFrame#QuickButton:hover { border: 1px solid #93C5FD; }

QPushButton {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 7px 11px;
    font-weight: 700;
    text-align: center;
    min-height: 34px;
}
QPushButton:hover { background: #F8FAFC; border: 1px solid #CBD5E1; }
QPushButton:pressed { background: #E2E8F0; }
QPushButton:disabled { color: #94A3B8; background: #F8FAFC; border-color: #E2E8F0; }
QPushButton#PrimaryButton { background: #2563EB; color: white; border: none; }
QPushButton#PrimaryButton:hover { background: #1D4ED8; }
QPushButton#GreenButton  { background: #059669; color: white; border: none; }
QPushButton#GreenButton:hover { background: #047857; }
QPushButton#OrangeButton { background: #FFFFFF; color: #C2410C; border: 1px solid #FDBA74; }
QPushButton#OrangeButton:hover { background: #FFF7ED; }
QPushButton#PurpleButton { background: #FFFFFF; color: #6D28D9; border: 1px solid #DDD6FE; }
QPushButton#PurpleButton:hover { background: #F5F3FF; }
QPushButton#LightButton  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
QPushButton#GreyButton   { background: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; }

QPushButton#SidebarToggle {
    background: #FFFFFF;
    color: #2563EB;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    font-weight: 900;
    text-align: center;
}
QPushButton#SidebarToggle:hover { background: #EFF6FF; border-color: #93C5FD; }
QPushButton#SidebarButton, QPushButton#SidebarActive {
    text-align: left;
    min-height: 36px;
    max-height: 38px;
    border-radius: 9px;
    padding: 7px 12px;
}
QPushButton#SidebarButton {
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: #334155;
    font-weight: 700;
}
QPushButton#SidebarButton:hover { background: #EFF6FF; border-left: 3px solid #3B82F6; color: #1D4ED8; }
QPushButton#SidebarActive {
    background: #2563EB;
    border: none;
    border-left: 3px solid #60A5FA;
    color: #FFFFFF;
    font-weight: 900;
}
QPushButton#ExitButton {
    background: #FFFFFF;
    color: #1D4ED8;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    min-height: 36px;
    text-align: center;
    padding: 7px 10px;
}
QPushButton#ExitButton:hover { background: #EFF6FF; }

QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 7px 10px;
    color: #0F172A;
    min-height: 34px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus { border: 1px solid #2563EB; }
QTextEdit { max-height: none; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView { padding: 6px; outline: 0; }

QTabBar::tab { background: #FFFFFF; color: #475569; border: 1px solid #E2E8F0; border-bottom: none; padding: 8px 14px; border-top-left-radius: 10px; border-top-right-radius: 10px; font-weight: 800; }
QTabBar::tab:selected { background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE; }
QTabBar::tab:hover { background: #F8FAFC; }

QTableWidget, QTableView {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: #E2E8F0;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    alternate-background-color: #F8FAFC;
}
QTableWidget::item, QTableView::item { padding: 8px; border: none; outline: 0; }
QTableWidget::item:selected, QTableView::item:selected { background: #2563EB; color: #FFFFFF; border: none; outline: 0; }
QTableWidget::item:focus, QTableView::item:focus { border: none; outline: 0; }
QTableWidget:focus, QTableView:focus { border: 1px solid #E2E8F0; outline: 0; }
QHeaderView::section { background: #F8FAFC; color: #334155; border: none; padding: 7px; font-weight: 800; }

QMenu { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 6px; color: #0F172A; }
QMenu::item { padding: 7px 18px; border-radius: 7px; }
QMenu::item:selected { background: #EFF6FF; color: #1D4ED8; }
QToolTip { background: #0F172A; color: #FFFFFF; border: none; border-radius: 8px; padding: 6px 8px; }

/* v117 Fluent tema seçici ve modern detaylar */
QPushButton#ThemeToggleButton {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 8px 12px;
    font-weight: 900;
}
QPushButton#ThemeToggleButton:hover { background: #EFF6FF; border-color: #93C5FD; color: #1D4ED8; }
QFrame#ThemePanel {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 14px;
}
QLabel#ThemePanelTitle { color: #1E3A8A; font-weight: 900; }
QPushButton#ThemeChoiceButton {
    background: #FFFFFF;
    color: #1E3A8A;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    padding: 8px 14px;
    font-weight: 900;
    min-height: 34px;
}
QPushButton#ThemeChoiceButton:hover { background: #DBEAFE; border-color: #60A5FA; color: #1D4ED8; }
QPushButton#DashboardActionButton {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 10px 14px;
    font-weight: 900;
}
QPushButton#DashboardActionButton:hover { background: #F8FAFC; border-color:#93C5FD; color:#1D4ED8; }

/* v117 tasarım sistemi */
QDialog#ERPDialog { background:#F8FAFC; }
QLabel#DialogTitle { color:#0B1220; font-size:22px; font-weight:900; }
QLabel#DialogSubtitle { color:#64748B; font-size:12px; font-weight:700; }
QFrame#SectionHeader { background:transparent; border:none; }
QLabel#SectionTitle { color:#0B1220; font-size:16px; font-weight:900; }
QLabel#InfoTileTitle { color:#0B1220; font-size:12px; font-weight:900; }
QLabel#InfoTileText { color:#475569; font-size:12px; font-weight:700; }
QFrame#InfoTile_blue, QFrame#InfoTile_red, QFrame#InfoTile_green, QFrame#InfoTile_orange, QFrame#InfoTile_purple { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; }
QPushButton#ThemeChoiceButton { background:#FFFFFF; color:#0F172A; border:1px solid #93C5FD; }
QPushButton#ThemeChoiceButton:disabled { background:#DBEAFE; color:#1D4ED8; border:1px solid #60A5FA; }


/* v119 DAL ERP Next Shell */
QFrame#NextContentShell { background:#F8FAFC; border:none; }
QFrame#NextTopBar { background:#F8FAFC; border-bottom:1px solid #E2E8F0; }
QLabel#NextPageTitle { color:#0B1220; font-size:22px; font-weight:900; }
QLabel#NextPageSubtitle { color:#64748B; font-size:12px; font-weight:700; }
QLineEdit#GlobalSearch { background:#FFFFFF; color:#0F172A; border:1px solid #CBD5E1; border-radius:14px; padding:8px 14px; font-weight:800; min-height:38px; }
QLineEdit#GlobalSearch:focus { border:1px solid #2563EB; background:#FFFFFF; }
QLabel#NextUserBadge { background:#FFFFFF; color:#0F172A; border:1px solid #E2E8F0; border-radius:14px; padding:8px 12px; font-weight:900; }
QFrame#NextStatusBar { background:#F8FAFC; border-top:1px solid #E2E8F0; }
QLabel#NextStatusLabel { background:transparent; color:#64748B; font-size:11px; font-weight:700; }

/* v120 Fluent Sidebar */
QFrame#Sidebar { background:#FFFFFF; border-right:1px solid #E2E8F0; }
QFrame#SidebarBrand { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:18px; }
QLabel#SidebarLogo { background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #2563EB, stop:1 #7C3AED); color:#FFFFFF; border-radius:14px; font-size:20px; font-weight:900; }
QLabel#SidebarBrandTitle { color:#0F172A; font-size:17px; font-weight:900; }
QLabel#SidebarBrandSubtitle { color:#64748B; font-size:11px; font-weight:800; }
QLabel#SidebarGroupTitle { color:#94A3B8; font-size:10px; font-weight:900; letter-spacing:1px; padding:9px 8px 3px 8px; }
QLabel#SidebarFooter { color:#64748B; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:7px; font-size:11px; font-weight:800; }
QPushButton#SidebarToggle { background:#FFFFFF; color:#2563EB; border:1px solid #E2E8F0; border-radius:12px; font-weight:900; }
QPushButton#SidebarToggle:hover { background:#EFF6FF; border-color:#93C5FD; }
QPushButton#SidebarButton, QPushButton#SidebarActive { text-align:left; min-height:40px; border-radius:13px; padding:8px 12px; font-size:13px; }
QPushButton#SidebarButton { background:transparent; border:1px solid transparent; color:#334155; font-weight:800; }
QPushButton#SidebarButton:hover { background:#EFF6FF; border:1px solid #BFDBFE; color:#1D4ED8; }
QPushButton#SidebarActive { background:#2563EB; border:1px solid #2563EB; color:#FFFFFF; font-weight:900; }
QPushButton#ExitButton { background:#FFFFFF; color:#1D4ED8; border:1px solid #CBD5E1; border-radius:13px; min-height:38px; font-weight:900; }
QPushButton#ExitButton:hover { background:#EFF6FF; border-color:#93C5FD; }


/* v124 UI polish */
QFrame#MetricCard {
    border-radius: 16px;
    background: #FFFFFF;
}
QFrame#MetricCard:hover {
    background: #FBFDFF;
    border: 1px solid #60A5FA;
}
QPushButton#DashboardActionButton {
    min-height: 38px;
    border-radius: 13px;
    font-weight: 900;
}
QFrame#MainCard { border-radius: 16px; }
QLabel#MetricTitle { color:#334155; font-weight:900; }
QLabel#MetricValue { color:#020617; font-weight:900; }
QLabel#MetricSub { color:#64748B; font-weight:700; }


/* v126 ERP Framework */
QWidget#ERPPage { background: transparent; }
QFrame#ERPPanel, QFrame#ERPStatCard, QFrame#ERPToolbar {
    background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px;
}
QFrame#ERPStatCard:hover { background:#F8FAFC; border:1px solid #93C5FD; }
QLabel#ERPPanelTitle, QLabel#ERPToolbarTitle { color:#0F172A; font-size:15px; font-weight:900; }
QLabel#ERPStatTitle { color:#334155; font-size:12px; font-weight:900; }
QLabel#ERPStatValue { color:#020617; font-size:20px; font-weight:900; }
QLabel#ERPStatSubtitle { color:#64748B; font-size:10px; font-weight:800; }
QPushButton#ERPButton, QPushButton#ERPPrimaryButton {
    border-radius:12px; padding:8px 12px; font-weight:900; min-height:38px;
}
QPushButton#ERPButton { background:#FFFFFF; color:#0F172A; border:1px solid #E2E8F0; }
QPushButton#ERPButton:hover { background:#EFF6FF; border-color:#93C5FD; color:#1D4ED8; }
QPushButton#ERPPrimaryButton { background:#2563EB; color:#FFFFFF; border:1px solid #2563EB; }
QPushButton#ERPPrimaryButton:hover { background:#1D4ED8; border-color:#1D4ED8; }

/* v140 okunabilirlik düzeltmeleri */
QFrame#TopBar { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; }
QWidget#ERPPage { background:#F8FAFC; color:#0F172A; }
QLabel#PageHeroTitle { color:#0F172A; font-size:24px; font-weight:900; background:transparent; }
QLabel#FormSectionLabel { color:#64748B; font-size:12px; font-weight:800; background:transparent; }
QLabel#TahsilatSelectedCari { color:#0F172A; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:12px; font-size:15px; font-weight:900; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox { placeholder-text-color:#94A3B8; }
QPushButton:disabled { color:#64748B; background:#F1F5F9; border:1px solid #CBD5E1; }


/* v140 Theme Engine Fix - açık tema dönüşü */
QWidget#ERPPage, QFrame#NextContentShell, QFrame#NextTopBar, QFrame#NextStatusBar,
QScrollArea, QScrollArea > QWidget, QStackedWidget, QTabWidget::pane {
    background:#F8FAFC;
    color:#0F172A;
}
QFrame#MainCard, QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard, QFrame#TopBar,
QFrame#ERPPanel, QFrame#ERPToolbar, QFrame#ERPStatCard, QFrame#ThemePanel {
    background:#FFFFFF;
    border:1px solid #E2E8F0;
    border-radius:14px;
    color:#0F172A;
}
QLabel { color:#0F172A; background:transparent; }
QPushButton#ThemeToggleButton {
    background:#FFFFFF;
    color:#0F172A;
    border:1px solid #CBD5E1;
    border-radius:12px;
    font-weight:900;
}
QPushButton#ThemeToggleButton:hover { background:#EFF6FF; border-color:#93C5FD; color:#1D4ED8; }

"""

DARK_STYLE = """
QWidget {
    background: #0F172A;
    font-size: 13px;
    color: #E2E8F0;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
QLabel { color: #E2E8F0; background: transparent; }
QDialog, QMainWindow, QScrollArea, QTabWidget::pane { background: #0F172A; border: none; }
QScrollArea { border: none; }
QScrollArea#SidebarNavScroll, QWidget#SidebarNavContainer { background: transparent; border: none; }
QScrollArea#SidebarNavScroll QScrollBar:vertical { background: transparent; width: 6px; margin: 2px 0px 2px 2px; }
QScrollArea#SidebarNavScroll QScrollBar::handle:vertical { background: #CBD5E1; min-height: 24px; border-radius: 3px; }
QScrollArea#SidebarNavScroll QScrollBar::add-line:vertical, QScrollArea#SidebarNavScroll QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:vertical { background: #111827; width: 10px; margin: 2px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #475569; min-height: 26px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #64748B; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QFrame#Sidebar { background: #1E293B; border-right: 1px solid #334155; }
QFrame#TopBar, QFrame#MetricCard, QFrame#MainCard, QFrame#QuickButton, QFrame#StatusCard,
QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 14px;
}
QFrame#MetricCard:hover, QFrame#QuickButton:hover { border: 1px solid #6366F1; }

QPushButton {
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 7px 11px;
    font-weight: 700;
    text-align: center;
    min-height: 34px;
}
QPushButton:hover { background: #334155; border: 1px solid #475569; }
QPushButton:pressed { background: #475569; }
QPushButton:disabled { color: #64748B; background: #111827; border-color: #334155; }

QPushButton#PrimaryButton { background: #6366F1; color: white; border: none; }
QPushButton#PrimaryButton:hover { background: #4F46E5; }
QPushButton#GreenButton  { background: #16A34A; color: white; border: none; }
QPushButton#OrangeButton { background: #EA580C; color: white; border: none; }
QPushButton#PurpleButton { background: #9333EA; color: white; border: none; }
QPushButton#LightButton  { background: #1E3A8A; color: #DBEAFE; border: 1px solid #2563EB; }
QPushButton#GreyButton   { background: #334155; color: #E2E8F0; border: 1px solid #475569; }

QPushButton#SidebarButton, QPushButton#SidebarActive {
    text-align: left;
    min-height: 34px;
    border-radius: 10px;
    padding: 6px 9px;
}
QPushButton#SidebarButton {
    background: transparent;
    border: none;
    border-left: 4px solid transparent;
    color: #CBD5E1;
    font-weight: 800;
}
QPushButton#SidebarButton:hover { background: #1E293B; border-left: 4px solid #475569; color: #F8FAFC; }
QPushButton#SidebarActive { background: #312E81; border: none; border-left: 4px solid #6366F1; color: #E0E7FF; font-weight: 900; }
QPushButton#ExitButton { background: #334155; color: #F8FAFC; border: none; border-radius: 10px; min-height: 34px; max-height: 40px; text-align: center; padding: 7px 10px; }
QPushButton#ExitButton:hover { background: #475569; }

QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 7px 10px;
    color: #E2E8F0;
    min-height: 34px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus { border: 1px solid #3B82F6; }
QTextEdit { max-height: none; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox QAbstractItemView { padding: 6px; outline: 0; }

QTabBar::tab {
    background: #111827;
    color: #CBD5E1;
    border: 1px solid #334155;
    border-bottom: none;
    padding: 8px 14px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 800;
}
QTabBar::tab:selected { background: #312E81; color: #E0E7FF; border-color: #6366F1; }
QTabBar::tab:hover { background: #1E293B; }

QTableWidget, QTableView {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    gridline-color: #334155;
    selection-background-color: #3B82F6;
    selection-color: #FFFFFF;
    alternate-background-color: #1F2937;
}
QTableWidget::item, QTableView::item { padding: 8px; border: none; outline: 0; }
QTableWidget::item:selected, QTableView::item:selected { background: #3B82F6; color: #FFFFFF; border: none; outline: 0; }
QTableWidget::item:focus, QTableView::item:focus { border: none; outline: 0; }
QTableWidget:focus, QTableView:focus { border: 1px solid #E2E8F0; outline: 0; }
QHeaderView::section { background: #1E293B; color: #E2E8F0; border: none; padding: 7px; font-weight: 800; }

QMenu { background: #111827; border: 1px solid #334155; border-radius: 10px; padding: 6px; color: #E2E8F0; }
QMenu::item { padding: 7px 18px; border-radius: 7px; }
QMenu::item:selected { background: #312E81; color: #E0E7FF; }
QToolTip { background: #F8FAFC; color: #0F172A; border: none; border-radius: 8px; padding: 6px 8px; }

/* v117 Fluent tema seçici ve modern detaylar */
QPushButton#ThemeToggleButton {
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #475569;
    border-radius: 12px;
    padding: 8px 12px;
    font-weight: 900;
}
QPushButton#ThemeToggleButton:hover { background: #334155; border-color: #64748B; color: #FFFFFF; }
QFrame#ThemePanel {
    background: #111827;
    border: 1px solid #334155;
    border-radius: 14px;
}
QLabel#ThemePanelTitle { color: #E0E7FF; font-weight: 900; }
QPushButton#ThemeChoiceButton {
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #475569;
    border-radius: 12px;
    padding: 8px 14px;
    font-weight: 900;
    min-height: 34px;
}
QPushButton#ThemeChoiceButton:hover { background: #312E81; border-color: #6366F1; color: #FFFFFF; }
QPushButton#DashboardActionButton {
    background: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 10px 14px;
    font-weight: 900;
}
QPushButton#DashboardActionButton:hover { background: #312E81; border-color:#6366F1; color:#FFFFFF; }

/* v117 tasarım sistemi */
QDialog#ERPDialog { background:#0F172A; }
QLabel#DialogTitle { color:#F8FAFC; font-size:22px; font-weight:900; }
QLabel#DialogSubtitle { color:#94A3B8; font-size:12px; font-weight:700; }
QFrame#SectionHeader { background:transparent; border:none; }
QLabel#SectionTitle { color:#F8FAFC; font-size:16px; font-weight:900; }
QLabel#InfoTileTitle { color:#F8FAFC; font-size:12px; font-weight:900; }
QLabel#InfoTileText { color:#CBD5E1; font-size:12px; font-weight:700; }
QFrame#InfoTile_blue, QFrame#InfoTile_red, QFrame#InfoTile_green, QFrame#InfoTile_orange, QFrame#InfoTile_purple { background:#111827; border:1px solid #334155; border-radius:14px; }
QPushButton#ThemeChoiceButton { background:#1E293B; color:#E2E8F0; border:1px solid #475569; }
QPushButton#ThemeChoiceButton:disabled { background:#312E81; color:#FFFFFF; border:1px solid #6366F1; }


/* v119 DAL ERP Next Shell */
QFrame#NextContentShell { background:#0F172A; border:none; }
QFrame#NextTopBar { background:#0F172A; border-bottom:1px solid #334155; }
QLabel#NextPageTitle { color:#F8FAFC; font-size:22px; font-weight:900; }
QLabel#NextPageSubtitle { color:#CBD5E1; font-size:12px; font-weight:700; }
QLineEdit#GlobalSearch { background:#111827; color:#E2E8F0; border:1px solid #475569; border-radius:14px; padding:8px 14px; font-weight:800; min-height:38px; }
QLineEdit#GlobalSearch:focus { border:1px solid #60A5FA; background:#111827; }
QLabel#NextUserBadge { background:#111827; color:#E2E8F0; border:1px solid #334155; border-radius:14px; padding:8px 12px; font-weight:900; }
QFrame#NextStatusBar { background:#0F172A; border-top:1px solid #334155; }
QLabel#NextStatusLabel { background:transparent; color:#CBD5E1; font-size:11px; font-weight:700; }

/* v120 Fluent Sidebar */
QFrame#Sidebar { background:#111827; border-right:1px solid #334155; }
QFrame#SidebarBrand { background:#0F172A; border:1px solid #334155; border-radius:18px; }
QLabel#SidebarLogo { background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6366F1, stop:1 #A855F7); color:#FFFFFF; border-radius:14px; font-size:20px; font-weight:900; }
QLabel#SidebarBrandTitle { color:#F8FAFC; font-size:17px; font-weight:900; }
QLabel#SidebarBrandSubtitle { color:#CBD5E1; font-size:11px; font-weight:800; }
QLabel#SidebarGroupTitle { color:#64748B; font-size:10px; font-weight:900; letter-spacing:1px; padding:9px 8px 3px 8px; }
QLabel#SidebarFooter { color:#CBD5E1; background:#0F172A; border:1px solid #334155; border-radius:12px; padding:7px; font-size:11px; font-weight:800; }
QPushButton#SidebarToggle { background:#0F172A; color:#E0E7FF; border:1px solid #334155; border-radius:12px; font-weight:900; }
QPushButton#SidebarToggle:hover { background:#1E293B; border-color:#6366F1; }
QPushButton#SidebarButton, QPushButton#SidebarActive { text-align:left; min-height:40px; border-radius:13px; padding:8px 12px; font-size:13px; }
QPushButton#SidebarButton { background:transparent; border:1px solid transparent; color:#CBD5E1; font-weight:800; }
QPushButton#SidebarButton:hover { background:#1E293B; border:1px solid #475569; color:#F8FAFC; }
QPushButton#SidebarActive { background:#4F46E5; border:1px solid #6366F1; color:#FFFFFF; font-weight:900; }
QPushButton#ExitButton { background:#1E293B; color:#F8FAFC; border:1px solid #334155; border-radius:13px; min-height:38px; font-weight:900; }
QPushButton#ExitButton:hover { background:#334155; border-color:#475569; }


/* v124 UI polish */
QFrame#MetricCard { border-radius: 16px; background: #111827; }
QFrame#MetricCard:hover { background: #172033; border: 1px solid #818CF8; }
QPushButton#DashboardActionButton { min-height: 38px; border-radius: 13px; font-weight: 900; }
QFrame#MainCard { border-radius: 16px; }
QLabel#MetricTitle { color:#CBD5E1; font-weight:900; }
QLabel#MetricValue { color:#F8FAFC; font-weight:900; }
QLabel#MetricSub { color:#94A3B8; font-weight:700; }


/* v126 ERP Framework */
QWidget#ERPPage { background: transparent; }
QFrame#ERPPanel, QFrame#ERPStatCard, QFrame#ERPToolbar {
    background:#111827; border:1px solid #334155; border-radius:14px;
}
QFrame#ERPStatCard:hover { background:#172033; border:1px solid #818CF8; }
QLabel#ERPPanelTitle, QLabel#ERPToolbarTitle { color:#F8FAFC; font-size:15px; font-weight:900; }
QLabel#ERPStatTitle { color:#CBD5E1; font-size:12px; font-weight:900; }
QLabel#ERPStatValue { color:#F8FAFC; font-size:20px; font-weight:900; }
QLabel#ERPStatSubtitle { color:#94A3B8; font-size:10px; font-weight:800; }
QPushButton#ERPButton, QPushButton#ERPPrimaryButton {
    border-radius:12px; padding:8px 12px; font-weight:900; min-height:38px;
}
QPushButton#ERPButton { background:#0F172A; color:#E2E8F0; border:1px solid #334155; }
QPushButton#ERPButton:hover { background:#1E293B; border-color:#6366F1; color:#FFFFFF; }
QPushButton#ERPPrimaryButton { background:#4F46E5; color:#FFFFFF; border:1px solid #6366F1; }
QPushButton#ERPPrimaryButton:hover { background:#4338CA; border-color:#818CF8; }

/* v140 Dark Theme Complete - okunabilirlik düzeltmeleri */
QFrame#TopBar { background:#111827; border:1px solid #334155; border-radius:16px; }
QWidget#ERPPage { background:#0F172A; color:#F8FAFC; }
QLabel#PageHeroTitle { color:#F8FAFC; font-size:24px; font-weight:900; background:transparent; }
QLabel#FormSectionLabel { color:#CBD5E1; font-size:12px; font-weight:800; background:transparent; }
QLabel#TahsilatSelectedCari { color:#F8FAFC; background:#1E293B; border:1px solid #475569; border-radius:12px; padding:12px; font-size:15px; font-weight:900; }
QLabel { color:#E2E8F0; }
QLabel:disabled { color:#94A3B8; }
QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
    background:#111827;
    color:#F8FAFC;
    border:1px solid #475569;
    placeholder-text-color:#94A3B8;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border:1px solid #60A5FA;
    background:#0B1220;
}
QPushButton:disabled {
    color:#CBD5E1;
    background:#1E293B;
    border:1px solid #475569;
}
QTableWidget, QTableView {
    background:#0B1220;
    color:#F8FAFC;
    alternate-background-color:#111827;
    border:1px solid #475569;
    gridline-color:#334155;
}
QTableWidget::item, QTableView::item { color:#F8FAFC; }
QTableWidget::item:selected, QTableView::item:selected { background:#2563EB; color:#FFFFFF; }
QHeaderView::section { background:#1E293B; color:#F8FAFC; border-bottom:1px solid #475569; }
QFrame#MainCard, QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard {
    background:#111827;
    border:1px solid #475569;
}


/* v140 Theme Engine Fix - koyu temada beyaz ada bırakma */
QWidget#ERPPage, QWidget#SidebarNavContainer, QFrame#NextContentShell, QFrame#NextTopBar,
QFrame#NextStatusBar, QScrollArea, QScrollArea > QWidget, QStackedWidget, QTabWidget::pane {
    background:#0F172A;
    color:#F8FAFC;
}
QFrame, QGroupBox {
    background:#0F172A;
    color:#F8FAFC;
}
QFrame#MainCard, QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard, QFrame#TopBar,
QFrame#ERPPanel, QFrame#ERPToolbar, QFrame#ERPStatCard, QFrame#ThemePanel {
    background:#1E293B;
    border:1px solid #334155;
    border-radius:14px;
    color:#F8FAFC;
}
QGroupBox {
    border:1px solid #334155;
    border-radius:14px;
    margin-top:18px;
    padding:12px;
    font-weight:900;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left:12px;
    padding:0 6px;
    color:#F8FAFC;
    background:#0F172A;
}
QLabel { color:#E2E8F0; background:transparent; }
QLabel#FormSectionLabel, QLabel#DialogSubtitle, QLabel#NextPageSubtitle { color:#CBD5E1; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    background:#111827;
    color:#F8FAFC;
    border:1px solid #475569;
    border-radius:10px;
    selection-background-color:#2563EB;
    selection-color:#FFFFFF;
    placeholder-text-color:#94A3B8;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
    background:#0B1220;
    border:1px solid #60A5FA;
}
QTableWidget, QTableView {
    background:#0B1220;
    color:#F8FAFC;
    alternate-background-color:#111827;
    border:1px solid #475569;
    gridline-color:#334155;
}
QHeaderView::section { background:#1E293B; color:#F8FAFC; border-bottom:1px solid #475569; }
QPushButton#ThemeToggleButton {
    background:#1E293B;
    color:#F8FAFC;
    border:1px solid #475569;
    border-radius:12px;
    font-weight:900;
}
QPushButton#ThemeToggleButton:hover { background:#334155; border-color:#60A5FA; color:#FFFFFF; }

"""


def get_style(koyu: bool = False) -> str:
    return DARK_STYLE if koyu else LIGHT_STYLE


def apply_theme(widget=None, koyu: bool = False) -> None:
    """Tema stilini hem uygulamaya hem de verilen pencereye uygular."""
    style = get_style(koyu)
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style)
    except Exception:
        pass
    if widget is not None:
        try:
            widget.setStyleSheet(style)
        except Exception:
            pass

# v142 Tahsilat UX ek stilleri, mevcut temayı bozmayacak şekilde sonradan uygulanır.
TAHSILAT_UX_LIGHT = """
QSplitter#ERPSplitter::handle { background:#E2E8F0; margin:4px; border-radius:3px; }
QLabel#SectionTitle { color:#0F172A; font-size:15px; font-weight:900; }
QLabel#TahsilatInfoPill, QLabel#TahsilatMutedBadge {
    background:#EFF6FF;
    color:#1D4ED8;
    border:1px solid #BFDBFE;
    border-radius:12px;
    padding:7px 10px;
    font-weight:900;
}
QFrame#TahsilatFormCard {
    background:#F8FAFC;
    border:1px solid #E2E8F0;
    border-radius:14px;
}
QPushButton#CompactActionButton {
    background:#FFFFFF;
    color:#0F172A;
    border:1px solid #CBD5E1;
    border-radius:11px;
    padding:6px 10px;
    font-weight:900;
    min-height:36px;
}
QPushButton#CompactActionButton:hover { background:#EFF6FF; border-color:#93C5FD; color:#1D4ED8; }
QLabel#TahsilatHint { color:#64748B; font-size:12px; font-weight:700; padding:4px 2px; }
"""

TAHSILAT_UX_DARK = """
QSplitter#ERPSplitter::handle { background:#334155; margin:4px; border-radius:3px; }
QLabel#SectionTitle { color:#F8FAFC; font-size:15px; font-weight:900; }
QLabel#TahsilatInfoPill, QLabel#TahsilatMutedBadge {
    background:#1E3A8A;
    color:#DBEAFE;
    border:1px solid #2563EB;
    border-radius:12px;
    padding:7px 10px;
    font-weight:900;
}
QFrame#TahsilatFormCard {
    background:#0F172A;
    border:1px solid #334155;
    border-radius:14px;
}
QPushButton#CompactActionButton {
    background:#111827;
    color:#F8FAFC;
    border:1px solid #475569;
    border-radius:11px;
    padding:6px 10px;
    font-weight:900;
    min-height:36px;
}
QPushButton#CompactActionButton:hover { background:#1E293B; border-color:#60A5FA; color:#FFFFFF; }
QLabel#TahsilatHint { color:#CBD5E1; font-size:12px; font-weight:700; padding:4px 2px; }
"""

# Önceki get_style fonksiyonunu v142 ek stilleriyle genişlet.
_eski_get_style_v142 = get_style

def get_style(koyu: bool = False) -> str:
    return _eski_get_style_v142(koyu) + (TAHSILAT_UX_DARK if koyu else TAHSILAT_UX_LIGHT)

# v143 Cari Kartları UX ek stilleri.
CUSTOMER_UX_LIGHT = """
QFrame#CustomerPage { background:#F8FAFC; color:#0F172A; }
QFrame#CustomerHeader, QFrame#CustomerToolbar, QFrame#CustomerListCard, QFrame#CustomerDetailCard {
    background:#FFFFFF;
    border:1px solid #E2E8F0;
    border-radius:16px;
    color:#0F172A;
}
QScrollArea#CustomerDetailScroll { background:transparent; border:none; }
QScrollArea#CustomerDetailScroll > QWidget > QWidget { background:transparent; }
QLabel#CustomerTitle { color:#0F172A; font-size:24px; font-weight:900; background:transparent; }
QLabel#CustomerSubtitle { color:#64748B; font-size:12px; font-weight:700; background:transparent; }
QLabel#CustomerSectionTitle { color:#0F172A; font-size:15px; font-weight:900; background:transparent; }
QLabel#CustomerBadge {
    background:#EFF6FF;
    color:#1D4ED8;
    border:1px solid #BFDBFE;
    border-radius:11px;
    padding:7px 10px;
    font-weight:900;
}
QLabel#CustomerMetric {
    background:#FFFFFF;
    color:#0F172A;
    border:1px solid #E2E8F0;
    border-radius:14px;
    padding:9px 12px;
    font-size:13px;
    font-weight:900;
}
QLabel#CustomerSelectedName {
    background:#F8FAFC;
    border:1px solid #E2E8F0;
    border-radius:12px;
    padding:12px;
    font-size:15px;
    font-weight:900;
    color:#0F172A;
}
QLabel#CustomerDetailInfo { color:#475569; line-height:1.35; background:transparent; font-weight:700; }
QLabel#CustomerBalanceCard {
    background:#EFF6FF;
    color:#1D4ED8;
    border:1px solid #BFDBFE;
    border-radius:12px;
    padding:12px;
    font-size:15px;
    font-weight:900;
}
QLabel#CustomerMiniCard {
    background:#F8FAFC;
    color:#334155;
    border:1px solid #E2E8F0;
    border-radius:12px;
    padding:12px;
    font-weight:900;
}
QLineEdit#CustomerSearch {
    background:#FFFFFF;
    color:#0F172A;
    border:1px solid #CBD5E1;
    border-radius:12px;
    padding:8px 12px;
    min-height:36px;
    placeholder-text-color:#94A3B8;
}
QLineEdit#CustomerSearch:focus { border-color:#2563EB; }
QPushButton#CustomerPrimaryButton {
    background:#2563EB;
    color:white;
    border:none;
    border-radius:12px;
    padding:8px 14px;
    min-height:38px;
    font-weight:900;
}
QPushButton#CustomerPrimaryButton:hover { background:#1D4ED8; }
QPushButton#CustomerToolButton, QPushButton#CustomerSuccessButton, QPushButton#CustomerDangerButton {
    background:#FFFFFF;
    color:#0F172A;
    border:1px solid #CBD5E1;
    border-radius:11px;
    padding:7px 11px;
    min-height:36px;
    font-weight:900;
}
QPushButton#CustomerToolButton:hover { background:#EFF6FF; border-color:#93C5FD; color:#1D4ED8; }
QPushButton#CustomerSuccessButton { background:#ECFDF5; color:#047857; border-color:#A7F3D0; }
QPushButton#CustomerSuccessButton:hover { background:#D1FAE5; }
QPushButton#CustomerDangerButton { background:#FEF2F2; color:#B91C1C; border-color:#FECACA; }
QPushButton#CustomerDangerButton:hover { background:#FEE2E2; }
QSplitter#CustomerSplitter::handle { background:#E2E8F0; margin:4px; border-radius:3px; }
QTableWidget#CustomerTable {
    background:#FFFFFF;
    color:#0F172A;
    alternate-background-color:#F8FAFC;
    border:1px solid #E2E8F0;
    border-radius:12px;
    gridline-color:#E2E8F0;
    selection-background-color:#2563EB;
    selection-color:white;
}
"""

CUSTOMER_UX_DARK = """
QFrame#CustomerPage { background:#0F172A; color:#F8FAFC; }
QFrame#CustomerHeader, QFrame#CustomerToolbar, QFrame#CustomerListCard, QFrame#CustomerDetailCard {
    background:#1E293B;
    border:1px solid #334155;
    border-radius:16px;
    color:#F8FAFC;
}
QScrollArea#CustomerDetailScroll { background:transparent; border:none; }
QScrollArea#CustomerDetailScroll > QWidget > QWidget { background:transparent; }
QLabel#CustomerTitle { color:#F8FAFC; font-size:24px; font-weight:900; background:transparent; }
QLabel#CustomerSubtitle { color:#CBD5E1; font-size:12px; font-weight:700; background:transparent; }
QLabel#CustomerSectionTitle { color:#F8FAFC; font-size:15px; font-weight:900; background:transparent; }
QLabel#CustomerBadge {
    background:#1E3A8A;
    color:#DBEAFE;
    border:1px solid #2563EB;
    border-radius:11px;
    padding:7px 10px;
    font-weight:900;
}
QLabel#CustomerMetric {
    background:#111827;
    color:#F8FAFC;
    border:1px solid #334155;
    border-radius:14px;
    padding:9px 12px;
    font-size:13px;
    font-weight:900;
}
QLabel#CustomerSelectedName {
    background:#111827;
    border:1px solid #475569;
    border-radius:12px;
    padding:12px;
    font-size:15px;
    font-weight:900;
    color:#F8FAFC;
}
QLabel#CustomerDetailInfo { color:#CBD5E1; line-height:1.35; background:transparent; font-weight:700; }
QLabel#CustomerBalanceCard {
    background:#1E3A8A;
    color:#DBEAFE;
    border:1px solid #2563EB;
    border-radius:12px;
    padding:12px;
    font-size:15px;
    font-weight:900;
}
QLabel#CustomerMiniCard {
    background:#111827;
    color:#E2E8F0;
    border:1px solid #334155;
    border-radius:12px;
    padding:12px;
    font-weight:900;
}
QLineEdit#CustomerSearch {
    background:#111827;
    color:#F8FAFC;
    border:1px solid #475569;
    border-radius:12px;
    padding:8px 12px;
    min-height:36px;
    placeholder-text-color:#94A3B8;
}
QLineEdit#CustomerSearch:focus { border-color:#60A5FA; }
QPushButton#CustomerPrimaryButton {
    background:#3B82F6;
    color:white;
    border:none;
    border-radius:12px;
    padding:8px 14px;
    min-height:38px;
    font-weight:900;
}
QPushButton#CustomerPrimaryButton:hover { background:#2563EB; }
QPushButton#CustomerToolButton, QPushButton#CustomerSuccessButton, QPushButton#CustomerDangerButton {
    background:#111827;
    color:#F8FAFC;
    border:1px solid #475569;
    border-radius:11px;
    padding:7px 11px;
    min-height:36px;
    font-weight:900;
}
QPushButton#CustomerToolButton:hover { background:#1E293B; border-color:#60A5FA; color:#FFFFFF; }
QPushButton#CustomerSuccessButton { background:#064E3B; color:#D1FAE5; border-color:#059669; }
QPushButton#CustomerSuccessButton:hover { background:#065F46; }
QPushButton#CustomerDangerButton { background:#7F1D1D; color:#FEE2E2; border-color:#DC2626; }
QPushButton#CustomerDangerButton:hover { background:#991B1B; }
QSplitter#CustomerSplitter::handle { background:#334155; margin:4px; border-radius:3px; }
QTableWidget#CustomerTable {
    background:#0B1220;
    color:#F8FAFC;
    alternate-background-color:#111827;
    border:1px solid #475569;
    border-radius:12px;
    gridline-color:#334155;
    selection-background-color:#2563EB;
    selection-color:white;
}
"""

_eski_get_style_v143 = get_style

def get_style(koyu: bool = False) -> str:
    return _eski_get_style_v143(koyu) + (CUSTOMER_UX_DARK if koyu else CUSTOMER_UX_LIGHT)

# v144 Açık Tema Soft Sage - #C0CFCA deneme paleti
LIGHT_SAGE_OVERRIDE = """
QWidget {
    background: #C0CFCA;
    color: #1F2937;
}
QDialog, QMainWindow, QScrollArea, QStackedWidget, QTabWidget::pane,
QFrame#NextContentShell, QFrame#NextTopBar, QFrame#NextStatusBar, QWidget#ERPPage {
    background: #C0CFCA;
    color: #1F2937;
}
QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
    background: #C0CFCA;
    color: #1F2937;
}
QLabel { color: #1F2937; background: transparent; }
QLabel#NextPageSubtitle, QLabel#DialogSubtitle, QLabel#FormSectionLabel, QLabel#ERPPageSubtitle,
QLabel#ERPPanelTitle, QLabel#NextStatusLabel, QLabel#CustomerSubtitle, QLabel#CustomerDetailInfo {
    color: #4F5F5A;
}
QFrame#Sidebar { background: #EEF3F1; border-right: 1px solid #A8B7B2; }
QFrame#SidebarBrand, QLabel#SidebarFooter { background: #F7FAF9; border: 1px solid #A8B7B2; }
QLabel#SidebarBrandTitle { color: #1F2937; }
QLabel#SidebarBrandSubtitle, QLabel#SidebarGroupTitle { color: #4F5F5A; }
QPushButton#SidebarToggle, QPushButton#ExitButton {
    background: #F7FAF9;
    color: #1F2937;
    border: 1px solid #A8B7B2;
}
QPushButton#SidebarToggle:hover, QPushButton#ExitButton:hover {
    background: #E4ECE9;
    border-color: #879C96;
}
QPushButton#SidebarButton { color: #34413D; background: transparent; }
QPushButton#SidebarButton:hover { background: #E4ECE9; border-color: #A8B7B2; color: #1D4ED8; }
QPushButton#SidebarActive { background: #2563EB; border: 1px solid #2563EB; color: #FFFFFF; }
QFrame#TopBar, QFrame#MainCard, QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard,
QFrame#MetricCard, QFrame#QuickButton, QFrame#StatusCard, QFrame#ERPPanel, QFrame#ERPToolbar,
QFrame#ERPStatCard, QFrame#ThemePanel, QFrame#CustomerHeader, QFrame#CustomerToolbar,
QFrame#CustomerListCard, QFrame#CustomerDetailCard, QFrame#TahsilatFormCard {
    background: #EEF3F1;
    border: 1px solid #A8B7B2;
    border-radius: 14px;
    color: #1F2937;
}
QFrame#MetricCard:hover, QFrame#QuickButton:hover, QFrame#ERPStatCard:hover {
    background: #F7FAF9;
    border-color: #2563EB;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
QLineEdit#GlobalSearch, QLineEdit#CustomerSearch {
    background: #F7FAF9;
    color: #1F2937;
    border: 1px solid #A8B7B2;
    border-radius: 10px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    placeholder-text-color: #6B7C77;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit#GlobalSearch:focus, QLineEdit#CustomerSearch:focus {
    background: #FFFFFF;
    border: 1px solid #2563EB;
}
QPushButton, QPushButton#ERPButton, QPushButton#CustomerToolButton, QPushButton#CompactActionButton,
QPushButton#ThemeToggleButton, QPushButton#DashboardActionButton {
    background: #F7FAF9;
    color: #1F2937;
    border: 1px solid #A8B7B2;
    border-radius: 10px;
    font-weight: 800;
}
QPushButton:hover, QPushButton#ERPButton:hover, QPushButton#CustomerToolButton:hover,
QPushButton#CompactActionButton:hover, QPushButton#ThemeToggleButton:hover, QPushButton#DashboardActionButton:hover {
    background: #E4ECE9;
    border-color: #2563EB;
    color: #1D4ED8;
}
QPushButton:disabled { color: #6B7C77; background: #D6E0DC; border: 1px solid #A8B7B2; }
QPushButton#PrimaryButton, QPushButton#ERPPrimaryButton, QPushButton#CustomerPrimaryButton {
    background: #2563EB;
    color: #FFFFFF;
    border: 1px solid #2563EB;
}
QPushButton#PrimaryButton:hover, QPushButton#ERPPrimaryButton:hover, QPushButton#CustomerPrimaryButton:hover {
    background: #1D4ED8;
    border-color: #1D4ED8;
    color: #FFFFFF;
}
QTableWidget, QTableView, QTableWidget#CustomerTable, QTableWidget#ERPTable {
    background: #F7FAF9;
    color: #1F2937;
    alternate-background-color: #EAF0EE;
    border: 1px solid #A8B7B2;
    border-radius: 10px;
    gridline-color: #A8B7B2;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QHeaderView::section {
    background: #D6E0DC;
    color: #1F2937;
    border: none;
    border-bottom: 1px solid #A8B7B2;
    padding: 7px;
    font-weight: 900;
}
QGroupBox {
    background: #EEF3F1;
    color: #1F2937;
    border: 1px solid #A8B7B2;
    border-radius: 14px;
    margin-top: 18px;
    padding: 12px;
    font-weight: 900;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1F2937;
    background: #EEF3F1;
}
QLabel#MetricTitle, QLabel#ERPStatTitle, QLabel#CustomerSectionTitle { color: #34413D; }
QLabel#MetricValue, QLabel#ERPStatValue, QLabel#CustomerTitle, QLabel#NextPageTitle, QLabel#PageHeroTitle { color: #1F2937; }
QLabel#MetricSub, QLabel#ERPStatSubtitle, QLabel#TahsilatHint { color: #4F5F5A; }
QLabel#TahsilatSelectedCari, QLabel#CustomerSelectedName, QLabel#CustomerMiniCard, QLabel#CustomerMetric {
    background: #F7FAF9;
    color: #1F2937;
    border: 1px solid #A8B7B2;
    border-radius: 12px;
}
QLabel#TahsilatInfoPill, QLabel#TahsilatMutedBadge, QLabel#CustomerBadge, QLabel#CustomerBalanceCard {
    background: #E6F0FF;
    color: #1D4ED8;
    border: 1px solid #9CC2FF;
    border-radius: 12px;
}
QMenu { background: #F7FAF9; color: #1F2937; border: 1px solid #A8B7B2; border-radius: 10px; }
QMenu::item:selected { background: #E4ECE9; color: #1D4ED8; }
QSplitter::handle, QSplitter#CustomerSplitter::handle, QSplitter#ERPSplitter::handle {
    background: #A8B7B2;
    margin: 4px;
    border-radius: 3px;
}
"""

_eski_get_style_v144 = get_style
def get_style(koyu: bool = False) -> str:
    return _eski_get_style_v144(koyu) if koyu else _eski_get_style_v144(False) + LIGHT_SAGE_OVERRIDE


# v145 Unified UI - Dashboard sage palette tüm sayfalara yayıldı
LIGHT_UNIFIED_UI_OVERRIDE = """
QWidget, QDialog, QMainWindow, QStackedWidget, QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget,
QTabWidget::pane, QWidget#ERPPage, QFrame#NextContentShell, QFrame#NextTopBar, QFrame#NextStatusBar {
    background: #C0CFCA;
    color: #1F2937;
}
QFrame, QGroupBox {
    background: #EEF3F1;
    color: #1F2937;
    border-color: #A8B7B2;
}
QFrame#MainCard, QFrame#Panel, QFrame#PanelCard, QFrame#InfoCard, QFrame#FormCard, QFrame#TopBar,
QFrame#ERPPanel, QFrame#ERPToolbar, QFrame#ERPStatCard, QFrame#ThemePanel,
QFrame#CustomerHeader, QFrame#CustomerToolbar, QFrame#CustomerListCard, QFrame#CustomerDetailCard,
QFrame#TahsilatFormCard, QFrame#MetricCard, QFrame#QuickButton, QFrame#StatusCard {
    background: #EEF3F1;
    border: 1px solid #A8B7B2;
    border-radius: 14px;
    color: #1F2937;
}
QLabel { color: #1F2937; background: transparent; }
QLabel#Muted, QLabel#FormSectionLabel, QLabel#NextPageSubtitle, QLabel#ERPStatSubtitle,
QLabel#MetricSub, QLabel#DialogSubtitle, QLabel#CustomerSubtitle, QLabel#CustomerDetailInfo,
QLabel#TahsilatHint, QLabel#NextStatusLabel {
    color: #4F5F5A;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
QLineEdit#GlobalSearch, QLineEdit#CustomerSearch {
    background: #F7FAF9;
    color: #1F2937;
    border: 1px solid #A8B7B2;
    border-radius: 10px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    placeholder-text-color: #6B7C77;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
    background: #FFFFFF;
    border: 1px solid #2563EB;
}
QTableWidget, QTableView {
    background: #F7FAF9;
    color: #1F2937;
    alternate-background-color: #EAF0EE;
    border: 1px solid #A8B7B2;
    border-radius: 10px;
    gridline-color: #A8B7B2;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QHeaderView::section {
    background: #D6E0DC;
    color: #1F2937;
    border: none;
    border-bottom: 1px solid #A8B7B2;
    padding: 7px;
    font-weight: 900;
}
QPushButton, QPushButton#GreyButton, QPushButton#OrangeButton, QPushButton#PurpleButton,
QPushButton#LightButton, QPushButton#CompactActionButton, QPushButton#DashboardActionButton,
QPushButton#ThemeToggleButton {
    background: #F7FAF9;
    color: #1F2937;
    border: 1px solid #A8B7B2;
    border-radius: 10px;
    font-weight: 800;
}
QPushButton:hover, QPushButton#GreyButton:hover, QPushButton#OrangeButton:hover,
QPushButton#PurpleButton:hover, QPushButton#LightButton:hover, QPushButton#CompactActionButton:hover,
QPushButton#DashboardActionButton:hover, QPushButton#ThemeToggleButton:hover {
    background: #E4ECE9;
    border-color: #2563EB;
    color: #1D4ED8;
}
QPushButton#PrimaryButton, QPushButton#ERPPrimaryButton, QPushButton#CustomerPrimaryButton {
    background: #2563EB;
    color: #FFFFFF;
    border: 1px solid #2563EB;
}
QPushButton#GreenButton, QPushButton#SuccessButton {
    background: #15803D;
    color: #FFFFFF;
    border: 1px solid #15803D;
}
QPushButton#RedButton, QPushButton#DangerButton {
    background: #B91C1C;
    color: #FFFFFF;
    border: 1px solid #B91C1C;
}
QGroupBox {
    border: 1px solid #A8B7B2;
    border-radius: 14px;
    margin-top: 18px;
    padding: 12px;
    font-weight: 900;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1F2937;
    background: #EEF3F1;
}
QTabBar::tab { background:#EEF3F1; color:#34413D; border:1px solid #A8B7B2; padding:8px 14px; font-weight:800; }
QTabBar::tab:selected { background:#F7FAF9; color:#1D4ED8; border-color:#879C96; }
QMenu { background: #F7FAF9; color: #1F2937; border: 1px solid #A8B7B2; border-radius: 10px; }
QMenu::item:selected { background: #E4ECE9; color: #1D4ED8; }
"""

_eski_get_style_v145 = get_style
def get_style(koyu: bool = False) -> str:
    return _eski_get_style_v145(koyu) if koyu else _eski_get_style_v145(False) + LIGHT_UNIFIED_UI_OVERRIDE


def normalize_inline_styles(root_widget=None) -> None:
    """v145: Eski ekranlarda kalan sabit beyaz stil kalıntılarını temizler.

    Bazı modüller kendi içinde setStyleSheet ile #FFFFFF/white verdiği için
    uygulama genelindeki soft sage tema görünmüyordu. Bu fonksiyon yalnızca
    tema ile çakışan renkli inline stilleri temizler; nesne adları ve genel QSS
    tasarım dilini uygular.
    """
    try:
        from PySide6.QtWidgets import QApplication, QPushButton, QWidget
    except Exception:
        return
    widgets = []
    try:
        if root_widget is not None:
            widgets.extend(root_widget.findChildren(QWidget))
            widgets.append(root_widget)
        else:
            app = QApplication.instance()
            if app:
                widgets.extend(app.allWidgets())
    except Exception:
        return
    kalintilar = (
        '#FFFFFF', '#ffffff', 'background:white', 'background: white', 'background:#fff',
        '#F8FAFC', '#f8fafc', '#F5F7FA', '#E2E8F0', '#D8E0EA', '#CBD5E1',
        '#0F172A', '#111827', '#1E293B', '#334155', '#475569'
    )
    for w in widgets:
        try:
            st = w.styleSheet() or ''
            if not st:
                continue
            if 'qlineargradient' in st:
                continue
            if any(x in st for x in kalintilar):
                # Özel amaçlı renkli aksiyon butonlarının semantic objectName'i varsa koru.
                obj = w.objectName() or ''
                if isinstance(w, QPushButton) and obj in {'PrimaryButton', 'GreenButton', 'RedButton', 'SuccessButton', 'DangerButton'}:
                    continue
                w.setStyleSheet('')
        except Exception:
            pass
