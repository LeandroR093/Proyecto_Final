path = r"c:\Users\Farmatodo Kike\Documents\4Geeks Data science\Proyecto_Final\src\app.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find start section marker
start_idx = -1
for i, line in enumerate(lines):
    if "st.markdown(\"---\")" in line and "n_selec = len(datos_dict)" in lines[max(0, i+1):min(len(lines), i+4)][0]:
        start_idx = i
        break

if start_idx == -1:
    # Fallback to general slice
    print("Trying fallback marker")
    for i, line in enumerate(lines):
        if "n_selec = len(datos_dict)" in line:
            start_idx = i - 1
            break

if start_idx == -1:
    print("Could not find replacement start line")
    exit(1)

new_content = lines[:start_idx]

bottom_section = [
    "st.markdown(\"---\")\n",
    "\n",
    "# 1. Row of Metrics for all Assets\n",
    "st.subheader(\"Resumen de Precios\")\n",
    "cols_precio = st.columns(len(datos_dict))\n",
    "for idx, (tk, df) in enumerate(datos_dict.items()):\n",
    "    with cols_precio[idx]:\n",
    "        ultimo_cierre = df['Close'].iloc[-1]\n",
    "        cierre_anterior = df['Close'].iloc[-2]\n",
    "        cambio_abs = ultimo_cierre - cierre_anterior\n",
    "        cambio_pct = (cambio_abs / cierre_anterior) * 100\n",
    "        st.metric(label=f\"{tk} Actual\", value=f\"${ultimo_cierre:.2f}\", delta=f\"{cambio_abs:.2f} ({cambio_pct:.2f}%)\")\n",
    "\n",
    "st.markdown(\"---\")\n",
    "\n",
    "# 2. Unified Canvas for Returns (%)\n",
    "st.subheader(f\"Evolución y Rendimiento Proyectado ({period})\")\n",
    "\n",
    "if len(datos_dict) > 1 and tipo_grafico == \"Velas\":\n",
    "    st.warning(\"⚠️ El gráfico de VELAS no admite superposición normalizada (%). Utilizando gráfico de Área/Líneas para la comparación.\")\n",
    "\n",
    "fig = go.Figure()\n",
    "\n",
    "for tk, df_data in datos_dict.items():\n",
    "    df_sim = sim_dict.get(tk, pd.DataFrame())\n",
    "    stats_sim = stats_dict.get(tk, {})\n",
    "    \n",
    "    dias_filtro = {\"1M\": 30, \"3M\": 90, \"6M\": 180, \"YTD\": 120, \"1A\": 252, \"MAX\": len(df_data)}\n",
    "    n_lookback = dias_filtro.get(period, 30)\n",
    "    df_plot = df_data.tail(n_lookback)\n",
    "    \n",
    "    if df_plot.empty: continue\n",
    "    \n",
    "    base_price = df_plot['Close'].iloc[0]\n",
    "    historico_pct = (df_plot['Close'] / base_price - 1) * 100\n",
    "    \n",
    "    fig.add_trace(go.Scatter(\n",
    "        x=df_plot.index, y=historico_pct, \n",
    "        mode='lines', name=f'{tk} Histórico',\n",
    "        line=dict(width=2)\n",
    "    ))\n",
    "    \n",
    "    if not df_sim.empty and horizonte_dias > 1:\n",
    "        ultima_fecha = df_plot.index[-1]\n",
    "        fechas_futuras = pd.date_range(start=ultima_fecha + pd.Timedelta(days=1), periods=horizonte_dias, freq='B')\n",
    "        \n",
    "        precios_finales = df_sim.iloc[-1]\n",
    "        media_final = precios_finales.mean()\n",
    "        idx_cercano = (precios_finales - media_final).abs().idxmin()\n",
    "        camino_realista = df_sim[idx_cercano].values[1:] \n",
    "        \n",
    "        camino_realista_pct = (camino_realista / base_price - 1) * 100\n",
    "        \n",
    "        fig.add_trace(go.Scatter(\n",
    "            x=fechas_futuras, y=camino_realista_pct, \n",
    "            mode='lines', name=f'{tk} Proyección',\n",
    "            line=dict(width=2.5, dash='dot')\n",
    "        ))\n",
    "\n",
    "fig.update_layout(\n",
    "    template=\"plotly_dark\", plot_bgcolor=\"rgba(0,0,0,0)\", paper_bgcolor=\"rgba(0,0,0,0)\",\n",
    "    margin=dict(l=40, r=40, t=20, b=40), xaxis=dict(showgrid=True, gridcolor=\"#21262d\"),\n",
    "    yaxis=dict(showgrid=True, gridcolor=\"#21262d\", title_text=\"Rendimiento Acumulado (%)\"), height=500,\n",
    "    legend=dict(orientation=\"h\", yanchor=\"bottom\", y=1.02, xanchor=\"right\", x=1)\n",
    ")\n",
    "st.plotly_chart(fig, use_container_width=True)\n",
    "\n",
    "if mostrar_grid:\n",
    "    st.divider()\n",
    "    st.subheader(\"Evolución de Parámetros Clave (Detalle Individual)\")\n",
    "    asset_ind_view = st.selectbox(\"Inspeccionar parámetros de:\", options=list(datos_dict.keys()))\n",
    "    \n",
    "    df_data_ind = datos_dict[asset_ind_view]\n",
    "    df_sim_ind = sim_dict.get(asset_ind_view, pd.DataFrame())\n",
    "    \n",
    "    dias_filtro_ind = {'1M': 30, '3M': 90, '6M': 180, 'YTD': 120, '1A': 252, 'MAX': len(df_data_ind)}\n",
    "    n_lookback = dias_filtro_ind.get(period, 30)\n",
    "    indicadores_data = calcular_indicadores_grid(df_data_ind, lookback_days=n_lookback)\n",
    "    \n",
    "    indicadores_futuros = {}\n",
    "    if not df_sim_ind.empty:\n",
    "        try:\n",
    "            precios_finales = df_sim_ind.iloc[-1]\n",
    "            media_final = precios_finales.mean()\n",
    "            idx_cercano = (precios_finales - media_final).abs().idxmin()\n",
    "            camino_realista = df_sim_ind[idx_cercano].values[1:] \n",
    "            df_futuro = df_data_ind.copy()\n",
    "            promedio_volumen = df_data_ind['Volume'].mean()\n",
    "            fechas_futuras_ind = pd.date_range(start=df_data_ind.index[-1] + pd.Timedelta(days=1), periods=horizonte_dias, freq='B')\n",
    "            filas_f = []\n",
    "            for px in camino_realista: filas_f.append({'Open': px, 'High': px * 1.002, 'Low': px * 0.998, 'Close': px, 'Adj Close': px, 'Volume': promedio_volumen})\n",
    "            df_append = pd.DataFrame(filas_f, index=fechas_futuras_ind)\n",
    "            df_futuro = pd.concat([df_futuro, df_append])\n",
    "            indicadores_futuros = calcular_indicadores_grid(df_futuro, lookback_days=horizonte_dias)\n",
    "        except: pass\n",
    "        \n",
    "    if indicadores_data:\n",
    "        claves_15 = [\"ADJ CLOSE\", \"HIGH\", \"LOW\", \"OPEN\", \"VOLUME\", \"VOL ADX\", \"VOL OBV\", \"VOL CMF\", \"VOL FI\", \"VOL MFI\", \"VOL NVI\", \"VOLAT BBH\", \"VOLAT BBL\", \"VOLAT KCH\", \"VOLAT KCL\"]\n",
    "        st.markdown(\"<style>.metric-sub { display: flex; justify-content: space-between; font-size: 11px; margin-top: 8px; color: #8b949e; border-top: 1px solid #30363d; padding-top: 6px; } .sub-title { color: #8b949e; }</style>\", unsafe_allow_html=True)\n",
    "        indicadores_filtrados = {k: indicadores_data[k] for k in claves_15 if k in indicadores_data}\n",
    "        cols = st.columns(4)\n",
    "        for i, (nombre, info) in enumerate(indicadores_filtrados.items()):\n",
    "            val_str = formatear_valor(info['val'])\n",
    "            pct_val = info.get('pct', 0.0)\n",
    "            pct_class = \"pct-up\" if pct_val > 0 else \"pct-down\" if pct_val < 0 else \"pct-neutral\"\n",
    "            pct_sign = \"+\" if pct_val > 0 else \"\"\n",
    "            fut_pct = 0.0; fut_class = \"pct-neutral\"; fut_sign = \"\"\n",
    "            if nombre in indicadores_futuros:\n",
    "                fut_val = indicadores_futuros[nombre]['val']               \n",
    "                if info['val'] != 0: fut_pct = ((fut_val - info['val']) / info['val']) * 100; fut_class = \"pct-up\" if fut_pct > 0 else \"pct-down\" if fut_pct < 0 else \"pct-neutral\"; fut_sign = \"+\" if fut_pct > 0 else \"\"\n",
    "            with cols[i % 4]:\n",
    "                st.markdown(f\"\"\"<div class='metric-card'><div class='metric-title'>{nombre}</div><div class='metric-value'>{val_str}</div><div class='metric-sub'><span><span class='sub-title'>Pasado:</span> <span class='{pct_class}'>{pct_sign}{pct_val:.1f}%</span></span><span><span class='sub-title'>Futuro:</span> <span class='{fut_class}'>{fut_sign}{fut_pct:.1f}%</span></span></div></div>\"\"\", unsafe_allow_html=True)\n",
    "                if (i + 1) % 4 == 0: st.markdown(\"<div style='margin-bottom: 20px;'></div>\", unsafe_allow_html=True)\n"
]

new_content.extend(bottom_section)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_content)

print("Refactored to Unified successfully")
