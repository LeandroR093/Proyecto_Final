import pandas as pd
import yfinance as yf
import xgboost as xgb
import pickle
import json
import warnings

# Ignorar advertencias de pandas para que la consola quede limpia
warnings.filterwarnings('ignore')

print("🤖 Iniciando proceso de retrenamiento del Oráculo...")

# --- PASO 1: CARGAR EL DICCIONARIO ---
with open('src/diccionario_tickers.json', 'r') as f:
    diccionario_tickers = json.load(f)

# --- PASO 2: DESCARGAR DATOS Y CREAR VARIABLES ---
# Aquí guardaremos los datos de todas las empresas juntos
lista_dataframes = []

print("📥 Descargando datos recientes de Wall Street...")
for ticker, ticker_encoded in diccionario_tickers.items():
    try:
        # Descargamos los últimos 2 años de datos para tener contexto reciente
        df = yf.download(ticker, period="2y", progress=False)
        
        # Si la empresa es muy nueva y no tiene datos suficientes, la saltamos
        if len(df) < 50:
            continue
            
        # 1. Variables de Identificación
        df['Ticker_Encoded'] = ticker_encoded
        
        # 2. Cálculos Técnicos (Exactamente iguales a tu Jupyter Notebook)
        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD_Line'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']
        
        # Z-Score
        sma20 = df['Close'].rolling(window=20).mean()
        std20 = df['Close'].rolling(window=20).std()
        df['Z_Score_20'] = (df['Close'] - sma20) / std20
        
        # RSI Simple
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # 3. LA VARIABLE OBJETIVO (El Futuro)
        # ¿El cierre de mañana es mayor al de hoy? (1 = Sube, 0 = Baja)
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        # Borramos las filas que quedaron con NaN (por los promedios y el shift)
        df = df.dropna()
        
        # Guardamos este pedacito de tabla en nuestra lista general
        lista_dataframes.append(df)
        
    except Exception as e:
        # Si Yahoo Finance falla con una empresa, simplemente pasamos a la siguiente
        pass

# Unimos todas las empresas en una sola super-tabla
df_final = pd.concat(lista_dataframes)

# --- PASO 3: PREPARAR LOS DATOS PARA EL MODELO ---
print("⚙️ Preparando datos para XGBoost...")

# Seleccionamos SOLO las columnas con las que entrenamos (ajusta esta lista a las tuyas)
columnas_entrenamiento = [
    'Volume', 'Std_20', 'MACD_Line', 'MACD_Signal', 'MACD_Hist', 'RSI_14', 
    'Momentum_10', 'Vol_SMA_20', 'Vol_Ratio', 'Vol_Change', 'High_Low_Spread', 
    'Z_Score_20', 'Above_SMA200', 'Pct_From_High_50', 'Ticker_Encoded'
    ]

X = df_final[columnas_entrenamiento]
y = df_final['Target']

# Opcional: Si quieres entrenar con TODOS los datos recientes para máxima precisión
# no necesitas hacer train_test_split aquí, ¡le das todo el conocimiento al modelo!

# --- PASO 4: ENTRENAR EL NUEVO MODELO ---
print("🧠 Entrenando la Inteligencia Artificial...")

# Usamos los hiperparámetros óptimos que encontraste con GridSearchCV
modelo_xgb = xgb.XGBClassifier(
    learning_rate=0.1, 
    max_depth=7, 
    n_estimators=200,
    random_state=42
)

# Entrenamos con toda la base de datos fresca
modelo_xgb.fit(X, y)

# --- PASO 5: GUARDAR EL NUEVO CEREBRO ---
ruta_modelo = 'models/modelo_financiero_prueba_xgb.pkl'

with open(ruta_modelo, 'wb') as archivo:
    pickle.dump(modelo_xgb, archivo)

print(f"✅ ¡Éxito! El nuevo modelo ha sido entrenado y guardado en {ruta_modelo}")