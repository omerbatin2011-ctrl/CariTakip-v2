"""Customer risk panel helpers."""

from __future__ import annotations

RISK_SAFE = "Risk yok"
RISK_DEBT = "Açık bakiye var"
RISK_CREDIT = "Cari avanslı durumda"


def calculate_balance_risk(balance: float) -> str:
    """Return a user-friendly risk description for a balance."""

    if balance > 0:
        return RISK_DEBT
    if balance < 0:
        return RISK_CREDIT
    return RISK_SAFE
