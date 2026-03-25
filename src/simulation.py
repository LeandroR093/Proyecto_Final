import numpy as np
import pandas as pd

def ejecutar_monte_carlo(df, dias_proyeccion=30, n_simulaciones=1000, vol_mult=1.0):
    """
    Ejecuta una simulación de Monte Carlo basada en Movimiento Browniano Geométrico (GBM).
    Retorna los caminos simulados y estadísticas de resumen.
    """
    if df.empty or len(df) < 20:
        return pd.DataFrame(), {}
        
    # Calcular retornos logarítmicos
    precios = df['Close'] if 'Close' in df else df['Adj Close']
    retornos_log = np.log(precios / precios.shift(1)).dropna()
    
    # Parámetros del modelo
    mu = retornos_log.mean() # Drift diario
    var = retornos_log.var()  # Varianza diaria
    sigma = retornos_log.std() * vol_mult # Volatilidad diaria Ajustada por Stress Test

    
    # Drift ajustado por varianza
    drift = mu - (0.5 * var)
    
    # Precio inicial (último precio conocido)
    S0 = precios.iloc[-1]
    
    # Matriz de números aleatorios normales N(0,1)
    # n_simulaciones caminos, dias_proyeccion pasos
    shocks = np.random.normal(0, 1, (n_simulaciones, dias_proyeccion))
    
    # Calcular retornos diarios simulados
    # drift + sigma * shocks
    retornos_simulados = np.exp(drift + sigma * shocks)
    
    # Crear matriz de precios simulados
    precios_simulados = np.zeros((n_simulaciones, dias_proyeccion + 1))
    precios_simulados[:, 0] = S0
    
    for t in range(1, dias_proyeccion + 1):
        precios_simulados[:, t] = precios_simulados[:, t-1] * retornos_simulados[:, t-1]
        
    # Convertir a DataFrame para facilitar el uso en Plotly
    # Transponer para que las filas sean los días (pasos) y columnas las simulaciones
    df_sim = pd.DataFrame(precios_simulados.T)
    
    # Estadísticas de resumen al final de la proyección (Última fila)
    precios_finales = precios_simulados[:, -1]
    mean_projection = np.mean(precios_finales)
    
    # Intervalo de confianza del 90% (Percentiles 5% y 95%)
    lower_bound = np.percentile(precios_finales, 5)
    upper_bound = np.percentile(precios_finales, 95)
    
    stats = {
        "current_price": S0,
        "mean_projection": mean_projection,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "n_simulaciones": n_simulaciones,
        "dias": dias_proyeccion
    }
    
    return df_sim, stats
