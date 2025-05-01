from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

model = None
scaler = MinMaxScaler(feature_range=(0, 1))

def init_model():
    global model
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(30, 1)),
        LSTM(50),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')

@csrf_exempt
@require_http_methods(["POST"])
def predict_price(request):
    try:
        global model, scaler
        
        data = json.loads(request.body)
        candles = data['candles']
        
        df = pd.DataFrame(candles)
        df['time'] = pd.to_datetime(df['time'], utc=True)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
        df = df.sort_values('time')
        
        closes = df['close'].values.reshape(-1, 1)
        scaled_data = scaler.fit_transform(closes)
        
        x_train, y_train = [], []
        for i in range(30, len(scaled_data)):
            x_train.append(scaled_data[i-30:i, 0])
            y_train.append(scaled_data[i, 0])
        
        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
        
        if model is None:
            init_model()
        model.fit(x_train, y_train, epochs=5, batch_size=1, verbose=0)
        
        last_30 = scaled_data[-30:]
        last_30 = np.reshape(last_30, (1, 30, 1))
        predicted = model.predict(last_30)
        predicted_price = scaler.inverse_transform(predicted)[0][0]
        
        return JsonResponse(round(float(predicted_price), 2), safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)