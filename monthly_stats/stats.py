from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

from monthly_stats.config import DERIBIT_EVENT_NAMES
from monthly_stats.utils import compact_pct, hour_bucket_from_ms, mean, median, safe_float, ten_min_bucket_from_ms, top_items


def compute_risk_stats(rows: List[Dict[str, Any]], start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    del start_dt, end_dt
    risk_rows = [r for r in rows if r["event"] == "risk_eval"]

    symbols = sorted({r["symbol"] for r in risk_rows if r["symbol"]})
    risk_values: List[float] = []
    max_risk = None

    per_symbol_risks: Dict[str, List[float]] = defaultdict(list)
    per_symbol_obs: Counter = Counter()
    per_symbol_ge_2: Counter = Counter()
    per_symbol_ge_3: Counter = Counter()
    per_symbol_ge_4: Counter = Counter()
    per_symbol_ge_5: Counter = Counter()

    market_high_risk_hours: Dict[str, set] = {
        "risk_ge_2": set(),
        "risk_ge_3": set(),
        "risk_ge_4": set(),
        "risk_ge_5": set(),
    }

    unique_risk_hours_total: set = set()

    for r in risk_rows:
        risk = safe_float(r["data"].get("risk"))
        if risk is None:
            continue

        sym = str(r["symbol"])
        hour_bucket = hour_bucket_from_ms(r["ts_ms"])
        unique_risk_hours_total.add(hour_bucket)

        risk_values.append(risk)
        per_symbol_risks[sym].append(risk)
        per_symbol_obs[sym] += 1

        if risk >= 2:
            market_high_risk_hours["risk_ge_2"].add(hour_bucket)
            per_symbol_ge_2[sym] += 1
        if risk >= 3:
            market_high_risk_hours["risk_ge_3"].add(hour_bucket)
            per_symbol_ge_3[sym] += 1
        if risk >= 4:
            market_high_risk_hours["risk_ge_4"].add(hour_bucket)
            per_symbol_ge_4[sym] += 1
        if risk >= 5:
            market_high_risk_hours["risk_ge_5"].add(hour_bucket)
            per_symbol_ge_5[sym] += 1

        if max_risk is None or risk > max_risk:
            max_risk = risk

    avg_risk = mean(risk_values)
    med_risk = median(risk_values)
    total_hours = len(unique_risk_hours_total)

    per_symbol_avg = {sym: mean(vals) for sym, vals in per_symbol_risks.items() if vals}
    per_symbol_ge_3_share = {
        sym: round(100.0 * per_symbol_ge_3[sym] / per_symbol_obs[sym], 1)
        for sym in per_symbol_obs
        if per_symbol_obs[sym] > 0
    }

    def top_symbol(counter: Counter) -> Any:
        if not counter:
            return None
        return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]

    return {
        "rows": len(risk_rows),
        "symbols_count": len(symbols),
        "symbols": symbols,
        "avg_risk": round(avg_risk, 3) if avg_risk is not None else None,
        "median_risk": round(med_risk, 3) if med_risk is not None else None,
        "max_risk": round(max_risk, 3) if max_risk is not None else None,
        "top_symbols_by_avg_risk": top_items(per_symbol_avg, n=5, round_digits=3),
        "top_symbols_by_risk_ge_3_share_pct": top_items(per_symbol_ge_3_share, n=5, round_digits=1),
        "market_high_risk_hours": {k: len(v) for k, v in market_high_risk_hours.items()},
        "unique_risk_hours_total": total_hours,
        "market_high_risk_ge2_share_pct": compact_pct(len(market_high_risk_hours["risk_ge_2"]), total_hours),
        "market_high_risk_ge3_share_pct": compact_pct(len(market_high_risk_hours["risk_ge_3"]), total_hours),
        "market_high_risk_ge4_share_pct": compact_pct(len(market_high_risk_hours["risk_ge_4"]), total_hours),
        "market_high_risk_ge5_share_pct": compact_pct(len(market_high_risk_hours["risk_ge_5"]), total_hours),
        "symbol_high_risk_ge2": top_symbol(per_symbol_ge_2),
        "symbol_high_risk_ge3": top_symbol(per_symbol_ge_3),
        "symbol_high_risk_ge4": top_symbol(per_symbol_ge_4),
        "symbol_high_risk_ge5": top_symbol(per_symbol_ge_5),
    }


def extract_alert_type(data: Dict[str, Any]) -> str:
    candidates = [
        data.get("alert_type"),
        data.get("type"),
        data.get("event_type"),
        data.get("divergence_type"),
        data.get("alert"),
        data.get("name"),
        data.get("signal"),
        data.get("kind"),
    ]
    for c in candidates:
        if c is not None and str(c).strip():
            return str(c).strip()

    if data.get("divergence"):
        return f"divergence:{data.get('divergence')}"
    if data.get("buildup_type"):
        return f"buildup:{data.get('buildup_type')}"

    return "unknown_alert"


def compute_alert_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    alert_rows = [r for r in rows if r["event"] == "alert_sent"]

    type_counter = Counter()
    dedup_hour_counter = Counter()
    dedup_symbol_counter = Counter()

    for r in alert_rows:
        alert_type = extract_alert_type(r["data"])
        symbol = str(r["data"].get("symbol") or r.get("symbol") or "UNKNOWN")
        hb = hour_bucket_from_ms(r["ts_ms"])
        
        type_counter[alert_type] += 1
        dedup_hour_counter[(symbol, alert_type, hb)] += 1

    dedup_type_counter = Counter()
    for (symbol, alert_type, _hb), _cnt in dedup_hour_counter.items():
        dedup_type_counter[alert_type] += 1
        dedup_symbol_counter[symbol] += 1

    return {
        "rows": len(alert_rows),
        "top_alert_types_dedup_1h": top_items(dict(dedup_type_counter), n=10),
        "top_symbols_dedup_1h": top_items(dict(dedup_symbol_counter), n=10),
        "top_alert_types_raw": top_items(dict(type_counter), n=10),
    }


def compute_bybit_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    bybit_rows = [r for r in rows if r["event"] == "bybit_market_state"]

    mci_vals = []
    slope_vals = []
    conf_vals = []
    regime_counter = Counter()
    phase_counter = Counter()

    above_06 = 0
    valid_mci_count = 0
    prev_regime = None
    regime_transitions = Counter()

    for r in bybit_rows:
        d = r["data"]

        mci = safe_float(d.get("mci"))
        slope = safe_float(d.get("mci_slope"))
        conf = safe_float(d.get("confidence"))
        regime = d.get("regime")
        phase = d.get("mci_phase")

        if mci is not None:
            mci_vals.append(mci)
            valid_mci_count += 1
            if mci > 0.6:
                above_06 += 1

        if slope is not None:
            slope_vals.append(slope)
        if conf is not None:
            conf_vals.append(conf)

        if regime:
            regime = str(regime)
            regime_counter[regime] += 1
            if prev_regime is not None and prev_regime != regime:
                regime_transitions[f"{prev_regime}->{regime}"] += 1
            prev_regime = regime

        if phase:
            phase_counter[str(phase)] += 1

    total_regimes = sum(regime_counter.values())
    total_phases = sum(phase_counter.values())
    regime_share = {k: compact_pct(v, total_regimes) for k, v in regime_counter.items()}

    regime_share_lc = {str(k).lower(): v for k, v in regime_share.items()}
    regime_directional_up_pct = regime_share_lc.get("directional_up", 0.0)
    regime_directional_down_pct = regime_share_lc.get("directional_down", 0.0)

    return {
        "rows": len(bybit_rows),
        "avg_mci": round(mean(mci_vals), 4) if mci_vals else None,
        "median_mci": round(median(mci_vals), 4) if mci_vals else None,
        "max_mci": round(max(mci_vals), 4) if mci_vals else None,
        "avg_mci_slope": round(mean(slope_vals), 4) if slope_vals else None,
        "avg_confidence": round(mean(conf_vals), 4) if conf_vals else None,
        "mci_gt_06_share_pct": compact_pct(above_06, valid_mci_count),
        "regime_share_pct": regime_share,
        "phase_share_pct": {k: compact_pct(v, total_phases) for k, v in phase_counter.items()},
        "top_regime_transitions": top_items(dict(regime_transitions), n=10),
        "regime_calm_pct": regime_share_lc.get("calm", 0.0),
        "regime_uncertain_pct": regime_share_lc.get("uncertain", 0.0),
        "regime_directional_up_pct": regime_directional_up_pct,
        "regime_directional_down_pct": regime_directional_down_pct,
        "regime_directional_total_pct": round(regime_directional_up_pct + regime_directional_down_pct, 1),
    }


def compute_okx_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    okx_rows = [r for r in rows if r["event"] == "okx_market_state"]

    olsi_vals = []
    slope_vals = []
    diff_vals = []

    divergence_counter = Counter()
    phase_div_counter = Counter()
    dedup_divergence_1h = Counter()

    for r in okx_rows:
        d = r["data"]

        olsi = safe_float(d.get("okx_olsi_avg")) if d.get("okx_olsi_avg") is not None else safe_float(d.get("olsi"))
        slope = safe_float(d.get("okx_olsi_slope")) if d.get("okx_olsi_slope") is not None else safe_float(d.get("olsi_slope"))
        div_diff = safe_float(d.get("divergence_diff"))

        div_type = d.get("divergence_type")
        phase_div = d.get("phase_divergence")

        if olsi is not None:
            olsi_vals.append(olsi)
        if slope is not None:
            slope_vals.append(slope)
        if div_diff is not None:
            diff_vals.append(div_diff)

        if div_type:
            div_type = str(div_type)
            divergence_counter[div_type] += 1
            dedup_divergence_1h[(div_type, hour_bucket_from_ms(r["ts_ms"]))] += 1

        if phase_div:
            phase_div_counter[str(phase_div)] += 1

    dedup_type_counter = Counter()
    for (div_type, _hb), _cnt in dedup_divergence_1h.items():
        dedup_type_counter[div_type] += 1

    dominant_div = top_items(dict(dedup_type_counter), n=1)
    dominant_div_name = dominant_div[0][0] if dominant_div else None

    return {
        "rows": len(okx_rows),
        "avg_olsi": round(mean(olsi_vals), 4) if olsi_vals else None,
        "median_olsi": round(median(olsi_vals), 4) if olsi_vals else None,
        "max_olsi": round(max(olsi_vals), 4) if olsi_vals else None,
        "avg_olsi_slope": round(mean(slope_vals), 4) if slope_vals else None,
        "avg_divergence_diff": round(mean(diff_vals), 4) if diff_vals else None,
        "divergence_types_raw": top_items(dict(divergence_counter), n=10),
        "divergence_types_dedup_1h": top_items(dict(dedup_type_counter), n=10),
        "phase_divergence_counts": top_items(dict(phase_div_counter), n=10),
        "divergence_calm_dominant": str(dominant_div_name).lower() == "calm" if dominant_div_name is not None else False,
    }


def compute_deribit_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    deribit_rows = [r for r in rows if r["event"] in DERIBIT_EVENT_NAMES]

    by_symbol = defaultdict(list)
    for r in deribit_rows:
        by_symbol[r["symbol"]].append(r)

    result: Dict[str, Any] = {
        "rows": len(deribit_rows),
        "symbols": {},
        "both_hot_or_warm_share_pct": 0.0,
        "btc_vbi": None,
        "eth_vbi": None,
        "btc_hot_pct": 0.0,
        "btc_warm_pct": 0.0,
        "btc_cold_pct": 0.0,
        "eth_hot_pct": 0.0,
        "eth_warm_pct": 0.0,
        "eth_cold_pct": 0.0,
    }

    bucket_state_map: Dict[str, Dict[str, str]] = defaultdict(dict)

    for sym, sym_rows in by_symbol.items():
        vbi_scores = []
        iv_slopes = []
        skews = []
        curvatures = []
        state_counter = Counter()

        for r in sym_rows:
            d = r["data"]
            vbi = safe_float(d.get("vbi_score"))
            iv_slope = safe_float(d.get("iv_slope"))
            skew = safe_float(d.get("skew"))
            curvature = safe_float(d.get("curvature"))
            state = d.get("vbi_state")

            if vbi is not None:
                vbi_scores.append(vbi)
            if iv_slope is not None:
                iv_slopes.append(iv_slope)
            if skew is not None:
                skews.append(skew)
            if curvature is not None:
                curvatures.append(curvature)
            if state:
                state = str(state).upper()
                state_counter[state] += 1
                bucket_state_map[ten_min_bucket_from_ms(r["ts_ms"])][sym] = state

        total_states = sum(state_counter.values())
        avg_vbi = round(mean(vbi_scores), 4) if vbi_scores else None
        state_share = {k: compact_pct(v, total_states) for k, v in state_counter.items()}
    
        result["symbols"][sym] = {
            "rows": len(sym_rows),
            "avg_vbi_score": avg_vbi,
            "max_vbi_score": round(max(vbi_scores), 4) if vbi_scores else None,
            "avg_iv_slope": round(mean(iv_slopes), 4) if iv_slopes else None,
            "avg_skew": round(mean(skews), 4) if skews else None,
            "avg_curvature": round(mean(curvatures), 4) if curvatures else None,
            "state_share_pct": state_share,
        }

        if sym == "BTC":
            result["btc_vbi"] = avg_vbi
            result["btc_hot_pct"] = state_share.get("HOT", 0.0)
            result["btc_warm_pct"] = state_share.get("WARM", 0.0)
            result["btc_cold_pct"] = state_share.get("COLD", 0.0)
        if sym == "ETH":
            result["eth_vbi"] = avg_vbi
            result["eth_hot_pct"] = state_share.get("HOT", 0.0)
            result["eth_warm_pct"] = state_share.get("WARM", 0.0)
            result["eth_cold_pct"] = state_share.get("COLD", 0.0)

    joint_buckets = 0
    elevated_buckets = 0
    elevated_states = {"HOT", "WARM"}

    for _bucket, sym_map in bucket_state_map.items():
        if "BTC" in sym_map and "ETH" in sym_map:
            joint_buckets += 1
            if sym_map["BTC"] in elevated_states and sym_map["ETH"] in elevated_states:
                elevated_buckets += 1

    result["both_hot_or_warm_share_pct"] = compact_pct(elevated_buckets, joint_buckets)
    return result


def compute_all_stats(rows: List[Dict[str, Any]], window_days: int, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    event_counts = Counter(r["event"] for r in rows)

    return {
        "window_days": window_days,
        "from_utc": start_dt.isoformat(),
        "to_utc": end_dt.isoformat(),
        "rows_total": len(rows),
        "event_counts": dict(event_counts),
        "risk": compute_risk_stats(rows, start_dt=start_dt, end_dt=end_dt),
        "alerts": compute_alert_stats(rows),
        "bybit": compute_bybit_stats(rows),
        "okx": compute_okx_stats(rows),
        "deribit": compute_deribit_stats(rows),
    }
