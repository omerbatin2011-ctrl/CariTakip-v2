"""DAL ERP Next v138 Theme Style Builder.

QSS stillerini tasarım sistemi token'larından üretir. Böylece renk, boşluk,
radius ve temel ölçüler tek merkezden yönetilir.
"""

from __future__ import annotations

from .design_system import (
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
    RADIUS_LG,
    RADIUS_MD,
    SPACING_MD,
    SPACING_SM,
    TABLE_ROW_HEIGHT,
    TOOL_BUTTON_HEIGHT,
    get_palette,
)


def build_erp_qss(theme: str = "light") -> str:
    p = get_palette(theme)
    return f"""
QWidget#ERPPage {{
    background: {p.background};
    color: {p.text};
}}
QFrame#ERPPanel, QFrame#ERPCard, QFrame#ERPForm {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {RADIUS_LG}px;
}}
QFrame#ERPToolbar {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {RADIUS_MD}px;
}}
QLabel#ERPPageTitle {{
    color: {p.text};
    font-size: 18px;
    font-weight: 800;
}}
QLabel#ERPPageSubtitle, QLabel#ERPPanelTitle, QLabel#ERPFormLabel, QLabel#ERPStatusItem {{
    color: {p.muted_text};
    font-size: 12px;
}}
QLabel#ERPToolbarTitle {{
    color: {p.text};
    font-size: 14px;
    font-weight: 800;
}}
QFrame#ERPStatCard {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {RADIUS_LG}px;
}}
QFrame#ERPStatCard:hover {{
    border-color: {p.primary};
    background: {p.surface_alt};
}}
QLabel#ERPStatTitle {{
    color: {p.muted_text};
    font-size: 12px;
    font-weight: 700;
}}
QLabel#ERPStatValue {{
    color: {p.text};
    font-weight: 900;
}}
QLabel#ERPStatSubtitle {{
    color: {p.muted_text};
    font-size: 11px;
}}
QPushButton#ERPButton, QPushButton#ERPToolButton {{
    min-height: {BUTTON_HEIGHT}px;
    padding: 0 {SPACING_MD}px;
    border-radius: {RADIUS_MD}px;
    background: {p.surface_alt};
    border: 1px solid {p.border};
    color: {p.text};
    font-weight: 700;
}}
QPushButton#ERPToolButton {{ min-height: {TOOL_BUTTON_HEIGHT}px; }}
QPushButton#ERPButton:hover, QPushButton#ERPToolButton:hover {{
    border-color: {p.primary};
}}
QPushButton#ERPPrimaryButton, QPushButton#ERPToolButtonPrimary {{
    min-height: {BUTTON_HEIGHT}px;
    padding: 0 {SPACING_MD}px;
    border-radius: {RADIUS_MD}px;
    background: {p.primary};
    border: 1px solid {p.primary};
    color: white;
    font-weight: 800;
}}
QPushButton#ERPPrimaryButton:hover, QPushButton#ERPToolButtonPrimary:hover {{
    background: {p.primary_hover};
}}
QPushButton#ERPDangerButton {{
    min-height: {BUTTON_HEIGHT}px;
    border-radius: {RADIUS_MD}px;
    background: {p.danger};
    color: white;
    border: 1px solid {p.danger};
    font-weight: 800;
}}
QLineEdit#ERPSearchBox, QLineEdit#ERPLineEdit, QTextEdit#ERPTextEdit, QComboBox#ERPComboBox, QDateEdit#ERPDateEdit {{
    min-height: {INPUT_HEIGHT}px;
    border: 1px solid {p.border};
    border-radius: {RADIUS_MD}px;
    background: {p.surface};
    color: {p.text};
    padding: 0 {SPACING_SM}px;
}}
QLineEdit#ERPSearchBox:focus, QLineEdit#ERPLineEdit:focus, QTextEdit#ERPTextEdit:focus, QComboBox#ERPComboBox:focus, QDateEdit#ERPDateEdit:focus {{
    border-color: {p.primary};
}}
QTableWidget#ERPTable {{
    background: {p.surface};
    alternate-background-color: {p.surface_alt};
    border: 1px solid {p.border};
    border-radius: {RADIUS_MD}px;
    gridline-color: {p.border};
    color: {p.text};
    selection-background-color: {p.primary};
    selection-color: white;
}}
QTableWidget#ERPTable::item {{
    min-height: {TABLE_ROW_HEIGHT}px;
    padding: 4px;
}}
QHeaderView::section {{
    background: {p.surface_alt};
    color: {p.text};
    border: none;
    border-bottom: 1px solid {p.border};
    padding: 7px;
    font-weight: 800;
}}
QFrame#ERPStatusBar {{
    background: {p.surface};
    border-top: 1px solid {p.border};
}}
QDialog#ERPDialog {{
    background: {p.background};
    color: {p.text};
}}
"""
