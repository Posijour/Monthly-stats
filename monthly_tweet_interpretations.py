import random
import re
from typing import Any, Dict, List, Optional, Tuple

INTRO_VARIANTS = [
    "Livermore monthly snapshot (30d)\n\n30-day structural view across:\n\n• futures positioning\n• options expectations\n• volatility background",
    "Livermore monthly snapshot (30d)\n\n30-day structural read across:\n\n• futures positioning\n• options expectations\n• volatility background",
]

SYNTHESIS_VARIANTS = {
    "contained": (
        "Structural takeaway:\n\n"
        "The 30d profile stayed contained.\n\n"
        "Pressure signals were limited and never aligned strongly enough to suggest a broader regime shift."
    ),
    "mixed": (
        "Structural takeaway:\n\n"
        "The month stayed mixed.\n\n"
        "Stress appeared across layers, but persistence and alignment remained uneven."
    ),
    "futures_led": (
        "Structural takeaway:\n\n"
        "Futures carried the clearest sign of pressure.\n\n"
        "Crowding repeated more consistently than confirmation from options or volatility."
    ),
    "options_led": (
        "Structural takeaway:\n\n"
        "The options layer carried more of the structural signal.\n\n"
        "Directional regimes and compression were clearer than confirmation from futures."
    ),
    "vol_led": (
        "Structural takeaway:\n\n"
        "The volatility backdrop carried more of the month than futures positioning did.\n\n"
        "Elevated vol conditions were clearer than broad crowding in futures."
    ),
    "broad_pressure": (
        "Structural takeaway:\n\n"
        "Pressure was not confined to one layer.\n\n"
        "Futures stress, options structure, and the volatility backdrop aligned often enough to matter at the monthly horizon."
    ),
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
    leaders = top_symbol_names(
        risk.get("top_symbols_by_risk_ge_3_share_pct") or risk.get("top_symbols_by_avg_risk") or []
    )

    calm = bybit.get("regime_calm_pct") or 0.0
    directional = bybit.get("regime_directional_total_pct") or 0.0
    compression = bybit.get("mci_gt_06_share_pct") or 0.0

    btc_wh = (deribit.get("btc_hot_pct") or 0.0) + (deribit.get("btc_warm_pct") or 0.0)
    eth_wh = (deribit.get("eth_hot_pct") or 0.0) + (deribit.get("eth_warm_pct") or 0.0)
    overlap = deribit.get("both_hot_or_warm_share_pct") or 0.0

    tw1 = pick_variant(INTRO_VARIANTS, "Livermore monthly snapshot (30d)")

    tw2 = (
        f"Futures (30d)\n\n"
        f"High-risk windows (risk≥3): {p(ge3)}\n"
        f"Extreme stress (risk≥5): {p(ge5)}\n"
        f"Most persistent pressure: {leaders}"
    )

    tw3 = (
        f"Options (30d)\n\n"
        f"CALM regime share: {p(calm)}\n"
        f"Directional regimes: {p(directional)}\n"
        f"High-compression windows (>0.6): {p(compression)}"
    )

    tw4 = (
        f"Volatility (30d)\n\n"
        f"BTC warm+hot share: {p(btc_wh)}\n"
        f"ETH warm+hot share: {p(eth_wh)}\n"
        f"BTC/ETH warm overlap: {p(overlap)} of windows"
    )

    sb = synthesis_bucket(stats)
    tw5 = SYNTHESIS_VARIANTS.get(sb, SYNTHESIS_VARIANTS["mixed"])

    tweets = [trim_tweet(tw1), trim_tweet(tw2), trim_tweet(tw3), trim_tweet(tw4), trim_tweet(tw5)]
    return tweets
