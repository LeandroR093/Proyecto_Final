path = r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\app.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Stress Test slider
if 'vol_mult = st.sidebar.slider' not in content:
    slider_code = """
    st.markdown("---")
    st.subheader("Stress Test (Monte Carlo)")
    vol_mult = st.slider("Multiplicador de Volatilidad", 1.0, 3.0, 1.0, step=0.1)
"""
    content = content.replace("# --- DOWNLOAD DATA ---", slider_code + "\n# --- DOWNLOAD DATA ---")

# 2. Add descargar_datos_db with Fallback
descargar_datos_target = """# --- DOWNLOAD DATA ---
@st.cache_data
def descargar_datos(ticker):
    df = yf.download(ticker, period='2y', progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df"""

db_refactor = """import sqlite3

# --- DOWNLOAD DATA ---
@st.cache_data
def descargar_datos(ticker):
    db_path = r"c:\\Users\\Farmatodo Kike\\Documents\\4Geeks Data science\\Proyecto_Final\\src\\sp500_market_data.db"
    try:
        conn = sqlite3.connect(db_path)
        query = f\"SELECT * FROM sp500_daily_metrics WHERE Ticker = '{ticker}'\"
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
    return df"""

if descargar_datos_target in content:
    content = content.replace(descargar_datos_target, db_refactor)

# 3. Update Monte Carlo call
content = content.replace(
    "df_s, stats_s = ejecutar_monte_carlo(df, dias_proyeccion=horizonte_dias, n_simulaciones=1000)",
    "df_s, stats_s = ejecutar_monte_carlo(df, dias_proyeccion=horizonte_dias, n_simulaciones=1000, vol_mult=vol_mult)"
)

# 4. Insert Risk Metrics
metrics_target = """        ultimo_cierre = df['Close'].iloc[-1]
        cierre_anterior = df['Close'].iloc[-2]
        cambio_abs = ultimo_cierre - cierre_anterior
        cambio_pct = (cambio_abs / cierre_anterior) * 100
        st.metric(label=f"{tk} Actual", value=f\"${ultimo_cierre:.2f}\", delta=f\"${cambio_abs:.2f} ({cambio_pct:.2f}%)\")"""

metrics_replace = """        ultimo_cierre = df['Close'].iloc[-1]
        cierre_anterior = df['Close'].iloc[-2]
        cambio_abs = ultimo_cierre - cierre_anterior
        cambio_pct = (cambio_abs / cierre_anterior) * 100
        
        # --- Cálculo Riesgo ---
        retornos = df['Close'].pct_change().dropna()
        sharpe = (retornos.mean() / retornos.std() * 15.87) if retornos.std() > 0 else 0  # np.sqrt(252) approx 15.87
        drawdown = (df['Close'] / df['Close'].cummax() - 1).min() * 100
        
        st.metric(label=f"{tk} Actual", value=f\"${ultimo_cierre:.2f}\", delta=f\"${cambio_abs:.2f} ({cambio_pct:.2f}%)\")
        st.markdown(f\"<div style='font-size:11px; color:#8b949e; margin-top:-10px;'> Sharpe: <b>{sharpe:.2f}</b> | Max DD: <b style='color:#f85149;'>{drawdown:.1f}%</b></div>\", unsafe_allow_html=True)"""

if metrics_target in content:
    content = content.replace(metrics_target, metrics_replace)

# 5. Add Correlation Heatmap
correlation_snippet = """st.markdown("---")

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

# 2. Unified Canvas for Returns (%)"""

if "# 2. Unified Canvas for Returns (%)" in content:
    content = content.replace("# 2. Unified Canvas for Returns (%)", correlation_snippet)

# 6. Add Backtesting snippet at the end
backtest_snippet = """
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
"""

# Append if backtesting isn't already there
if "Estrategia Backtesting" not in content and "df_data_ind =" in content:
    content += backtest_snippet

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Advanced refactoring successfully V3")
