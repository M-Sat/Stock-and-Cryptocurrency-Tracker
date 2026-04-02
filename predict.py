import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from datetime import datetime, timedelta
import sys

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
sequence_length = 100
epochs = 30
batch_size = 32
future_steps = [1, 7, 30, 365]
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=365*5)).strftime('%Y-%m-%d')
data = yf.download(ticker, start=start_date, end=end_date)

data['MA50'] = data['Close'].rolling(50).mean()
data['MA200'] = data['Close'].rolling(200).mean()
data['Return'] = np.log(data['Close'] / data['Close'].shift(1))
data.dropna(inplace=True)
features_cols = ['Close', 'MA50', 'MA200', 'Volume', 'Return']
target_col_index = 4

scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data[features_cols])

target_scaler = MinMaxScaler()
target_scaler.fit(data[['Return']])

X, y = [], []
prices_prev = [] 

for i in range(sequence_length, len(scaled_data) - max(future_steps)):
    X.append(scaled_data[i-sequence_length:i])
    
    targets = []
    for step in future_steps:
        targets.append(scaled_data[i + step][target_col_index])
    y.append(targets)
    prices_prev.append(data['Close'].iloc[i-1])

X, y = np.array(X), np.array(y)
prices_prev = np.array(prices_prev)

split = int(0.8 * len(X))
X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]
prices_prev_val = prices_prev[split:]
model = tf.keras.models.Sequential([
    tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(len(future_steps))
])

model.compile(optimizer='adam', loss='huber')

early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
history = model.fit(X_train, y_train, validation_data=(X_val, y_val), 
                    epochs=epochs, batch_size=batch_size, callbacks=[early_stop], verbose=1)
predictions_scaled = model.predict(X_val)

predictions_rescaled = target_scaler.inverse_transform(predictions_scaled)
y_val_rescaled = target_scaler.inverse_transform(y_val)

pred_prices = np.zeros_like(predictions_rescaled)
actual_prices = np.zeros_like(y_val_rescaled)

for i in range(len(prices_prev_val)):
    pred_prices[i] = prices_prev_val[i] * np.exp(predictions_rescaled[i])
    actual_prices[i] = prices_prev_val[i] * np.exp(y_val_rescaled[i])
print("\nModel Performance (MAE):")
for i, step in enumerate(future_steps):
    mae = mean_absolute_error(actual_prices[:, i], pred_prices[:, i])
    print(f"t+{step} days: ${mae:.2f}")

last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, len(features_cols))
future_preds_scaled = model.predict(last_sequence)
future_returns = target_scaler.inverse_transform(future_preds_scaled)[0]

last_real_price = float(data['Close'].iloc[-1])
future_prices = [last_real_price * np.exp(r) for r in future_returns]

print("\nFuture Price Projections:")
for step, price in zip(future_steps, future_prices):
    print(f"+{step} days: ${price:.2f}")

plt.style.use('dark_background')
fig = plt.figure(figsize=(14, 6), facecolor='#0b0e14')
fig.patch.set_facecolor('#0b0e14')

DARK_BG = '#0b0e14'
ACCENT_BLUE = '#007bff'
ACCENT_GREEN = '#28a745'
ACCENT_RED = '#dc3545'
TEXT_COLOR = '#ffffff'
GRID_COLOR = '#252940'
ax1 = plt.subplot(1, 2, 1)
ax1.set_facecolor('#161926')
ax1.plot(actual_prices[:, 0], label="Actual", color=ACCENT_BLUE, linewidth=2.5, alpha=0.8)
ax1.plot(pred_prices[:, 0], label="Predicted", color=ACCENT_GREEN, linestyle='--', linewidth=2.5, alpha=0.8)
ax1.set_title("Validation: 1-Day Prediction", fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)
ax1.set_xlabel("Sample", fontsize=11, color=TEXT_COLOR)
ax1.set_ylabel("Price ($)", fontsize=11, color=TEXT_COLOR)
ax1.legend(loc='best', fontsize=10, framealpha=0.95)
ax1.grid(True, alpha=0.2, color=GRID_COLOR)
ax1.tick_params(colors=TEXT_COLOR)

ax2 = plt.subplot(1, 2, 2)
ax2.set_facecolor('#161926')

x_labels = [f"{s}d" for s in future_steps]
x_pos = np.arange(len(x_labels))
bars = ax2.bar(x_pos, future_prices, color=ACCENT_GREEN, alpha=0.8, edgecolor=ACCENT_BLUE, linewidth=2)
ax2.axhline(y=last_real_price, color=ACCENT_BLUE, linestyle='-', linewidth=2.5, 
            label=f'Current: ${last_real_price:.2f}', alpha=0.7)

for idx, (bar, price) in enumerate(zip(bars, future_prices)):
    pct_change = ((price - last_real_price) / last_real_price) * 100
    value_color = ACCENT_GREEN if pct_change > 0 else ACCENT_RED
    
    ax2.text(bar.get_x() + bar.get_width()/2, price + (max(future_prices) * 0.01),
             f'${price:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold', color=TEXT_COLOR)
    
    pct_text = f'{pct_change:+.2f}%'
    ax2.text(bar.get_x() + bar.get_width()/2, last_real_price - (max(future_prices) * 0.03),
             pct_text, ha='center', va='top', fontsize=10, fontweight='bold', color=value_color)

ax2.set_xticks(x_pos)
ax2.set_xticklabels(x_labels, fontsize=11, color=TEXT_COLOR)
ax2.set_ylabel("Price ($)", fontsize=11, color=TEXT_COLOR)
ax2.set_title("Future Price Projections", fontsize=14, fontweight='bold', color=TEXT_COLOR, pad=15)
ax2.legend(loc='lower left', fontsize=10, framealpha=0.95)
ax2.grid(True, alpha=0.2, axis='y', color=GRID_COLOR)
ax2.tick_params(colors=TEXT_COLOR)

# Format y-axis as currency
formatter = plt.FuncFormatter(lambda x, p: f'${x:.0f}')
ax2.yaxis.set_major_formatter(formatter)

plt.tight_layout()
plt.savefig('prediction_plot.png', facecolor='#0b0e14', dpi=150, bbox_inches='tight')
print("\n[PLOT_SAVED]")