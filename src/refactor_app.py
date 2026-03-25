import re

path = r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\app.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find break points
# We want to replace everything from line 141 (# --- DOWNLOAD DATA ---) onwards
# But first let's see where # --- DOWNLOAD DATA --- is exactly
start_line = -1
for i, line in enumerate(lines):
    if "# --- DOWNLOAD DATA ---" in line:
        start_line = i
        break

if start_line == -1:
    print("Could not find start marker")
    exit(1)

# Keep up to start_line - 1
new_content = lines[:start_line]

# Append Batch calculations
new_content.extend([
    "# --- DOWNLOAD DATA ---\n",
    "@st.cache_data\n",
    "def descargar_datos(ticker):\n",
    "    df = yf.download(ticker, period='2y', progress=False)\n",
    "    if isinstance(df.columns, pd.MultiIndex):\n",
    "        df.columns = df.columns.get_level_values(0)\n",
    "    return df\n",
    "\n",
    "st.title(\"⚡ Advanced Quant Trading Platform\")\n",
    "\n",
    "# Selector de periodo global\n",
    "period = st.radio(\"Período de Visualización\", [\"1M\", \"3M\", \"6M\", \"YTD\", \"1A\", \"MAX\"], index=4, horizontal=True)\n",
    "\n",
    "datos_dict = {}\n",
    "sim_dict = {}\n",
    "stats_dict = {}\n",
    "\n",
    "if not acciones_seleccionadas:\n",
    "    st.warning(\"Selecciona al menos una acción en el sidebar.\")\n",
    "    st.stop()\n",
    "\n",
    "with st.spinner(f\"Simulando proyecciones...\"):\n",
    "    for ticker in acciones_seleccionadas:\n",
    "        df = descargar_datos(ticker)\n",
    "        if not df.empty and len(df) > 20:\n",
    "            from simulation import ejecutar_monte_carlo\n",
    "            df_s, stats_s = ejecutar_monte_carlo(df, dias_proyeccion=horizonte_dias, n_simulaciones=1000)\n",
    "            datos_dict[ticker] = df\n",
    "            sim_dict[ticker] = df_s\n",
    "            stats_dict[ticker] = stats_s\n",
    "\n",
    "if not datos_dict:\n",
    "    st.error(\"No se pudieron cargar datos suficientes para ninguna acción.\")\n",
    "    st.stop()\n",
    "\n",
    "st.markdown(\"---\")\n",
    "\n",
    "n_selec = len(datos_dict)\n",
    "n_cols = 1 if n_selec <= 1 else 2 if n_selec <= 4 else 3\n",
    "columns_grid = st.columns(n_cols)\n",
    "\n",
    "for i, (ticker, df_data) in enumerate(datos_dict.items()):\n",
    "    df_sim = sim_dict.get(ticker, pd.DataFrame())\n",
    "    stats_sim = stats_dict.get(ticker, {})\n",
    "    col_idx = i % n_cols\n",
    "    \n",
    "    with columns_grid[col_idx]:\n",
    "        st.markdown(f\"\"\"\n",
    "        <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; margin-bottom: 12px;'>\n",
    "            <h4 style='margin:0; color: #58a6ff;'>{ticker}</h4>\n",
    "        </div>\n",
    "        \"\"\", unsafe_allow_html=True)\n",
    "        \n",
    "        ultimo_cierre = df_data['Close'].iloc[-1]\n",
    "        cierre_anterior = df_data['Close'].iloc[-2]\n",
    "        cambio_abs = ultimo_cierre - cierre_anterior\n",
    "        cambio_pct = (cambio_abs / cierre_anterior) * 100\n",
    "        st.metric(label=f\"{ticker} Actual\", value=f\"${ultimo_cierre:.2f}\", delta=f\"{cambio_abs:.2f} ({cambio_pct:.2f}%)\")\n",
    "\n"
])

# Subheader and old banner are simplified inside card or omitted if covered by metric
# Let's read remainder lines from app.py to append with indent after specific index
# We skip single model downloads old code.
# The remainder of app.py starts adding Tabs.
# Let's find # --- CHARTS & ANALYSIS TABS --- in original lines
tabs_line = -1
for i, line in enumerate(lines):
    if "# --- CHARTS & ANALYSIS TABS ---" in line:
        tabs_line = i
        break

if tabs_line == -1:
    print("Could not find tabs marker")
    exit(1)

# We also need is and items calculated like 'indicadores_data' etc inside loop
# We will inject calculation logic first inside loop
loop_calculus = [
    "        # --- CALCULAR INDICADORES (GRID) ---\n",
    "        dias_filtro_ind = {'1M': 30, '3M': 90, '6M': 180, 'YTD': 120, '1A': 252, 'MAX': len(df_data)}\n",
    "        n_lookback = dias_filtro_ind.get(period, 30)\n",
    "        indicadores_data = calcular_indicadores_grid(df_data, lookback_days=n_lookback)\n",
    "\n",
    "        indicadores_futuros = {}\n",
    "        if not df_sim.empty:\n",
    "            try:\n",
    "                precios_finales = df_sim.iloc[-1]\n",
    "                media_final = precios_finales.mean()\n",
    "                idx_cercano = (precios_finales - media_final).abs().idxmin()\n",
    "                camino_realista = df_sim[idx_cercano].values[1:]\n",
    "                \n",
    "                df_futuro = df_data.copy()\n",
    "                promedio_volumen = df_data['Volume'].mean()\n",
    "                fechas_futuras_ind = pd.date_range(start=df_data.index[-1] + pd.Timedelta(days=1), periods=horizonte_dias, freq='B')\n",
    "                \n",
    "                filas_f = []\n",
    "                for px in camino_realista:\n",
    "                    filas_f.append({'Open': px, 'High': px * 1.002, 'Low': px * 0.998, 'Close': px, 'Adj Close': px, 'Volume': promedio_volumen})\n",
    "                df_append = pd.DataFrame(filas_f, index=fechas_futuras_ind)\n",
    "                df_futuro = pd.concat([df_futuro, df_append])\n",
    "                indicadores_futuros = calcular_indicadores_grid(df_futuro, lookback_days=horizonte_dias)\n",
    "            except: pass\n",
    "\n"
]
new_content.extend(loop_calculus)

# Now we take the original lines from tabs_line to the end and indent them by 8 spaces (2 levels: for and with)
# Wait, inside loop, we are within `with columns_grid[col_idx]:` which is indent 8.
indent = "        "

# We must keep some global vars like 'mostrar_grid' and 'tipo_grafico' from sidebar.
# They are already in sidebar.

for line in lines[tabs_line:]:
    # Make sure we don't break Streamlit spacing
    # Just indent every file line
    if line.strip() == "":
        new_content.append("\n")
    else:
        new_content.append(indent + line)

# Save back to file
with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_content)

print("Refactored successfully")
