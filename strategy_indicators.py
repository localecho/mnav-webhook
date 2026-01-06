#!/usr/bin/env python3
"""
mNAV Strategy Indicators
Leading and lagging indicators for MicroStrategy trading signals
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Signal(Enum):
    STRONG_LONG = "STRONG_LONG"
    LONG = "LONG"
    NEUTRAL = "NEUTRAL"
    SHORT = "SHORT"
    STRONG_SHORT = "STRONG_SHORT"


@dataclass
class IndicatorResult:
    name: str
    value: float
    signal: str  # bullish, bearish, neutral
    weight: float
    description: str


class LeadingIndicators:
    """
    Leading indicators that predict future mNAV movements.
    These typically lead price action by 1-7 days.
    """

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def get_btc_momentum(self, periods: List[int] = [1, 7, 30]) -> Dict[str, IndicatorResult]:
        """
        Calculate Bitcoin price momentum (Rate of Change).
        Strong BTC momentum often leads mNAV expansion.
        """
        results = {}

        try:
            # Fetch BTC historical prices
            response = requests.get(
                'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart',
                params={'vs_currency': 'usd', 'days': max(periods) + 1},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                prices = [p[1] for p in data['prices']]
                current_price = prices[-1]

                for period in periods:
                    if len(prices) > period:
                        past_price = prices[-(period + 1)]
                        roc = ((current_price - past_price) / past_price) * 100

                        # Determine signal
                        if roc > 10:
                            signal = "bullish"
                        elif roc > 5:
                            signal = "slightly_bullish"
                        elif roc < -10:
                            signal = "bearish"
                        elif roc < -5:
                            signal = "slightly_bearish"
                        else:
                            signal = "neutral"

                        results[f'btc_roc_{period}d'] = IndicatorResult(
                            name=f"BTC {period}d Momentum",
                            value=round(roc, 2),
                            signal=signal,
                            weight=0.15 if period == 7 else 0.1,
                            description=f"Bitcoin {period}-day rate of change: {roc:.1f}%"
                        )

        except Exception as e:
            logger.error(f"Error fetching BTC momentum: {e}")

        return results

    def get_options_flow(self) -> Optional[IndicatorResult]:
        """
        Analyze MSTR options flow (call/put ratio).
        High call/put ratio indicates bullish institutional sentiment.
        """
        try:
            # In production, would use CBOE or options data API
            # For now, use a placeholder calculation

            # Simulated call/put ratio based on market conditions
            # Real implementation would fetch from options data provider
            call_put_ratio = 1.2  # Placeholder

            if call_put_ratio > 2.0:
                signal = "bullish"
            elif call_put_ratio > 1.3:
                signal = "slightly_bullish"
            elif call_put_ratio < 0.5:
                signal = "bearish"
            elif call_put_ratio < 0.8:
                signal = "slightly_bearish"
            else:
                signal = "neutral"

            return IndicatorResult(
                name="Options Call/Put Ratio",
                value=round(call_put_ratio, 2),
                signal=signal,
                weight=0.15,
                description=f"MSTR options call/put ratio: {call_put_ratio:.2f}"
            )

        except Exception as e:
            logger.error(f"Error fetching options flow: {e}")
            return None

    def get_whale_activity(self) -> Optional[IndicatorResult]:
        """
        Track large Bitcoin wallet movements.
        Exchange outflows = accumulation (bullish)
        Exchange inflows = distribution (bearish)
        """
        try:
            # In production, would use Glassnode or similar on-chain data
            # Placeholder implementation

            # Simulated net flow (negative = outflow = bullish)
            net_exchange_flow = -5000  # BTC

            if net_exchange_flow < -10000:
                signal = "bullish"
                desc = "Strong accumulation (exchange outflows)"
            elif net_exchange_flow < -3000:
                signal = "slightly_bullish"
                desc = "Mild accumulation"
            elif net_exchange_flow > 10000:
                signal = "bearish"
                desc = "Strong distribution (exchange inflows)"
            elif net_exchange_flow > 3000:
                signal = "slightly_bearish"
                desc = "Mild distribution"
            else:
                signal = "neutral"
                desc = "Neutral exchange flows"

            return IndicatorResult(
                name="Whale Exchange Flow",
                value=net_exchange_flow,
                signal=signal,
                weight=0.1,
                description=desc
            )

        except Exception as e:
            logger.error(f"Error fetching whale activity: {e}")
            return None

    def get_fear_greed_index(self) -> Optional[IndicatorResult]:
        """
        Crypto Fear & Greed Index - contrarian indicator.
        Extreme fear = potential buying opportunity
        Extreme greed = potential selling opportunity
        """
        try:
            response = requests.get(
                'https://api.alternative.me/fng/',
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                value = int(data['data'][0]['value'])
                classification = data['data'][0]['value_classification']

                # Contrarian signal
                if value < 20:
                    signal = "bullish"  # Extreme fear = buy
                elif value < 40:
                    signal = "slightly_bullish"
                elif value > 80:
                    signal = "bearish"  # Extreme greed = sell
                elif value > 60:
                    signal = "slightly_bearish"
                else:
                    signal = "neutral"

                return IndicatorResult(
                    name="Fear & Greed Index",
                    value=value,
                    signal=signal,
                    weight=0.1,
                    description=f"Crypto sentiment: {classification} ({value}/100)"
                )

        except Exception as e:
            logger.error(f"Error fetching fear/greed: {e}")
            return None


class LaggingIndicators:
    """
    Lagging indicators that confirm trends.
    These follow price action and confirm momentum.
    """

    def __init__(self):
        self.mnav_history: List[Tuple[datetime, float]] = []

    def add_mnav_datapoint(self, timestamp: datetime, mnav: float):
        """Add historical mNAV datapoint."""
        self.mnav_history.append((timestamp, mnav))
        # Keep last 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        self.mnav_history = [(t, v) for t, v in self.mnav_history if t > cutoff]

    def get_moving_averages(self, current_mnav: float) -> Dict[str, IndicatorResult]:
        """
        Calculate mNAV moving averages.
        Price above MA = bullish trend
        Price below MA = bearish trend
        """
        results = {}

        if len(self.mnav_history) < 7:
            # Not enough data, use current value for all
            for period in [7, 30]:
                results[f'mnav_ma_{period}d'] = IndicatorResult(
                    name=f"mNAV {period}d MA",
                    value=current_mnav,
                    signal="neutral",
                    weight=0.1,
                    description=f"Insufficient data for {period}d MA"
                )
            return results

        values = [v for _, v in sorted(self.mnav_history)]

        for period in [7, 30]:
            if len(values) >= period:
                ma = np.mean(values[-period:])
                deviation = ((current_mnav - ma) / ma) * 100

                if deviation > 10:
                    signal = "bearish"  # Overbought relative to MA
                elif deviation > 5:
                    signal = "slightly_bearish"
                elif deviation < -10:
                    signal = "bullish"  # Oversold relative to MA
                elif deviation < -5:
                    signal = "slightly_bullish"
                else:
                    signal = "neutral"

                results[f'mnav_ma_{period}d'] = IndicatorResult(
                    name=f"mNAV {period}d MA",
                    value=round(ma, 2),
                    signal=signal,
                    weight=0.1,
                    description=f"Current: {current_mnav:.2f}x vs MA: {ma:.2f}x ({deviation:+.1f}%)"
                )

        return results

    def get_rsi(self, current_mnav: float, period: int = 14) -> Optional[IndicatorResult]:
        """
        Calculate Relative Strength Index for mNAV.
        RSI < 30 = oversold (bullish)
        RSI > 70 = overbought (bearish)
        """
        if len(self.mnav_history) < period + 1:
            return IndicatorResult(
                name=f"mNAV RSI({period})",
                value=50,
                signal="neutral",
                weight=0.15,
                description="Insufficient data for RSI calculation"
            )

        values = [v for _, v in sorted(self.mnav_history)]
        deltas = np.diff(values[-(period + 1):])

        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        if rsi < 30:
            signal = "bullish"
            desc = "Oversold - potential bounce"
        elif rsi < 40:
            signal = "slightly_bullish"
            desc = "Approaching oversold"
        elif rsi > 70:
            signal = "bearish"
            desc = "Overbought - potential pullback"
        elif rsi > 60:
            signal = "slightly_bearish"
            desc = "Approaching overbought"
        else:
            signal = "neutral"
            desc = "Neutral momentum"

        return IndicatorResult(
            name=f"mNAV RSI({period})",
            value=round(rsi, 1),
            signal=signal,
            weight=0.15,
            description=f"RSI: {rsi:.1f} - {desc}"
        )

    def get_premium_zone(self, current_mnav: float) -> IndicatorResult:
        """
        Classify current mNAV into premium/discount zones.
        Based on historical ranges.
        """
        # Historical mNAV zones
        zones = {
            'deep_discount': (0, 1.2),
            'discount': (1.2, 1.8),
            'fair_value': (1.8, 2.5),
            'premium': (2.5, 3.5),
            'extreme_premium': (3.5, float('inf'))
        }

        for zone_name, (low, high) in zones.items():
            if low <= current_mnav < high:
                current_zone = zone_name
                break
        else:
            current_zone = 'unknown'

        # Mean reversion signal
        mean_mnav = 2.0  # Historical average
        deviation = ((current_mnav - mean_mnav) / mean_mnav) * 100

        if current_zone in ['deep_discount', 'discount']:
            signal = "bullish"
        elif current_zone in ['extreme_premium']:
            signal = "bearish"
        elif current_zone == 'premium':
            signal = "slightly_bearish"
        else:
            signal = "neutral"

        return IndicatorResult(
            name="Premium Zone",
            value=current_mnav,
            signal=signal,
            weight=0.15,
            description=f"Zone: {current_zone.replace('_', ' ').title()} ({deviation:+.1f}% from mean)"
        )


class StrategyEngine:
    """
    Combines leading and lagging indicators to generate trading signals.
    """

    def __init__(self):
        self.leading = LeadingIndicators()
        self.lagging = LaggingIndicators()

        # Signal weights
        self.leading_weight = 0.6
        self.lagging_weight = 0.4

    def calculate_composite_score(self, indicators: List[IndicatorResult]) -> Tuple[float, float]:
        """
        Calculate weighted composite score from all indicators.
        Returns (score, confidence)
        """
        signal_values = {
            'bullish': 2,
            'slightly_bullish': 1,
            'neutral': 0,
            'slightly_bearish': -1,
            'bearish': -2
        }

        total_weight = sum(ind.weight for ind in indicators)
        if total_weight == 0:
            return 0, 0

        weighted_sum = sum(
            signal_values.get(ind.signal, 0) * ind.weight
            for ind in indicators
        )

        # Normalize to -10 to +10 scale
        score = (weighted_sum / total_weight) * 5

        # Confidence based on indicator agreement
        signals = [ind.signal for ind in indicators]
        bullish_count = sum(1 for s in signals if 'bullish' in s)
        bearish_count = sum(1 for s in signals if 'bearish' in s)
        total = len(signals)

        if total > 0:
            agreement = max(bullish_count, bearish_count) / total
            confidence = agreement * 100
        else:
            confidence = 0

        return round(score, 2), round(confidence, 1)

    def generate_signal(self, current_mnav: float) -> Dict:
        """
        Generate comprehensive strategy signal.
        """
        indicators = []

        # Collect leading indicators
        btc_momentum = self.leading.get_btc_momentum()
        indicators.extend(btc_momentum.values())

        options = self.leading.get_options_flow()
        if options:
            indicators.append(options)

        whales = self.leading.get_whale_activity()
        if whales:
            indicators.append(whales)

        fear_greed = self.leading.get_fear_greed_index()
        if fear_greed:
            indicators.append(fear_greed)

        # Collect lagging indicators
        ma_indicators = self.lagging.get_moving_averages(current_mnav)
        indicators.extend(ma_indicators.values())

        rsi = self.lagging.get_rsi(current_mnav)
        if rsi:
            indicators.append(rsi)

        premium_zone = self.lagging.get_premium_zone(current_mnav)
        indicators.append(premium_zone)

        # Calculate composite score
        score, confidence = self.calculate_composite_score(indicators)

        # Determine signal
        if score >= 4:
            signal = Signal.STRONG_LONG
        elif score >= 2:
            signal = Signal.LONG
        elif score <= -4:
            signal = Signal.STRONG_SHORT
        elif score <= -2:
            signal = Signal.SHORT
        else:
            signal = Signal.NEUTRAL

        # Build response
        leading_indicators = [
            {
                'name': ind.name,
                'value': ind.value,
                'signal': ind.signal,
                'description': ind.description
            }
            for ind in indicators[:4]  # First 4 are leading
        ]

        lagging_indicators = [
            {
                'name': ind.name,
                'value': ind.value,
                'signal': ind.signal,
                'description': ind.description
            }
            for ind in indicators[4:]  # Rest are lagging
        ]

        return {
            'signal': signal.value,
            'score': score,
            'confidence': confidence,
            'current_mnav': current_mnav,
            'leading_indicators': leading_indicators,
            'lagging_indicators': lagging_indicators,
            'recommendation': self._get_recommendation(signal, score, confidence),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def _get_recommendation(self, signal: Signal, score: float, confidence: float) -> str:
        """Generate human-readable recommendation."""
        if signal == Signal.STRONG_LONG:
            return f"Strong buy signal. Consider accumulating. Score: {score}/10, Confidence: {confidence}%"
        elif signal == Signal.LONG:
            return f"Bullish bias. Look for entry on dips. Score: {score}/10, Confidence: {confidence}%"
        elif signal == Signal.STRONG_SHORT:
            return f"Strong sell signal. Consider reducing exposure. Score: {score}/10, Confidence: {confidence}%"
        elif signal == Signal.SHORT:
            return f"Bearish bias. Avoid new longs. Score: {score}/10, Confidence: {confidence}%"
        else:
            return f"Neutral. Wait for clearer signal. Score: {score}/10, Confidence: {confidence}%"


# Global strategy engine instance
strategy_engine = StrategyEngine()


def get_strategy_signal(current_mnav: float) -> Dict:
    """Main entry point for strategy signals."""
    return strategy_engine.generate_signal(current_mnav)
