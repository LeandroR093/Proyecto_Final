path = r"C:\Users\Farmatodo Kike\.gemini\antigravity\brain\04bb0ed0-838d-4121-ae3f-51514634b65f\task.md"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Mark Phase 6 complete
content = content.replace("- [ ] Implement Normalized returns", "- [x] Implement Normalized returns")
content = content.replace("- [ ] Render superimposition Plotly", "- [x] Render superimposition Plotly")
content = content.replace("- [ ] Add conditional fallback UI", "- [x] Add conditional fallback UI")

# Append Phase 7 if not already there
if "Phase 7" not in content:
    content += """
## Phase 7: Analíticas Avanzadas y Carga desde DB [NEW]
- [ ] Implement `cargar_datos_db(ticker)` fallback logic <!-- id: 21 -->
- [ ] Add Correlation Matrix heatmap in `app.py` <!-- id: 22 -->
- [ ] Add Risk-Adjusted metrics (Sharpe, Drawdown) inside cards <!-- id: 23 -->
- [ ] Add Backtesting tab in UI <!-- id: 24 -->
- [ ] Add Stress Testing slider in Sidebar <!-- id: 25 -->
"""

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated task.md successfully")
