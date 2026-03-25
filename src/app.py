import streamlit as st
import pandas as pd
import pickle
import json
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from indicators import calcular_indicadores_grid, formatear_valor
from simulation import ejecutar_monte_carlo

st.set_page_config(page_title="Advanced Quant Trading Platform", page_icon="⚡", layout="wide")

# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
    /* Dark Theme Setup */
    body {
        background-color: #0d1117;
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Metrics Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 20px;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }
    .metric-title {
        color: #8b949e;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 20px;
        font-weight: 600;
        margin-top: 6px;
    }
    .metric-pct {
        font-size: 12px;
        margin-top: 4px;
    }
    .pct-up { color: #3fb950; }
    .pct-down { color: #f85149; }
    .pct-neutral { color: #8b949e; }
    
    /* Banner/Notification */
    .banner {
        background-color: rgba(56, 139, 253, 0.1);
        border: 1px solid rgba(56, 139, 253, 0.4);
        border-radius: 8px;
        padding: 12px 16px;
        margin: 16px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

import os

# --- CARGAR ARCHIVOS ---
@st.cache_resource
def cargar_archivos_v2():
    # Directorio actual (src/)
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    # Directorio raíz (Proyecto_Final/)
    dir_raiz = os.path.dirname(dir_actual)
    
    ruta_modelo = os.path.join(dir_raiz, 'models', 'oraculo_financiero2_xgb.pkl')
    ruta_diccionario = os.path.join(dir_actual, 'diccionario_tickers.json')
    
    try:
        with open(ruta_modelo, 'rb') as archivo_modelo:
            modelo = pickle.load(archivo_modelo)
    except Exception as e:
        print(f"Error cargando modelo: {e}")
        modelo = None # Fallback if model not found
        
    try:
        with open(ruta_diccionario, 'r') as archivo_json:
            diccionario = json.load(archivo_json)
    except Exception as e:
        print(f"Error cargando diccionario: {e}")
        diccionario = {}
        
    return modelo, diccionario

modelo, diccionario_tickers = cargar_archivos_v2()



# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/50/sales-performance.png", width=40)
    st.subheader("Selección de Activos")
    # Multiselect para múltiples activos
    acciones_seleccionadas = st.multiselect(
        "Comparar Acciones (Máx 10)", 
        options=list(diccionario_tickers.keys()), 
        default=[list(diccionario_tickers.keys())[0]] if diccionario_tickers else [],
        max_selections=10
    )

    
    st.markdown("---")
    st.subheader("Modelo AI")
    algoritmo = st.selectbox("Algoritmo de Proyección", options=["Ensemble (RF + XGB)", "XGBoost", "Random Forest"])
    
    st.markdown("---")
    st.subheader("Proyección (Monte Carlo)")
    horizonte = st.selectbox("Horizonte", options=["1 Día", "5 Días", "30 Días", "90 Días"], index=0)
    dias_dict = {"1 Día": 1, "5 Días": 5, "30 Días": 30, "90 Días": 90}
    horizonte_dias = dias_dict[horizonte]
    
    st.markdown("---")
    st.subheader("Visualización")
    tipo_grafico = st.radio("Tipo Gráfico", options=["Área", "Velas"], index=0)
    mostrar_volumen = st.checkbox("Volumen", value=True)
    mostrar_grid = st.checkbox("Ver Parámetros Clave", value=False)


    st.markdown("---")
    st.subheader("Stress Test (Monte Carlo)")
    vol_mult = st.slider("Multiplicador de Volatilidad", 1.0, 3.0, 1.0, step=0.1)

import sqlite3

# --- DOWNLOAD DATA ---
@st.cache_data
def descargar_datos(ticker):
    db_path = r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\sp500_market_data.db"
    try:
        conn = sqlite3.connect(db_path)
        query = f"SELECT * FROM sp500_daily_metrics WHERE Ticker = '{ticker}'"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            # Ensure index has name 'Date'
            df.index.name = 'Date'
            return df
    except Exception as e:
         pass
         
    df = yf.download(ticker, period='2y', progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

st.title("⚡ Advanced Quant Trading Platform")

# Selector de periodo global
period = st.radio("Período de Visualización", ["1M", "3M", "6M", "YTD", "1A", "MAX"], index=4, horizontal=True)

datos_dict = {}
sim_dict = {}
stats_dict = {}

if not acciones_seleccionadas:
    st.warning("Selecciona al menos una acción en el sidebar.")
    st.stop()

with st.spinner(f"Simulando proyecciones..."):
    for ticker in acciones_seleccionadas:
        df = descargar_datos(ticker)
        if not df.empty and len(df) > 20:
            from simulation import ejecutar_monte_carlo
            df_s, stats_s = ejecutar_monte_carlo(df, dias_proyeccion=horizonte_dias, n_simulaciones=1000, vol_mult=vol_mult)
            datos_dict[ticker] = df
            sim_dict[ticker] = df_s
            stats_dict[ticker] = stats_s

if not datos_dict:
    st.error("No se pudieron cargar datos suficientes para ninguna acción.")
    st.stop()

st.markdown("---")
st.markdown("---")

# 1. Row of Metrics for all Assets
st.subheader("Resumen de Precios")
cols_precio = st.columns(len(datos_dict))
for idx, (tk, df) in enumerate(datos_dict.items()):
    with cols_precio[idx]:
        ultimo_cierre = df['Close'].iloc[-1]
        cierre_anterior = df['Close'].iloc[-2]
        cambio_abs = ultimo_cierre - cierre_anterior
        cambio_pct = (cambio_abs / cierre_anterior) * 100
        st.metric(label=f"{tk} Actual", value=f"${ultimo_cierre:.2f}", delta=f"{cambio_abs:.2f} ({cambio_pct:.2f}%)")

st.markdown("---")

st.markdown("---")

# 3. Matriz de Correlación
if len(datos_dict) > 1:
    st.subheader("Matriz de Correlación (Pearson)")
    df_combined = pd.DataFrame({tk: df['Close'] for tk, df in datos_dict.items()}).dropna()
    if not df_combined.empty:
        df_corr = df_combined.corr()
        fig_corr = go.Figure(go.Heatmap(
            z=df_corr.values, x=df_corr.columns, y=df_corr.index, colorscale='balance', zmin=-1, zmax=1,
            text=np.round(df_corr.values, 2), texttemplate="%{text}"
        ))
        fig_corr.update_layout(template="plotly_dark", height=280, margin=dict(t=20, b=20, l=40, r=40))
        st.plotly_chart(fig_corr, use_container_width=True)

# 2. Unified Canvas for Returns (%)
st.subheader(f"Evolución y Rendimiento Proyectado ({period})")

if len(datos_dict) > 1 and tipo_grafico == "Velas":
    st.warning("⚠️ El gráfico de VELAS no admite superposición normalizada (%). Utilizando gráfico de Área/Líneas para la comparación.")

fig = go.Figure()

for tk, df_data in datos_dict.items():
    df_sim = sim_dict.get(tk, pd.DataFrame())
    stats_sim = stats_dict.get(tk, {})
    
    dias_filtro = {"1M": 30, "3M": 90, "6M": 180, "YTD": 120, "1A": 252, "MAX": len(df_data)}
    n_lookback = dias_filtro.get(period, 30)
    df_plot = df_data.tail(n_lookback)
    
    if df_plot.empty: continue
    
    # Check for Single Asset Candlestick View
    if len(datos_dict) == 1 and tipo_grafico == "Velas":
        fig.add_trace(go.Candlestick(
            x=df_plot.index,
            open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'],
            name=f'{tk} Velas'
        ))
        
        if not df_sim.empty and horizonte_dias > 1:
            ultima_fecha = df_plot.index[-1]
            fechas_futuras = pd.date_range(start=ultima_fecha + pd.Timedelta(days=1), periods=horizonte_dias, freq='B')
            precios_finales = df_sim.iloc[-1]
            media_final = precios_finales.mean()
            idx_cercano = (precios_finales - media_final).abs().idxmin()
            camino_realista = df_sim[idx_cercano].values[1:] 
            
            fig.add_trace(go.Scatter(
                x=fechas_futuras, y=camino_realista, 
                mode='lines', name=f'{tk} Proyección',
                line=dict(width=2.5, dash='dot')
            ))
    else:
        # Normalized Returns %
        base_price = df_plot['Close'].iloc[0]
        historico_pct = (df_plot['Close'] / base_price - 1) * 100
        
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=historico_pct, 
            mode='lines', name=f'{tk} Histórico',
            line=dict(width=2)
        ))
        
        if not df_sim.empty and horizonte_dias > 1:
            ultima_fecha = df_plot.index[-1]
            fechas_futuras = pd.date_range(start=ultima_fecha + pd.Timedelta(days=1), periods=horizonte_dias, freq='B')
            precios_finales = df_sim.iloc[-1]
            media_final = precios_finales.mean()
            idx_cercano = (precios_finales - media_final).abs().idxmin()
            camino_realista = df_sim[idx_cercano].values[1:] 
            camino_realista_pct = (camino_realista / base_price - 1) * 100
            
            fig.add_trace(go.Scatter(
                x=fechas_futuras, y=camino_realista_pct, 
                mode='lines', name=f'{tk} Proyección',
                line=dict(width=2.5, dash='dot')
            ))

# Dynamic Y-Axis Title
title_y = "Rendimiento Acumulado (%)" if len(datos_dict) > 1 or tipo_grafico != "Velas" else "Precio ($)"

fig.update_layout(
    template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=20, b=40), xaxis=dict(showgrid=True, gridcolor="#21262d"),
    yaxis=dict(showgrid=True, gridcolor="#21262d", title_text=title_y), height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

if mostrar_grid:
    st.divider()
    st.subheader("Evolución de Parámetros Clave (Detalle Individual)")
    asset_ind_view = st.selectbox("Inspeccionar parámetros de:", options=list(datos_dict.keys()))
    
    df_data_ind = datos_dict[asset_ind_view]
    df_sim_ind = sim_dict.get(asset_ind_view, pd.DataFrame())
    
    dias_filtro_ind = {'1M': 30, '3M': 90, '6M': 180, 'YTD': 120, '1A': 252, 'MAX': len(df_data_ind)}
    n_lookback = dias_filtro_ind.get(period, 30)
    indicadores_data = calcular_indicadores_grid(df_data_ind, lookback_days=n_lookback)
    
    indicadores_futuros = {}
    if not df_sim_ind.empty:
        try:
            precios_finales = df_sim_ind.iloc[-1]
            media_final = precios_finales.mean()
            idx_cercano = (precios_finales - media_final).abs().idxmin()
            camino_realista = df_sim_ind[idx_cercano].values[1:] 
            df_futuro = df_data_ind.copy()
            promedio_volumen = df_data_ind['Volume'].mean()
            fechas_futuras_ind = pd.date_range(start=df_data_ind.index[-1] + pd.Timedelta(days=1), periods=horizonte_dias, freq='B')
            filas_f = []
            for px in camino_realista: filas_f.append({'Open': px, 'High': px * 1.002, 'Low': px * 0.998, 'Close': px, 'Adj Close': px, 'Volume': promedio_volumen})
            df_append = pd.DataFrame(filas_f, index=fechas_futuras_ind)
            df_futuro = pd.concat([df_futuro, df_append])
            indicadores_futuros = calcular_indicadores_grid(df_futuro, lookback_days=horizonte_dias)
        except: pass
        
    if indicadores_data:
        claves_15 = ["ADJ CLOSE", "HIGH", "LOW", "OPEN", "VOLUME", "VOL ADX", "VOL OBV", "VOL CMF", "VOL FI", "VOL MFI", "VOL NVI", "VOLAT BBH", "VOLAT BBL", "VOLAT KCH", "VOLAT KCL"]
        st.markdown("<style>.metric-sub { display: flex; justify-content: space-between; font-size: 11px; margin-top: 8px; color: #8b949e; border-top: 1px solid #30363d; padding-top: 6px; } .sub-title { color: #8b949e; }</style>", unsafe_allow_html=True)
        indicadores_filtrados = {k: indicadores_data[k] for k in claves_15 if k in indicadores_data}
        cols = st.columns(4)
        for i, (nombre, info) in enumerate(indicadores_filtrados.items()):
            val_str = formatear_valor(info['val'])
            pct_val = info.get('pct', 0.0)
            pct_class = "pct-up" if pct_val > 0 else "pct-down" if pct_val < 0 else "pct-neutral"
            pct_sign = "+" if pct_val > 0 else ""
            fut_pct = 0.0; fut_class = "pct-neutral"; fut_sign = ""
            if nombre in indicadores_futuros:
                fut_val = indicadores_futuros[nombre]['val']               
                if info['val'] != 0: fut_pct = ((fut_val - info['val']) / info['val']) * 100; fut_class = "pct-up" if fut_pct > 0 else "pct-down" if fut_pct < 0 else "pct-neutral"; fut_sign = "+" if fut_pct > 0 else ""
            with cols[i % 4]:
                st.markdown(f"""<div class='metric-card'><div class='metric-title'>{nombre}</div><div class='metric-value'>{val_str}</div><div class='metric-sub'><span><span class='sub-title'>Pasado:</span> <span class='{pct_class}'>{pct_sign}{pct_val:.1f}%</span></span><span><span class='sub-title'>Futuro:</span> <span class='{fut_class}'>{fut_sign}{fut_pct:.1f}%</span></span></div></div>""", unsafe_allow_html=True)
                if (i + 1) % 4 == 0: st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # 4. Backtesting Simple (Cruce de Medias)
    st.divider()
    st.subheader("Estrategia Backtesting: Cruce Medias 20/50")
    
    df_data_ind = df_data_ind.copy()
    df_data_ind['MA20'] = df_data_ind['Close'].rolling(window=20).mean()
    df_data_ind['MA50'] = df_data_ind['Close'].rolling(window=50).mean()
    
    df_data_ind['Signal'] = 0
    df_data_ind.loc[df_data_ind['MA20'] > df_data_ind['MA50'], 'Signal'] = 1
    df_data_ind['Retorno_Estrategia'] = df_data_ind['Close'].pct_change() * df_data_ind['Signal'].shift(1)
    
    rend_cum_est = (1 + df_data_ind['Retorno_Estrategia']).dropna().cumprod() - 1
    rend_cum_bh = (1 + df_data_ind['Close'].pct_change()).dropna().cumprod() - 1

    fig_backtest = go.Figure()
    fig_backtest.add_trace(go.Scatter(x=rend_cum_est.index, y=rend_cum_est * 100, name="Estrategia (MA 20/50)", line=dict(color="#3fb950")))
    fig_backtest.add_trace(go.Scatter(x=rend_cum_bh.index, y=rend_cum_bh * 100, name="Buy & Hold", line=dict(color="#8b949e", dash='dash')))
    
    fig_backtest.update_layout(template="plotly_dark", height=350, title_text="Rendimiento Acumulado (%)", yaxis=dict(title_text="%"))
    st.plotly_chart(fig_backtest, use_container_width=True)
