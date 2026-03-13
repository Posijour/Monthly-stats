import random
import re
from typing import Any, Dict, List, Optional, Tuple

INTRO_VARIANTS = [
    "Livermore monthly snapshot (30d)\n\n30-day structural view across:\n\n• futures positioning\n• options expectations\n• volatility background",
    "Livermore monthly snapshot (30d)\n\nRolling 30-day regime read across:\n\n• futures positioning\n• options expectations\n• volatility background",
]

FUTURES_VARIANTS = {
    "extreme": [
        "Futures pressure was frequent and persistent, with repeated high-stress windows shaping the month.",
        "Crowding was not episodic: stress conditions repeated often enough to define the monthly futures regime.",
    ],
    "high": [
        "Futures stress reappeared regularly, showing persistent pressure rather than isolated bursts.",
        "High-risk windows were frequent enough to suggest recurring crowd pressure through the month.",
    ],
    "medium": [
        "Pressure appeared in waves: meaningful, but not dominant enough to define the whole 30d structure.",
        "Futures stress was visible yet uneven, with intermittent rather than continuous pressure.",
    ],
    "light": [
        "Futures pressure stayed mostly local, with only occasional high-risk expansion.",
        "Some stress appeared, but it stayed episodic and limited in market-wide persistence.",
    ],
    "calm": [
        "Futures structure remained mostly contained, with low recurrence of high-stress windows.",
        "The month looked relatively calm in futures, without broad persistent crowding.",
    ],
}

OPTIONS_VARIANTS = {
    "high": [
        "Options were structurally active: directional regimes and compression appeared often enough to matter.",
        "Options leaned away from neutral, with sustained directional or compressed episodes in the 30d view.",
    ],
    "medium": [
        "Options showed selective directional pressure, but not a fully dominant regime shift.",
        "The options layer was mixed: some directional/compression phases, but no uninterrupted regime.",
    ],
    "calm": [
        "Options stayed mostly neutral, with directional and high-compression windows limited.",
        "The options regime remained largely balanced, with only light structural pressure.",
    ],
}

VOL_VARIANTS = {
    "high": [
        "Volatility stayed elevated for a meaningful share of windows, pointing to persistent repricing background.",
        "BTC/ETH often sat in warm-hot states together, suggesting non-trivial volatility expansion backdrop.",
    ],
    "medium": [
        "Volatility firmness appeared repeatedly, but mostly in shorter phases rather than one continuous expansion.",
        "The vol backdrop was active in parts, though persistence remained moderate.",
    ],
    "calm": [
        "Volatility conditions were mostly contained, with limited overlap of elevated BTC/ETH states.",
        "Warm-hot phases were present but not persistent enough to dominate the monthly structure.",
    ],
}

SYNTHESIS_VARIANTS = {
    "contained": "Structural takeaway:\n\nThe 30d profile stayed contained: pressure signals were limited and did not synchronize into a broad regime shift.",
    "mixed": "Structural takeaway:\n\nThe month was mixed: stress appeared across layers, but persistence and alignment were uneven.",
    "futures_led": "Structural takeaway:\n\nFutures led the month: crowd pressure repeated more consistently than options or volatility confirmation.",
    "options_led": "Structural takeaway:\n\nOptions led the structure: directional/compression signals were stronger than futures confirmation.",
    "vol_led": "Structural takeaway:\n\nVolatility led the month: elevated vol background was clearer than futures pressure.",
    "broad_pressure": "Structural takeaway:\n\nBroad pressure regime: futures stress, options structure, and volatility backdrop aligned often enough to matter.",
}


def pick_variant(options: List[str], fallback: str) -> str:
    if not options:
        return fallback
    cleaned = [str(x).strip() for x in options if str(x).strip()]
    return random.choice(cleaned) if cleaned else fallback


def trim_tweet(text: str, max_len: int = 260) -> str:
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def clean_symbol(sym: str) -> str:
    return str(sym).replace("USDT", "")


def top_symbol_names(items: List[Tuple[str, Any]], limit: int = 3) -> str:
    if not items:
        return "n/a"
    return ", ".join(clean_symbol(k) for k, _ in items[:limit])


def p(x: Optional[float]) -> str:
    return f"{(x or 0.0):.1f}%"


def futures_bucket(ge3: float, ge5: float, avg_risk: float) -> str:
    if ge3 >= 45 or ge5 >= 12 or avg_risk >= 1.2:
        return "extreme"
    if ge3 >= 30 or ge5 >= 8 or avg_risk >= 0.9:
        return "high"
    if ge3 >= 18 or ge5 >= 4 or avg_risk >= 0.6:
        return "medium"
    if ge3 >= 8 or ge5 >= 2 or avg_risk >= 0.3:
        return "light"
    return "calm"


def options_bucket(directional: float, compression: float, calm: float) -> str:
    if directional >= 45 or compression >= 20 or calm <= 35:
        return "high"
    if directional >= 25 or compression >= 10 or calm <= 55:
        return "medium"
    return "calm"


def vol_bucket(btc_wh: float, eth_wh: float, overlap: float) -> str:
    if overlap >= 35 or (btc_wh >= 55 and eth_wh >= 55):
        return "high"
    if overlap >= 18 or (btc_wh >= 35 or eth_wh >= 35):
        return "medium"
    return "calm"


def synthesis_bucket(stats: Dict[str, Any]) -> str:
    risk = stats.get("risk") or {}
    bybit = stats.get("bybit") or {}
    deribit = stats.get("deribit") or {}

    ge3 = risk.get("market_high_risk_ge3_share_pct") or 0.0
    directional = bybit.get("regime_directional_total_pct") or 0.0
    compression = bybit.get("mci_gt_06_share_pct") or 0.0
    vol_overlap = deribit.get("both_hot_or_warm_share_pct") or 0.0

    options_signal = max(directional, compression)
    vol_signal = vol_overlap
    futures_signal = ge3

    if futures_signal >= 30 and (options_signal >= 25 or vol_signal >= 25):
        return "broad_pressure"
    if futures_signal >= 28 and futures_signal > options_signal + 8 and futures_signal > vol_signal + 8:
        return "futures_led"
    if options_signal >= 28 and options_signal > futures_signal + 8 and options_signal > vol_signal + 6:
        return "options_led"
    if vol_signal >= 28 and vol_signal > futures_signal + 8 and vol_signal > options_signal + 6:
        return "vol_led"
    if futures_signal < 10 and options_signal < 12 and vol_signal < 12:
        return "contained"
    return "mixed"


def build_thread_tweets(stats: Dict[str, Any]) -> List[str]:
    risk = stats.get("risk") or {}
    bybit = stats.get("bybit") or {}
    deribit = stats.get("deribit") or {}

    ge3 = risk.get("market_high_risk_ge3_share_pct") or 0.0
    ge5 = risk.get("market_high_risk_ge5_share_pct") or 0.0
    avg_risk = risk.get("avg_risk") or 0.0
    leaders = top_symbol_names(risk.get("top_symbols_by_risk_ge_3_share_pct") or risk.get("top_symbols_by_avg_risk") or [])

    calm = bybit.get("regime_calm_pct") or 0.0
    directional = bybit.get("regime_directional_total_pct") or 0.0
    compression = bybit.get("mci_gt_06_share_pct") or 0.0

    btc_wh = (deribit.get("btc_hot_pct") or 0.0) + (deribit.get("btc_warm_pct") or 0.0)
    eth_wh = (deribit.get("eth_hot_pct") or 0.0) + (deribit.get("eth_warm_pct") or 0.0)
    overlap = deribit.get("both_hot_or_warm_share_pct") or 0.0

    tw1 = pick_variant(INTRO_VARIANTS, "Livermore monthly snapshot (30d)")

    fb = futures_bucket(ge3, ge5, avg_risk)
    tw2 = (
        f"Futures (30d)\n\n"
        f"High-risk windows (risk≥3): {p(ge3)}\n"
        f"Extreme stress (risk≥5): {p(ge5)}\n"
        f"Most persistent pressure: {leaders}\n\n"
        f"{pick_variant(FUTURES_VARIANTS.get(fb, []), 'Futures stress stayed mixed through the month.')}"
    )

    ob = options_bucket(directional, compression, calm)
    tw3 = (
        f"Options (30d)\n\n"
        f"CALM regime share: {p(calm)}\n"
        f"Directional regimes: {p(directional)}\n"
        f"High-compression windows (>0.6): {p(compression)}\n\n"
        f"{pick_variant(OPTIONS_VARIANTS.get(ob, []), 'Options structure stayed mixed through the month.')}"
    )

    vb = vol_bucket(btc_wh, eth_wh, overlap)
    tw4 = (
        f"Volatility (30d)\n\n"
        f"BTC warm+hot share: {p(btc_wh)}\n"
        f"ETH warm+hot share: {p(eth_wh)}\n"
        f"BTC/ETH warm overlap: {p(overlap)} of windows\n\n"
        f"{pick_variant(VOL_VARIANTS.get(vb, []), 'Volatility stayed mixed through the month.')}"
    )

    sb = synthesis_bucket(stats)
    tw5 = SYNTHESIS_VARIANTS.get(sb, SYNTHESIS_VARIANTS["mixed"])

    tweets = [trim_tweet(tw1), trim_tweet(tw2), trim_tweet(tw3), trim_tweet(tw4), trim_tweet(tw5)]
    return tweets
