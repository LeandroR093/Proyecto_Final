import numpy as np
import pandas as pd

def ejecutar_monte_carlo(df, dias_proyeccion=30, n_simulaciones=1000, vol_mult=1.0):
    """
    Ejecuta una simulación estocástica basada en Movimiento Browniano Geométrico (GBM).
    Refinado para asegurar coherencia estadística y reproductibilidad.
    """
    if df.empty or len(df) < 20:
        return pd.DataFrame(), {}
        
    # Calcular retornos logarítmicos
    precios = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
    retornos_log = np.log(precios / precios.shift(1)).dropna()
    
    # Parámetros base diarios
    mu = retornos_log.mean() 
    sigma_base = retornos_log.std()
    
    # Aplicar Multiplicador de Volatilidad (Stress Test)
    # Si aumentamos la volatilidad, el componente de drift (mu - 0.5 * sigma^2) 
    # debe recalcularse para mantener la coherencia del modelo GBM.
    sigma_adj = sigma_base * vol_mult
    drift_adj = mu - (0.5 * (sigma_adj**2))
    
    # Precio inicial
    S0 = precios.iloc[-1]
    
    # Generación de caminos (Vectorizada para performance)
    # W_t ~ N(0, 1) con semilla fija para determinismo
    rng = np.random.default_rng(42)
    shocks = rng.normal(0, 1, (dias_proyeccion, n_simulaciones))
    
    # Matriz de incrementos: exp((mu - 0.5*sigma^2) + sigma * Z)
    incrementos = np.exp(drift_adj + sigma_adj * shocks)
    
    # Concatenar precio inicial y calcular producto acumulado
    caminos = np.vstack([np.full(n_simulaciones, S0), incrementos])
    precios_simulados = np.cumprod(caminos, axis=0)
    
    # Convertir a DataFrame (Filas = Días, Columnas = Simulaciones)
    df_sim = pd.DataFrame(precios_simulados)
    
    # Estadísticas de resumen
    precios_finales = precios_simulados[-1, :]
    stats = {
        "current_price": S0,
        "mean_projection": np.mean(precios_finales),
        "median_projection": np.median(precios_finales),
        "lower_bound": np.percentile(precios_finales, 5), # Escenario Pesimista
        "upper_bound": np.percentile(precios_finales, 95), # Escenario Optimista
        "std_dev": np.std(precios_finales),
        "n_simulaciones": n_simulaciones,
        "dias": dias_proyeccion
    }
    
    return df_sim, stats
