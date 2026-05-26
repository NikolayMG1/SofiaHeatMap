import pandas as pd

df = pd.read_csv("sofia_temps.csv")

df["date"] = pd.to_datetime(df["date"])
df["temp_mean"] = pd.to_numeric(df["temp_mean"], errors="coerce")

df = df.dropna(subset=["temp_mean", "date"])


daily_avg = df.groupby("date")["temp_mean"].mean().reset_index()
daily_avg.columns = ["date", "avg_temp"]

daily_avg["rolling_avg"] = daily_avg["avg_temp"].rolling(window=7).mean()


import matplotlib.pyplot as plt

plt.figure(figsize=(12,5))
plt.plot(daily_avg["date"], daily_avg["avg_temp"], alpha=0.4, label="Daily avg")
plt.plot(daily_avg["date"], daily_avg["rolling_avg"], linewidth=2, label="7-day avg")

plt.title("Sofia Average Temperature Over Time")
plt.xlabel("Date")
plt.ylabel("Temperature (°C)")
plt.legend()
plt.show()


from sklearn.linear_model import LinearRegression
import numpy as np

df_trend = daily_avg.dropna()

X = np.array((df_trend["date"] - df_trend["date"].min()).dt.days).reshape(-1, 1)
y = df_trend["avg_temp"].values

model = LinearRegression()
model.fit(X, y)

slope = model.coef_[0]

print("Temperature trend per day:", slope, "°C/day")
print("Per year approx:", slope * 365, "°C/year")

district_avg = df.groupby("district")["temp_mean"].mean().sort_values()

print(district_avg)

