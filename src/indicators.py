import pandas as pd
import numpy as np
import ta

def calcular_indicadores_grid(df, lookback_days=1):
    """
    Calcula los indicadores técnicos listados en el grid del dashboard.
    Retorna un diccionario con {nombre_metrica: {valor: x, cambio_pct: y}}
    """
    if df.empty or len(df) < 20:
        return {}
        
    # Copiamos para no modificar el original
    df_ta = df.copy()
    
    # 1. Básicos
    metras = {
        "ADJ CLOSE": df_ta['Adj Close'].iloc[-1] if 'Adj Close' in df_ta.columns else df_ta['Close'].iloc[-1],
        "HIGH": df_ta['High'].iloc[-1],
        "LOW": df_ta['Low'].iloc[-1],
        "OPEN": df_ta['Open'].iloc[-1],
        "VOLUME": df_ta['Volume'].iloc[-1]
    }

    # Calcular cambios porcentuales para básicos (hoy vs lookback_days atrás)
    metras_pct = {}
    for k in metras.keys():
        idx_prev = -1 - lookback_days
        # Asegurar que no nos salimos del índice
        if abs(idx_prev) <= len(df_ta):
            # Obtener el valor de comparación
            col_cmp = k if k in df_ta.columns else 'Close'
            prev = df_ta[col_cmp].iloc[idx_prev]
            if prev != 0:
                metras_pct[k] = ((metras[k] - prev) / prev) * 100
            else:
                metras_pct[k] = 0.0
        else:
            metras_pct[k] = 0.0


    # --- CÁLCULOS INDIVIDUALES RESILIENTES ---
    res = {
        "ADJ CLOSE": {"val": metras["ADJ CLOSE"], "pct": metras_pct["ADJ CLOSE"]},
        "HIGH": {"val": metras["HIGH"], "pct": metras_pct["HIGH"]},
        "LOW": {"val": metras["LOW"], "pct": metras_pct["LOW"]},
        "OPEN": {"val": metras["OPEN"], "pct": metras_pct["OPEN"]},
        "VOLUME": {"val": metras["VOLUME"], "pct": metras_pct["VOLUME"]}
    }

    # Helper para calcular de forma segura
    def safe_append(key, calc_func):
        try:
            series = calc_func()
            # Check if the series is empty or contains NaN at the last position
            if not series.empty and pd.notna(series.iloc[-1]):
                res[key] = {"val": series.iloc[-1], "pct": 0.0}
            else:
                res[key] = {"val": 0.0, "pct": 0.0}
        except Exception as e:
            # print(f"Error calculating {key}: {e}") # For debugging
            res[key] = {"val": 0.0, "pct": 0.0}

    # 2. Indicadores Volumen
    safe_append("VOL ADX", lambda: ta.trend.ADXIndicator(df_ta['High'], df_ta['Low'], df_ta['Close']).adx())
    safe_append("VOL OBV", lambda: ta.volume.OnBalanceVolumeIndicator(df_ta['Close'], df_ta['Volume']).on_balance_volume())
    safe_append("VOL CMF", lambda: ta.volume.ChaikinMoneyFlowIndicator(df_ta['High'], df_ta['Low'], df_ta['Close'], df_ta['Volume']).chaikin_money_flow())
    safe_append("VOL FI", lambda: ta.volume.ForceIndexIndicator(df_ta['Close'], df_ta['Volume']).force_index())
    # VOL EFI was a duplicate of FI, setting to 0.0
    res["VOL EFI"] = {"val": 0.0, "pct": 0.0} 
    safe_append("VOL SMA_EM", lambda: ta.volume.EaseOfMovementIndicator(df_ta['High'], df_ta['Low'], df_ta['Volume']).ease_of_movement())
    safe_append("VOL VPT", lambda: ta.volume.VolumePriceTrendIndicator(df_ta['Close'], df_ta['Volume']).volume_price_trend())
    # VOL VWAP is not directly from ta, setting to current close or 0.0
    res["VOL VWAP"] = {"val": df_ta['Close'].iloc[-1] if not df_ta['Close'].empty else 0.0, "pct": 0.0}
    safe_append("VOL MFI", lambda: ta.volume.MfiIndicator(df_ta['High'], df_ta['Low'], df_ta['Close'], df_ta['Volume']).money_flow_index())
    safe_append("VOL NVI", lambda: ta.volume.NegativeVolumeIndexIndicator(df_ta['Close'], df_ta['Volume']).negative_volume_index())

    # 3. Volatilidad (Bollinger)
    try:
        bb = ta.volatility.BollingerBands(df_ta['Close'])
        bbh = bb.bollinger_hband()
        bbl = bb.bollinger_lband()
        bb_mavg = bb.bollinger_mavg()

        res["VOLAT BBH"] = {"val": bbh.iloc[-1] if not bbh.empty and pd.notna(bbh.iloc[-1]) else 0.0, "pct": 0.0}
        res["VOLAT BBL"] = {"val": bbl.iloc[-1] if not bbl.empty and pd.notna(bbl.iloc[-1]) else 0.0, "pct": 0.0}
        
        # Bandwidth
        if not bbh.empty and not bbl.empty and not bb_mavg.empty and bb_mavg.iloc[-1] != 0:
            bb_width = (bbh.iloc[-1] - bbl.iloc[-1]) / bb_mavg.iloc[-1]
            res["VOLAT BBV"] = {"val": bb_width, "pct": 0.0}
        else:
            res["VOLAT BBV"] = {"val": 0.0, "pct": 0.0}

        # %B
        if not df_ta['Close'].empty and not bbh.empty and not bbl.empty and (bbh.iloc[-1] - bbl.iloc[-1]) != 0:
            bb_pct = (df_ta['Close'].iloc[-1] - bbl.iloc[-1]) / (bbh.iloc[-1] - bbl.iloc[-1])
            res["VOLAT BBP"] = {"val": bb_pct, "pct": 0.0}
        else:
            res["VOLAT BBP"] = {"val": 0.0, "pct": 0.0}

    except Exception as e:
        # print(f"Error calculating Bollinger Bands: {e}") # For debugging
        res["VOLAT BBH"] = {"val": 0.0, "pct": 0.0}
        res["VOLAT BBL"] = {"val": 0.0, "pct": 0.0}
        res["VOLAT BBV"] = {"val": 0.0, "pct": 0.0}
        res["VOLAT BBP"] = {"val": 0.0, "pct": 0.0}

    # 4. Keltner Channels
    try:
        kc = ta.volatility.KeltnerChannel(df_ta['High'], df_ta['Low'], df_ta['Close'])
        kcc = kc.keltner_channel_mband()
        kch = kc.keltner_channel_hband()
        kcl = kc.keltner_channel_lband()

        res["VOLAT KCC"] = {"val": kcc.iloc[-1] if not kcc.empty and pd.notna(kcc.iloc[-1]) else 0.0, "pct": 0.0}
        res["VOLAT KCH"] = {"val": kch.iloc[-1] if not kch.empty and pd.notna(kch.iloc[-1]) else 0.0, "pct": 0.0}
        res["VOLAT KCL"] = {"val": kcl.iloc[-1] if not kcl.empty and pd.notna(kcl.iloc[-1]) else 0.0, "pct": 0.0}
    except Exception as e:
        # print(f"Error calculating Keltner Channels: {e}") # For debugging
        res["VOLAT KCC"] = {"val": 0.0, "pct": 0.0}
        res["VOLAT KCH"] = {"val": 0.0, "pct": 0.0}
        res["VOLAT KCL"] = {"val": 0.0, "pct": 0.0}

    return res


def formatear_valor(val):
    """Formatea valores grandes (K, M, B)"""
    if abs(val) >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}B"
    elif abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    elif abs(val) >= 1000:
        return f"{val / 1000:.2f}K"
    else:
        return f"{val:.2f}"
