import pandas as pd
import yfinance as yf
import xgboost as xgb
import pickle
import json
import warnings

# Ignorar advertencias de pandas
warnings.filterwarnings('ignore')

print("🤖 Iniciando proceso de retrenamiento del Oráculo...")

# --- PASO 1: CARGAR EL DICCIONARIO ---
with open('src/diccionario_tickers.json', 'r') as f:
    diccionario_tickers = json.load(f)

lista_dataframes = []

print("📥 Descargando datos recientes de Wall Street...")
for ticker, ticker_encoded in diccionario_tickers.items():
    try:
        # Descargamos los últimos 2 años de datos
        df = yf.download(ticker, period="2y", progress=False)
        
        # Necesitamos al menos 200 días para calcular la Media Móvil de 200 (SMA200)
        if len(df) < 200:
            continue
            
        df['Ticker_Encoded'] = ticker_encoded
        
        # --- CÁLCULOS TÉCNICOS ---
        # 1. Variables Base
        df['Std_20'] = df['Close'].rolling(window=20).std()
        df['Momentum_10'] = df['Close'] - df['Close'].shift(10)
        df['High_Low_Spread'] = df['High'] - df['Low']
        
        # 2. Variables de Volumen
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
        df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA_20']
        df['Vol_Change'] = df['Volume'].pct_change().fillna(0)
        
        # 3. Variables de Medias Móviles y Máximos
        sma200 = df['Close'].rolling(window=200).mean()
        df['Above_SMA200'] = (df['Close'] > sma200).astype(int)
        
        high_50 = df['High'].rolling(window=50).max()
        df['Pct_From_High_50'] = (df['Close'] - high_50) / high_50

        # 4. MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_Line'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']
        
        # 5. Z-Score y RSI
        sma20 = df['Close'].rolling(window=20).mean()
        df['Z_Score_20'] = (df['Close'] - sma20) / df['Std_20']
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # --- LA VARIABLE OBJETIVO (Target) ---
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        # Limpieza de nulos por los cálculos "rolling"
        df = df.dropna()
        lista_dataframes.append(df)
        
    except Exception as e:
        pass

df_final = pd.concat(lista_dataframes)

# --- PASO 3: PREPARAR LOS DATOS ---
print("⚙️ Preparando datos para XGBoost...")

# Aquí están TODAS las columnas que tu modelo nos pidió en el error
columnas_entrenamiento = [
    'Volume', 'Std_20', 'MACD_Line', 'MACD_Signal', 'MACD_Hist', 
    'RSI_14', 'Momentum_10', 'Vol_SMA_20', 'Vol_Ratio', 'Vol_Change', 
    'High_Low_Spread', 'Z_Score_20', 'Above_SMA200', 'Pct_From_High_50',
    'Ticker_Encoded'
]

# Si el orden falla por alguna razón con tu modelo original, 
# el modelo se reentrenará usando este nuevo orden correcto.
X = df_final[columnas_entrenamiento]
y = df_final['Target']

# --- PASO 4: ENTRENAR ---
print("🧠 Entrenando la Inteligencia Artificial...")
modelo_xgb = xgb.XGBClassifier(
    learning_rate=0.1, 
    max_depth=7, 
    n_estimators=200,
    random_state=42
)

modelo_xgb.fit(X, y)

# --- PASO 5: GUARDAR ---
ruta_modelo = 'models/modelo_financiero_prueba_xgb.pkl'
with open(ruta_modelo, 'wb') as archivo:
    pickle.dump(modelo_xgb, archivo)

print(f"✅ ¡Éxito! El nuevo modelo ha sido entrenado y guardado en {ruta_modelo}")