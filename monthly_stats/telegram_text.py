import random
from typing import Any, Dict, List


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


INTRO_VARIANTS: List[str] = [
    "Livermore monthly structural read (30d)",
    "Livermore monthly regime read (30d)",
    "Livermore monthly structure read (30d)",
]

FUTURES_VARIANTS: Dict[str, List[str]] = {
    "persistent_active": [
        "Futures pressure stayed persistent through the month, with extreme stress active in multiple windows.",
        "Futures crowding remained persistent across the month, while extreme stress stayed active in repeated windows.",
        "Futures pressure held at a persistent level, with extreme stress remaining active often enough to matter.",
    ],
    "persistent_visible": [
        "Futures pressure stayed persistent through the month, while extreme stress remained visible rather than fully contained.",
        "Persistent futures pressure shaped the month, with extreme stress visible across part of the window.",
        "Futures crowding remained persistent, while extreme stress stayed visible across repeated windows.",
    ],
    "persistent_contained": [
        "Futures pressure stayed persistent through the month, though extreme stress remained comparatively contained.",
        "Persistent futures pressure shaped the month, even as extreme stress stayed more contained than broad crowding.",
        "Futures crowding remained persistent, while the most acute stress stayed relatively contained.",
    ],
    "frequent_active": [
        "Futures pressure recurred frequently through the month, with extreme stress active in multiple windows.",
        "Futures crowding appeared frequently, while extreme stress remained active often enough to shape the monthly read.",
        "Pressure in futures was frequent rather than isolated, with extreme stress active across part of the month.",
    ],
    "frequent_visible": [
        "Futures pressure recurred frequently through the month, with extreme stress remaining visible across the window.",
        "Futures crowding appeared frequently, while extreme stress stayed visible rather than dominant.",
        "Pressure in futures remained frequent, with extreme stress visible across selected windows.",
    ],
    "frequent_contained": [
        "Futures pressure recurred frequently through the month, though extreme stress stayed comparatively contained.",
        "Futures crowding appeared often, but the most acute stress remained more contained than persistent.",
        "Pressure in futures was frequent, while extreme stress stayed contained relative to the broader pressure profile.",
    ],
    "intermittent_active": [
        "Futures pressure was intermittent through the month, though extreme stress still turned active in selected windows.",
        "Futures crowding appeared in intermittent waves, with extreme stress active during part of the window.",
        "Pressure in futures stayed intermittent, while extreme stress still became active in isolated segments.",
    ],
    "intermittent_visible": [
        "Futures pressure appeared intermittently through the month, with extreme stress remaining visible but not dominant.",
        "Futures crowding came in waves, while extreme stress stayed visible across part of the horizon.",
        "Pressure in futures was intermittent, with extreme stress visible without becoming the defining feature of the month.",
    ],
    "intermittent_contained": [
        "Futures pressure appeared intermittently through the month, while extreme stress remained broadly contained.",
        "Futures crowding came in waves, but the sharpest stress remained contained overall.",
        "Pressure in futures was intermittent, with extreme stress staying largely contained.",
    ],
    "contained_active": [
        "Futures pressure stayed relatively contained overall, though extreme stress still turned active in isolated windows.",
        "Broad futures pressure remained contained, but isolated extreme-stress windows still appeared.",
        "The futures layer stayed relatively contained, even as isolated windows of extreme stress emerged.",
    ],
    "contained_visible": [
        "Futures pressure stayed relatively contained, with extreme stress visible only in limited parts of the month.",
        "The futures layer remained contained overall, while extreme stress stayed visible but selective.",
        "Broad futures pressure remained contained, with only limited visibility of extreme stress.",
    ],
    "contained_contained": [
        "Futures pressure stayed relatively contained through the month, with extreme stress also remaining contained.",
        "The futures layer remained contained overall, without persistent extreme stress taking hold.",
        "Both broad futures pressure and extreme stress stayed contained across the monthly horizon.",
    ],
}

OPTIONS_VARIANTS: Dict[str, List[str]] = {
    "neutral": [
        "Options structure stayed mostly neutral, with directional pressure failing to take durable control.",
        "The options layer remained mostly neutral, with limited structural pressure outside selective compression phases.",
        "Options stayed broadly neutral, with compression appearing periodically but without a durable directional regime.",
    ],
    "directional": [
        "Options moved away from neutral often enough to matter, with directional pressure shaping part of the monthly structure.",
        "The options layer leaned directional through part of the month, reducing the weight of the neutral regime.",
        "Directional regimes appeared often enough to matter, pushing options structure away from a fully neutral read.",
    ],
    "compressed": [
        "Compression phases appeared often enough to shape the monthly options read, even without a clean directional regime.",
        "The options layer reflected recurring compression, giving the month a tighter structural profile.",
        "Options structure was shaped by recurring compression phases, even as directional conviction remained incomplete.",
    ],
    "mixed": [
        "Options structure remained mixed, with neutral and directional regimes alternating around periodic compression phases.",
        "The options layer stayed mixed, with no single regime holding long enough to dominate the monthly read.",
        "Options remained mixed overall, as neutral, directional, and compression phases rotated without a stable regime taking hold.",
    ],
}

VOL_VARIANTS: Dict[str, List[str]] = {
    "expansion backdrop": [
        "Volatility conditions reflected an expansion backdrop, with BTC/ETH state overlap reinforcing the broader regime.",
        "The volatility backdrop stayed in expansion mode, with BTC and ETH aligning in elevated states often enough to matter.",
        "Volatility reflected a clear expansion backdrop, reinforced by persistent BTC/ETH overlap in elevated states.",
    ],
    "firmer backdrop": [
        "Volatility conditions reflected a firmer backdrop, with BTC/ETH overlap supporting the monthly structure.",
        "The volatility backdrop turned firmer across the month, with BTC and ETH aligning often enough to register.",
        "Volatility remained firmer than neutral, with BTC/ETH state overlap helping sustain the broader backdrop.",
    ],
    "contained backdrop": [
        "Volatility conditions stayed comparatively contained, with BTC/ETH overlap failing to build a stronger expansion backdrop.",
        "The volatility backdrop remained relatively contained, without enough BTC/ETH alignment to define the month.",
        "Volatility stayed broadly contained, with limited BTC/ETH overlap in elevated states.",
    ],
}

CROSS_LAYER_VARIANTS: Dict[str, List[str]] = {
    "broad pressure": [
        "Pressure was not confined to one layer, and alignment across futures, options, and volatility was persistent enough to define the monthly structure.",
        "More than one layer carried structural pressure, with futures, options, and volatility aligning often enough to matter at the monthly horizon.",
        "The monthly structure was shaped by multi-layer pressure, with alignment across positioning, options, and volatility appearing often enough to register.",
    ],
    "futures-led pressure": [
        "Futures crowding recurred consistently, while confirmation from options and volatility remained only partial over the same horizon.",
        "The clearest pressure sat in futures, while options and volatility offered only partial confirmation across the month.",
        "Futures carried the strongest structural signal, with broader confirmation from options and volatility remaining incomplete.",
    ],
    "vol-led backdrop": [
        "Volatility delivered the clearest structural signal, while positioning and options pressure stayed secondary in persistence.",
        "The volatility backdrop led the monthly read, while futures and options remained less consistent in confirmation.",
        "Volatility carried more of the month than positioning or options, with broader confirmation remaining uneven.",
    ],
    "mixed structure": [
        "Signals appeared across layers, but persistence and timing did not align into a single dominant structural regime.",
        "Pressure appeared in more than one layer, but alignment remained uneven rather than regime-defining.",
        "The monthly read stayed mixed, with cross-layer signals present but not synchronized strongly enough to resolve into one dominant regime.",
    ],
}

REGIME_VARIANTS: Dict[str, List[str]] = {
    "broad pressure": [
        "Broad pressure environment with recurring crowding and a firm volatility backdrop.",
        "Broad pressure regime with multi-layer confirmation across positioning, options, and volatility.",
        "Monthly regime resolved into broad pressure, with repeated crowding and a firm background volatility profile.",
    ],
    "futures-led pressure": [
        "Futures-led pressure environment with recurring crowding and limited cross-layer confirmation.",
        "Futures-led regime with repeated positioning stress and only partial confirmation elsewhere.",
        "Monthly regime remained futures-led, with crowding recurring more consistently than broader confirmation.",
    ],
    "vol-led backdrop": [
        "Volatility-led environment with selective participation from positioning and options structure.",
        "Vol-led regime with a firmer backdrop than positioning alone would imply.",
        "Monthly regime leaned on volatility more than on futures or options confirmation.",
    ],
    "mixed structure": [
        "Mixed monthly structure with uneven confirmation across futures, options, and volatility.",
        "Mixed regime with pressure signals present, but cross-layer confirmation remaining incomplete.",
        "Monthly structure stayed mixed, with no single layer fully resolving the broader read.",
    ],
}

SHORT_FILLERS: List[str] = [
    "The balance of signals remained stable enough to treat this as a structural monthly read rather than a short-lived fluctuation.",
    "Taken together, the monthly profile looked structural rather than reactive, with pressure dynamics extending beyond a single local burst.",
    "Overall, the signal mix stayed broad enough to read as a monthly structure rather than a short-lived distortion.",
]


def _pick(options: List[str], fallback: str) -> str:
    cleaned = [x.strip() for x in options if isinstance(x, str) and x.strip()]
    if not cleaned:
        return fallback
    return random.choice(cleaned)


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
    cross_layer = _cross_layer_state(
        futures_states["futures_pressure"],
        options_state,
        vol_state,
    )

    futures_key = f"{futures_states['futures_pressure']}_{futures_states['stress_state']}"
    futures_line = _pick(
        FUTURES_VARIANTS.get(futures_key, []),
        "Futures pressure remained visible through the month, with extreme stress staying secondary to the broader structure.",
    )

    options_line = _pick(
        OPTIONS_VARIANTS.get(options_state, []),
        "Options structure remained mixed through the month.",
    )

    vol_line = _pick(
        VOL_VARIANTS.get(vol_state, []),
        "Volatility conditions remained part of the monthly structure without becoming the sole defining layer.",
    )

    cross_layer_line = _pick(
        CROSS_LAYER_VARIANTS.get(cross_layer, []),
        "Cross-layer signals remained mixed, without a single clean structural alignment dominating the month.",
    )

    regime_line = _pick(
        REGIME_VARIANTS.get(cross_layer, []),
        "Mixed monthly regime with incomplete cross-layer confirmation.",
    )

    text = (
        f"{_pick(INTRO_VARIANTS, 'Livermore monthly structural read (30d)')}\n\n"
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
        text += " " + _pick(
            SHORT_FILLERS,
            "The monthly balance of signals remained broad enough to read as structure rather than noise.",
        )

    return text[:900].strip()
