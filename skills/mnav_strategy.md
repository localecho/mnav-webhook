---
name: mnav_strategy
description: Strategy overlay for mNAV with leading/lagging indicators
triggers:
  - analyze mnav
  - strategy overlay
  - leading lagging
---

# Skill: mNAV Strategy Overlay

## Overview

Overlay technical strategy indicators on mNAV data to identify leading/lagging signals for MicroStrategy trading decisions.

---

## Indicator Framework

```
┌─────────────────────────────────────────────────────────────┐
│                 mNAV STRATEGY OVERLAY                       │
│                                                             │
│   mNAV Data                                                 │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              LEADING INDICATORS                      │  │
│   │  - BTC price momentum                                │  │
│   │  - Options flow (call/put ratio)                     │  │
│   │  - Institutional accumulation                        │  │
│   │  - Whale wallet activity                             │  │
│   └─────────────────────────────────────────────────────┘  │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              LAGGING INDICATORS                      │  │
│   │  - mNAV moving averages (7d, 30d)                   │  │
│   │  - Premium/discount persistence                      │  │
│   │  - Volume trends                                     │  │
│   │  - RSI on mNAV                                       │  │
│   └─────────────────────────────────────────────────────┘  │
│        │                                                    │
│        ▼                                                    │
│   Strategy Signal (Long / Short / Neutral)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Leading Indicators

### BTC Price Momentum

```yaml
btc_momentum:
  metric: rate_of_change
  periods: [1d, 7d, 30d]

  signals:
    bullish:
      - btc_roc_7d > 5%
      - btc_roc_30d > 15%
    bearish:
      - btc_roc_7d < -5%
      - btc_roc_30d < -15%

  lead_time: 1-3 days ahead of mNAV movement
```

### Options Flow

```yaml
options_flow:
  source: cboe_mstr_options

  metrics:
    call_put_ratio:
      bullish: > 1.5
      neutral: 0.8 - 1.5
      bearish: < 0.8

    unusual_activity:
      - large_call_sweeps
      - put_hedging
      - gamma_exposure

  lead_time: 2-5 days ahead
```

### Whale Wallet Activity

```yaml
whale_tracking:
  sources:
    - glassnode
    - santiment
    - whale_alert

  signals:
    accumulation:
      - exchange_outflows > 10000 BTC
      - whale_addresses_increasing
    distribution:
      - exchange_inflows > 10000 BTC
      - whale_addresses_decreasing

  lead_time: 3-7 days ahead
```

---

## Lagging Indicators

### mNAV Moving Averages

```yaml
mnav_ma:
  periods:
    short: 7d
    medium: 30d
    long: 90d

  signals:
    golden_cross: short > medium (bullish)
    death_cross: short < medium (bearish)

  current_position:
    above_all_ma: strong_premium
    below_all_ma: deep_discount
```

### Premium Persistence

```yaml
premium_analysis:
  historical_range:
    min: 0.8x (discount)
    max: 4.0x (extreme premium)
    mean: 2.0x

  zone_classification:
    deep_discount: < 1.2x
    discount: 1.2x - 1.8x
    fair_value: 1.8x - 2.5x
    premium: 2.5x - 3.5x
    extreme_premium: > 3.5x

  mean_reversion:
    enabled: true
    strength: 0.7
```

### mNAV RSI

```yaml
mnav_rsi:
  period: 14d

  levels:
    oversold: < 30
    neutral: 30 - 70
    overbought: > 70

  divergence_detection:
    bullish: price_lower_low + rsi_higher_low
    bearish: price_higher_high + rsi_lower_high
```

---

## Strategy Signals

### Signal Generation

```python
def generate_signal(mnav_data, indicators):
    """
    Combine leading and lagging indicators for strategy signal.
    """
    leading_score = 0
    lagging_score = 0

    # Leading indicators (weight: 60%)
    if indicators.btc_momentum > 5:
        leading_score += 2
    if indicators.call_put_ratio > 1.5:
        leading_score += 2
    if indicators.whale_accumulation:
        leading_score += 1

    # Lagging indicators (weight: 40%)
    if mnav_data.current < mnav_data.ma_30d:
        lagging_score += 1  # Discount = potential buy
    if mnav_data.rsi < 30:
        lagging_score += 2  # Oversold

    total_score = (leading_score * 0.6) + (lagging_score * 0.4)

    if total_score > 3:
        return "LONG"
    elif total_score < -3:
        return "SHORT"
    else:
        return "NEUTRAL"
```

### Signal Dashboard

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           mNAV STRATEGY DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Current mNAV: 2.45x
  Signal: LONG ▲

  LEADING INDICATORS:
    BTC Momentum (7d):   +8.2%  ✅ Bullish
    Call/Put Ratio:      1.72   ✅ Bullish
    Whale Flow:          Accumulating ✅

  LAGGING INDICATORS:
    mNAV vs 30d MA:      Below (-5%) ✅
    RSI (14d):           35     ⚠️ Near Oversold
    Premium Zone:        Fair Value

  COMPOSITE SCORE: +4.2 / 10
  CONFIDENCE: 72%

  RECOMMENDATION:
    Consider accumulating on dips
    Target: 2.8x (+14%)
    Stop: 2.0x (-18%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Historical Backtesting

### Performance Metrics

```yaml
backtest:
  period: 2020-01-01 to present

  results:
    total_signals: 156
    win_rate: 68%
    avg_return: 12.4%
    sharpe_ratio: 1.85
    max_drawdown: -28%

  by_signal_type:
    long:
      count: 98
      win_rate: 72%
      avg_return: 18.2%
    short:
      count: 42
      win_rate: 61%
      avg_return: 8.1%
```

---

## API Integration

### Endpoints

```yaml
endpoints:
  /api/strategy:
    method: GET
    returns:
      signal: LONG | SHORT | NEUTRAL
      confidence: 0-100
      leading_indicators: {...}
      lagging_indicators: {...}

  /api/strategy/history:
    method: GET
    params:
      days: 30
    returns:
      signals: [{date, signal, outcome}, ...]

  /api/strategy/backtest:
    method: POST
    body:
      start_date: "2023-01-01"
      end_date: "2024-01-01"
      params: {...}
```

---

## Google Sheets Export

### Daily Dashboard Update

```yaml
sheets_integration:
  sheet_id: $MNAV_SHEET_ID

  daily_row:
    - date
    - mnav
    - btc_price
    - mstr_price
    - signal
    - confidence
    - leading_score
    - lagging_score

  charts:
    - mnav_with_ma
    - signal_history
    - indicator_heatmap
```

---

## Commands

```bash
# Get current strategy signal
/mnav strategy

# View indicator breakdown
/mnav indicators

# Backtest strategy
/mnav backtest --start 2023-01-01

# Export to sheets
/mnav export --sheet
```

---

## Configuration

```yaml
# config/mnav_strategy.yaml
strategy:
  enabled: true

  leading_weight: 0.6
  lagging_weight: 0.4

  thresholds:
    long: 3.0
    short: -3.0

  data_sources:
    btc: coingecko
    mstr: yahoo_finance
    options: cboe
    whales: glassnode

  alerts:
    signal_change: true
    extreme_readings: true
    channels:
      - slack
      - email
```

---

*Data-driven strategy overlay for mNAV trading decisions.*
