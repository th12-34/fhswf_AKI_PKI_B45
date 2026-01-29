"""
Programmname: Indicators

Autor: Maximilian Pfau / Gregor Schumacher

Datum: 13.01.2026

Beschreibung:
Beinhaltet die Indikatoren Berechnung für die Analyse von Asset-Werten. Wird in dem asset_analyse view benötigt.

Quellen:
- Programmierung
    - Lehrbrief zur Vorlesung
    - https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
    - ChatGPT 5.2
"""

import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Berechnet den Relative Strength Index (RSI).
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_bollinger_bands(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet Bollinger Bands (SMA ± num_std * Standardabweichung).
    """
    mid = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std()
    upper = mid + (num_std * std)
    lower = mid - (num_std * std)
    return mid, upper, lower


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Berechnet den MACD-Indikator.
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line

    return macd, signal_line, hist