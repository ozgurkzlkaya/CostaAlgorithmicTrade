from datetime import datetime, timedelta
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from data.models import Candle, SignalCandidate, TimeframeData
from scoring.engine import ScoreEngine
from scoring.models import ScoreContext


def _build_candles(count: int, start_price: float = 100.0, step: float = 0.2) -> list[Candle]:
    now = datetime.utcnow()
    candles: list[Candle] = []
    price = start_price
    for i in range(count):
        ts = now - timedelta(minutes=15 * (count - i))
        high = price * 1.005
        low = price * 0.995
        close = price + step
        candles.append(Candle(timestamp=ts, open=price, high=high, low=low, close=close, volume=1000))
        price = close
    return candles


def test_score_within_bounds():
    engine = ScoreEngine({"enabled": True})
    tf_data = [
        TimeframeData(timeframe="15m", candles=_build_candles(60)),
        TimeframeData(timeframe="1h", candles=_build_candles(60, step=0.1)),
        TimeframeData(timeframe="4h", candles=_build_candles(60, step=0.05)),
    ]
    candidate = SignalCandidate(
        mode="CRYPTO_FUTURES",
        symbol="TESTUSDT",
        strategy="trend_following",
        direction="LONG",
        timeframe="15m",
        entry=101.0,
        sl=99.0,
        tp=105.0,
        rr=3.0,
        score=0.0,
        reason={},
        filters={},
        generated_at=datetime.utcnow(),
    )
    context = ScoreContext(mode="CRYPTO_FUTURES", volatility_reason="", regime_reason="risk_on", regime_score=1.0, backtest_metrics={})
    score = engine.score(candidate, tf_data, context)
    assert 0.0 <= score <= 100.0
    assert engine.passes_threshold("CRYPTO_FUTURES", score)
