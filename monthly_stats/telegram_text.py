from typing import Any, Dict


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _futures_states(ge3_share: float, ge5_share: float) -> Dict[str, str]:
    if ge3_share >= 70:
        futures_pressure = "persistent"
    elif ge3_share >= 40:
        futures_pressure = "frequent"
    elif ge3_share >= 20:
        futures_pressure = "intermittent"
    else:
        futures_pressure = "contained"

    if ge5_share >= 30:
        stress_state = "active"
    elif ge5_share >= 10:
        stress_state = "visible"
    else:
        stress_state = "contained"

    return {"futures_pressure": futures_pressure, "stress_state": stress_state}


def _options_state(calm_pct: float, directional_pct: float, compression_pct: float) -> str:
    if calm_pct > 60:
        return "neutral"
    if directional_pct > 30:
        return "directional"
    if compression_pct > 15:
        return "compressed"
    return "mixed"


def _vol_state(overlap: float) -> str:
    if overlap >= 35:
        return "expansion backdrop"
    if overlap >= 20:
        return "firmer backdrop"
    return "contained backdrop"


def _cross_layer_state(futures_pressure: str, options_state: str, vol_state: str) -> str:
    futures_strong = futures_pressure in {"persistent", "frequent"}
    options_strong = options_state in {"directional", "compressed"}
    vol_strong = vol_state in {"expansion backdrop", "firmer backdrop"}

    if futures_strong and options_strong and vol_strong:
        return "broad pressure"
    if futures_strong and not (options_strong and vol_strong):
        return "futures-led pressure"
    if vol_strong and not futures_strong:
        return "vol-led backdrop"
    return "mixed structure"


def build_monthly_telegram_interpretation(stats: Dict[str, Any]) -> str:
    risk = stats.get("risk") or {}
    bybit = stats.get("bybit") or {}
    deribit = stats.get("deribit") or {}

    ge3_share = _as_float(risk.get("market_high_risk_ge3_share_pct"))
    ge5_share = _as_float(risk.get("market_high_risk_ge5_share_pct"))

    calm_pct = _as_float(bybit.get("regime_calm_pct"))
    directional_pct = _as_float(bybit.get("regime_directional_total_pct"))
    compression_pct = _as_float(bybit.get("mci_gt_06_share_pct"))

    overlap = _as_float(deribit.get("both_hot_or_warm_share_pct"))

    futures_states = _futures_states(ge3_share, ge5_share)
    options_state = _options_state(calm_pct, directional_pct, compression_pct)
    vol_state = _vol_state(overlap)
    cross_layer = _cross_layer_state(futures_states["futures_pressure"], options_state, vol_state)

    futures_line = (
        f"Futures pressure was {futures_states['futures_pressure']} through the month, with extreme stress {futures_states['stress_state']} across risk windows."
    )
    options_line = (
        f"Options structure read as {options_state}, with neutral and directional regimes alternating around periodic compression phases."
    )
    vol_line = f"Volatility conditions reflected a {vol_state}, with BTC/ETH state overlap shaping the background tone."

    cross_layer_line = {
        "broad pressure": "Pressure was not confined to one layer, and alignment across futures, options, and volatility was persistent enough to define the monthly structure.",
        "futures-led pressure": "Futures crowding recurred consistently, while confirmation from options and volatility remained only partial over the same horizon.",
        "vol-led backdrop": "Volatility delivered the clearest structural signal, while positioning and options pressure stayed secondary in persistence.",
        "mixed structure": "Signals appeared across layers, but persistence and timing did not align into a single dominant structural regime.",
    }[cross_layer]

    regime_line = {
        "broad pressure": "Broad pressure environment with recurring crowding and a firm volatility backdrop.",
        "futures-led pressure": "Futures-led pressure environment with recurring crowding and limited cross-layer confirmation.",
        "vol-led backdrop": "Volatility-led environment with selective participation from positioning and options structure.",
        "mixed structure": "Mixed monthly structure with uneven confirmation across futures, options, and volatility.",
    }[cross_layer]

    text = (
        "Livermore monthly structural read (30d)\n\n"
        "Futures structure\n"
        f"{futures_line}\n\n"
        "Options structure\n"
        f"{options_line}\n\n"
        "Volatility structure\n"
        f"{vol_line}\n\n"
        "Cross-layer read\n"
        f"{cross_layer_line}\n\n"
        "Monthly regime\n"
        f"{regime_line}"
    )

    if len(text) < 400:
        text += " The balance of signals remained stable enough to treat this as a structural monthly read rather than a short-lived fluctuation."

    return text[:900].strip()
