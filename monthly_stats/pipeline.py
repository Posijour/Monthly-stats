from datetime import timedelta
from typing import Any, Dict, List, Optional

from monthly_stats.config import PAGE_SIZE, SUPABASE_KEY, SUPABASE_URL
from monthly_stats.parsing import normalize_row
from monthly_stats.stats import compute_all_stats
from monthly_stats.supabase_client import (
    fetch_existing_monthly_row,
    fetch_logs_paginated,
    save_monthly_stats_row,
    update_monthly_stats_twitter_fields,
)
from monthly_stats.twitter_client import post_thread_tweets, validate_thread_tweets
from monthly_stats.utils import dt_to_unix_ms, now_utc, safe_int
from monthly_tweet_interpretations import build_thread_tweets


def should_skip_twitter_post(existing_row: Optional[Dict[str, Any]]) -> bool:
    if not existing_row:
        return False
    root_tweet_id = existing_row.get("root_tweet_id")
    tweet_count = safe_int(existing_row.get("tweet_count"), default=0) or 0
    return bool(root_tweet_id) or tweet_count > 0


def run_monthly_job(window_days: int = 30) -> List[str]:
    end_dt = now_utc()
    start_dt = end_dt - timedelta(days=window_days)

    start_ts_ms = dt_to_unix_ms(start_dt)
    end_ts_ms = dt_to_unix_ms(end_dt)

    print(f"[window] {window_days}d")
    print(f"[from]   {start_dt.isoformat()}")
    print(f"[to]     {end_dt.isoformat()}")

    raw_rows = fetch_logs_paginated(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        start_ts_ms=start_ts_ms,
        end_ts_ms=end_ts_ms,
        page_size=PAGE_SIZE,
    )

    rows = [normalize_row(r) for r in raw_rows]
    rows = [r for r in rows if r["ts_ms"] is not None]

    print(f"[rows raw] {len(raw_rows)}")
    print(f"[rows normalized] {len(rows)}")

    stats = compute_all_stats(rows=rows, window_days=window_days, start_dt=start_dt, end_dt=end_dt)
    tweets = build_thread_tweets(stats)

    risk = stats.get("risk") or {}
    bybit = stats.get("bybit") or {}
    deribit = stats.get("deribit") or {}

    print(f"[metrics] rows_total={stats.get('rows_total')}")
    print(f"[metrics] risk_ge_3_share_pct={risk.get('market_high_risk_ge3_share_pct')}")
    print(f"[metrics] risk_ge_5_share_pct={risk.get('market_high_risk_ge5_share_pct')}")
    print(f"[metrics] bybit_regime_calm_pct={bybit.get('regime_calm_pct')}")
    print(f"[metrics] bybit_regime_directional_total_pct={bybit.get('regime_directional_total_pct')}")
    print(f"[metrics] bybit_mci_gt_06_share_pct={bybit.get('mci_gt_06_share_pct')}")
    print(f"[metrics] deribit_btc_eth_elevated_share_pct={deribit.get('both_hot_or_warm_share_pct')}")

    print("\n" + "=" * 80)
    print("THREAD")
    print("=" * 80)
    for i, tw in enumerate(tweets, start=1):
        print(f"\n----- TWEET {i} | len={len(tw)} -----\n")
        print(tw)

    period_start_iso = stats.get("from_utc")
    period_end_iso = stats.get("to_utc")
    existing_row = None
    if period_start_iso and period_end_iso:
        existing_row = fetch_existing_monthly_row(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            period_start_iso=period_start_iso,
            period_end_iso=period_end_iso,
        )

    if should_skip_twitter_post(existing_row):
        print("Twitter thread already posted for this period, skipping", flush=True)
        return []

    saved = existing_row or save_monthly_stats_row(stats=stats, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY, tweet_ids=[])
    print(f"[supabase] monthly_stats row saved id={saved.get('id', 'n/a')}")

    is_valid, validation_errors = validate_thread_tweets(tweets)
    if not is_valid:
        print(f"[thread validation] failed: {validation_errors}", flush=True)
        raise RuntimeError("Thread validation failed, skipping Twitter posting")

    try:
        tweet_ids = post_thread_tweets(tweets)
        print(f"[twitter] posted_thread_ids={tweet_ids}")
    except Exception as twitter_error:
        print(f"[twitter] failed after monthly_stats save: {twitter_error}", flush=True)
        raise

    saved_id = saved.get("id") if isinstance(saved, dict) else None
    if saved_id:
        updated = update_monthly_stats_twitter_fields(
            row_id=saved_id,
            tweet_ids=tweet_ids,
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
        )
        print(f"[supabase] monthly_stats twitter fields updated id={updated.get('id', saved_id)}")

    return tweet_ids


def main() -> None:
    run_monthly_job(window_days=30)
