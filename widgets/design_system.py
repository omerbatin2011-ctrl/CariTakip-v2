"""DAL ERP Next v139 Design System.

Bu dosya, uygulamanın ölçü, renk ve responsive kırılımlarını tek merkezde tutar.
Yeni ekranlarda sabit piksel değerleri yerine buradaki token'lar kullanılmalıdır.
"""

from __future__ import annotations

from dataclasses import dataclass

VERSION = "v144"

# Spacing scale
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_2XL = 32

# Radius scale
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16
RADIUS_XL = 20

# Layout metrics
SIDEBAR_EXPANDED = 236
SIDEBAR_COMPACT = 72
SIDEBAR_WIDE = 260
TOPBAR_HEIGHT = 54
STATUSBAR_HEIGHT = 28

# Common control metrics
BUTTON_HEIGHT = 40
TOOL_BUTTON_HEIGHT = 36
INPUT_HEIGHT = 40
TABLE_ROW_HEIGHT = 34

# KPI card metrics
KPI_MIN_WIDTH = 205
KPI_IDEAL_WIDTH = 230
KPI_MAX_WIDTH = 260
KPI_MIN_HEIGHT = 86
KPI_ICON_SIZE = 38

# Font sizes
FONT_TITLE = 18
FONT_SUBTITLE = 12
FONT_BODY = 13
FONT_SMALL = 11
FONT_BUTTON = 13
FONT_KPI_TITLE = 12
FONT_KPI_VALUE = 20
FONT_KPI_SUBTITLE = 11


@dataclass(frozen=True)
class ThemePalette:
    name: str
    background: str
    surface: str
    surface_alt: str
    text: str
    muted_text: str
    border: str
    primary: str
    primary_hover: str
    success: str
    warning: str
    danger: str
    shadow: str


LIGHT = ThemePalette(
    name="light",
    background="#C0CFCA",
    surface="#EEF3F1",
    surface_alt="#F7FAF9",
    text="#1F2937",
    muted_text="#4F5F5A",
    border="#A8B7B2",
    primary="#2563EB",
    primary_hover="#1D4ED8",
    success="#15803D",
    warning="#B45309",
    danger="#B91C1C",
    shadow="rgba(31, 41, 55, 0.10)",
)

DARK = ThemePalette(
    name="dark",
    background="#0F172A",
    surface="#111827",
    surface_alt="#1F2937",
    text="#F8FAFC",
    muted_text="#CBD5E1",
    border="#334155",
    primary="#60A5FA",
    primary_hover="#3B82F6",
    success="#22C55E",
    warning="#F59E0B",
    danger="#F87171",
    shadow="rgba(0, 0, 0, 0.24)",
)

CORPORATE = ThemePalette(
    name="corporate",
    background="#EEF4FF",
    surface="#FFFFFF",
    surface_alt="#F1F5FF",
    text="#0B1F3A",
    muted_text="#53657D",
    border="#D8E3F8",
    primary="#1E40AF",
    primary_hover="#1D4ED8",
    success="#15803D",
    warning="#B45309",
    danger="#B91C1C",
    shadow="rgba(30, 64, 175, 0.10)",
)

PALETTES = {
    "light": LIGHT,
    "dark": DARK,
    "corporate": CORPORATE,
}


def get_palette(name: str | None = None) -> ThemePalette:
    return PALETTES.get((name or "light").lower(), LIGHT)


def dashboard_kpi_columns(width: int) -> int:
    """Dashboard KPI kolon sayısı.

    Kartlar artık gereksiz genişlemez; yeterli alan yoksa yeni satıra iner.
    """
    try:
        width = int(width or 1200)
    except Exception:
        width = 1200
    if width >= 1640:
        return 6
    if width >= 1360:
        return 5
    if width >= 1120:
        return 4
    if width >= 860:
        return 3
    if width >= 560:
        return 2
    return 1


def quick_action_columns(width: int) -> int:
    try:
        width = int(width or 1200)
    except Exception:
        width = 1200
    if width >= 1500:
        return 7
    if width >= 1180:
        return 4
    if width >= 760:
        return 3
    if width >= 520:
        return 2
    return 1


def grid_columns(width: int, min_item_width: int = KPI_MIN_WIDTH, max_columns: int = 6) -> int:
    """Genel responsive kolon hesaplayıcı."""
    try:
        width = int(width or 1200)
    except Exception:
        width = 1200
    min_item_width = max(120, int(min_item_width or KPI_MIN_WIDTH))
    return max(1, min(max_columns, width // min_item_width))
