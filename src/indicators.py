import pandas as pd
import numpy as np
import ta

def calcular_indicadores_grid(df, lookback_days=1):
    """
    Calcula los indicadores técnicos requeridos para el dashboard.
    Asegura precisión en volumen y volatilidad.
    """
    if df.empty or len(df) < 20:
        return {}
        
    df_ta = df.copy()
    
    # 1. Parámetros de Precio (Básicos)
    # Usamos nombres exactos del requerimiento
    metras = {
        "ADJ CLOSE": df_ta['Adj Close'].iloc[-1] if 'Adj Close' in df_ta.columns else df_ta['Close'].iloc[-1],
        "HIGH": df_ta['High'].iloc[-1],
        "LOW": df_ta['Low'].iloc[-1],
        "OPEN": df_ta['Open'].iloc[-1],
        "VOLUME": df_ta['Volume'].iloc[-1]
    }

    # Cambios porcentuales básicos
    metras_pct = {}
    for k in metras.keys():
        idx_prev = -1 - lookback_days
        if abs(idx_prev) <= len(df_ta):
            col_cmp = 'Adj Close' if k == 'ADJ CLOSE' and 'Adj Close' in df_ta.columns else k.capitalize()
            if col_cmp not in df_ta.columns: col_cmp = 'Close'
            prev = df_ta[col_cmp].iloc[idx_prev]
            metras_pct[k] = ((metras[k] - prev) / prev * 100) if prev != 0 else 0.0
        else:
            metras_pct[k] = 0.0

    res = {k: {"val": metras[k], "pct": metras_pct[k]} for k in metras}

    # Helper para cálculos seguros con la librería 'ta'
    def safe_calc(key, func):
        try:
            series = func()
            val = series.iloc[-1]
            if pd.isna(val): val = 0.0
            
            # Calculamos pct respecto al lookback para indicadores que lo permitan
            prev_val = series.iloc[-1 - lookback_days] if len(series) > lookback_days else val
            pct = ((val - prev_val) / prev_val * 100) if prev_val != 0 and not pd.isna(prev_val) else 0.0
            
            res[key] = {"val": val, "pct": pct}
        except:
            res[key] = {"val": 0.0, "pct": 0.0}

    # 2. Parámetros de Volumen
    safe_calc("Vol ADX", lambda: ta.trend.ADXIndicator(df_ta['High'], df_ta['Low'], df_ta['Close']).adx())
    safe_calc("Vol OBV", lambda: ta.volume.OnBalanceVolumeIndicator(df_ta['Close'], df_ta['Volume']).on_balance_volume())
    safe_calc("Vol CMF", lambda: ta.volume.ChaikinMoneyFlowIndicator(df_ta['High'], df_ta['Low'], df_ta['Close'], df_ta['Volume']).chaikin_money_flow())
    safe_calc("Vol FI", lambda: ta.volume.ForceIndexIndicator(df_ta['Close'], df_ta['Volume']).force_index())
    safe_calc("Vol MFI", lambda: ta.volume.MfiIndicator(df_ta['High'], df_ta['Low'], df_ta['Close'], df_ta['Volume']).money_flow_index())
    safe_calc("Vol NVI", lambda: ta.volume.NegativeVolumeIndexIndicator(df_ta['Close'], df_ta['Volume']).negative_volume_index())

    # 3. Parámetros de Volatilidad
    # Bollinger Bands
    try:
        bb = ta.volatility.BollingerBands(df_ta['Close'])
        res["Volat BBH"] = {"val": bb.bollinger_hband().iloc[-1], "pct": 0.0}
        res["Volat BBL"] = {"val": bb.bollinger_lband().iloc[-1], "pct": 0.0}
    except:
        res["Volat BBH"] = {"val": 0.0, "pct": 0.0}
        res["Volat BBL"] = {"val": 0.0, "pct": 0.0}

    # Keltner Channels
    try:
        kc = ta.volatility.KeltnerChannel(df_ta['High'], df_ta['Low'], df_ta['Close'])
        res["Volat KCH"] = {"val": kc.keltner_channel_hband().iloc[-1], "pct": 0.0}
        res["Volat KCL"] = {"val": kc.keltner_channel_lband().iloc[-1], "pct": 0.0}
    except:
        res["Volat KCH"] = {"val": 0.0, "pct": 0.0}
        res["Volat KCL"] = {"val": 0.0, "pct": 0.0}

    return res


def formatear_valor(val):
    """Formatea valores grandes (K, M, B) para legibilidad financiera"""
    if pd.isna(val): return "N/A"
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    elif abs_val >= 1000:
        return f"{val / 1000:.2f}K"
    else:
        return f"{val:.2f}"

