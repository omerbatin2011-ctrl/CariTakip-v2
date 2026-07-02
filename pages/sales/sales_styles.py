SALES_PAGE_STYLE = """
QWidget {
    background: #F1F5F9;
    color: #0F172A;
    font-family: Arial;
}

QFrame#HeaderPanel,
QFrame#Panel,
QFrame#RibbonPanel,
QFrame#ActionPanel {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

QPushButton {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 12px;
    font-weight: 700;
}

QPushButton:hover {
    background: #F8FAFC;
}

QPushButton#PrimaryButton {
    background: #2563EB;
    color: white;
    border: none;
}

QPushButton#DangerButton,
QPushButton#OutlineDangerButton {
    color: #B91C1C;
    border: 1px solid #FCA5A5;
}

QLineEdit,
QTextEdit,
QComboBox {
    background: white;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px;
}

QTableWidget {
    background: white;
    border: 1px solid #E2E8F0;
    gridline-color: #E2E8F0;
}

QHeaderView::section {
    background: #F8FAFC;
    color: #334155;
    padding: 7px;
    border: 1px solid #E2E8F0;
    font-weight: 800;
}
"""