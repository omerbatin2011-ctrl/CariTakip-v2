"""DAL ERP Next ortak widget paketleri."""

try:
    from .erp_framework import (
        FRAMEWORK_VERSION,
        ERPButton,
        ERPCard,
        ERPComboBox,
        ERPDateEdit,
        ERPDialog,
        ERPForm,
        ERPLineEdit,
        ERPPage,
        ERPPanel,
        ERPResponsiveGrid,
        ERPSearchBox,
        ERPStatCard,
        ERPStatusBar,
        ERPTable,
        ERPTextEdit,
        ERPToolbar,
        ERPToolButton,
    )
except Exception:
    # Eski PySide6 kurulumlarında modül import hatası uygulamayı açılışta kırmasın.
    FRAMEWORK_VERSION = "unknown"

try:
    from .ui_helpers import ERPButton as LegacyERPButton
    from .ui_helpers import ERPCard as LegacyERPCard
    from .ui_helpers import ERPPanel as LegacyERPPanel
    from .ui_helpers import action_button
except Exception:
    pass

try:
    from .erp_page import placeholder_page
except Exception:
    pass


try:
    from .design_system import (
        BUTTON_HEIGHT,
        INPUT_HEIGHT,
        KPI_MAX_WIDTH,
        KPI_MIN_WIDTH,
        dashboard_kpi_columns,
        get_palette,
        grid_columns,
        quick_action_columns,
    )
    from .design_system import (
        VERSION as DESIGN_SYSTEM_VERSION,
    )
    from .theme_styles import build_erp_qss
except Exception:
    DESIGN_SYSTEM_VERSION = "unknown"
