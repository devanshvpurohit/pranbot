import time
import os
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ===================== CONFIG =====================
ESP32_IP = "http://192.168.4.1"
REFRESH_SEC = 1
HISTORY = 120
GRID_SIZE = 20
EMA_ALPHA = 0.2
CMD_TIMEOUT = 0.4
DANGER_GPI = 200

# ===================== SENSOR MODEL =====================
MQ_SENSORS = {
    "MQ2":   {"json": "smoke",   "clean_adc": 800, "weight": 1.2},
    "MQ3":   {"json": "methane", "clean_adc": 120, "weight": 1.0},
    "MQ7":   {"json": "co",      "clean_adc": 40,  "weight": 1.5},
    "MQ135": {"json": "air",     "clean_adc": 90,  "weight": 1.0},
}

AQI_BANDS = [
    (0, 50, "Good", "green"),
    (51, 100, "Moderate", "yellow"),
    (101, 200, "Unhealthy", "orange"),
    (201, 300, "Very Unhealthy", "red"),
    (301, 500, "Hazardous", "purple"),
]

# ===================== PAGE =====================
st.set_page_config("Autonomous Gas Robot", layout="wide")
st.title("🤖 Autonomous Gas Detection Robot")
st.caption("AQI-Style GPI • EMA Stabilized • Industrial Sensor Logic")

# ===================== SESSION STATE =====================
if "sensors" not in st.session_state:
    st.session_state.sensors = {
        s: {
            "raw": [],
            "rs_r0": [],
            "r0": cfg["clean_adc"],
            "health": "WARMUP"
        } for s, cfg in MQ_SENSORS.items()
    }
    st.session_state.gpi_raw = []
    st.session_state.gpi_ema = []
    st.session_state.log_rows = []

# ===================== ESP HELPERS =====================
def fetch_data():
    try:
        return requests.get(f"{ESP32_IP}/data", timeout=0.6).json()
    except:
        return None

def send_cmd(cmd):
    try:
        requests.get(f"{ESP32_IP}/cmd?d={cmd}", timeout=CMD_TIMEOUT)
    except:
        pass

# ===================== MQ CORE =====================
def rs_r0(adc, r0):
    return max(adc, 1) / max(r0, 1)

def auto_calibrate(sensor):
    if len(sensor["raw"]) >= 60:
        avg = np.mean(sensor["raw"][-60:])
        if avg < sensor["r0"] * 1.2:
            sensor["r0"] = avg

def health_check(sensor):
    vals = sensor["raw"]
    if len(vals) < 10:
        return "WARMUP"
    if max(vals[-10:]) - min(vals[-10:]) < 2:
        return "STUCK"
    if np.std(vals[-20:]) > 0.6 * np.mean(vals[-20:]):
        return "NOISY"
    if np.mean(vals[-20:]) < 3:
        return "DEAD"
    return "OK"

def gpi_from_ratio(r):
    return min(int(100 * np.log10(1 + r * 5)), 500)

def ema(prev, val):
    return val if prev is None else EMA_ALPHA * val + (1 - EMA_ALPHA) * prev

# ===================== MAIN LOOP =====================
raw = fetch_data()
gpi_raw = 0
gpi_ema = 0

if raw:
    gpi_parts = []

    for name, cfg in MQ_SENSORS.items():
        s = st.session_state.sensors[name]
        adc = raw.get(cfg["json"], 0)

        s["raw"].append(adc)
        s["raw"] = s["raw"][-HISTORY:]

        auto_calibrate(s)

        ratio = rs_r0(adc, s["r0"])
        s["rs_r0"].append(ratio)
        s["rs_r0"] = s["rs_r0"][-HISTORY:]

        s["health"] = health_check(s)

        if s["health"] == "OK":
            gpi_parts.append(gpi_from_ratio(ratio) * cfg["weight"])

    if gpi_parts:
        gpi_raw = int(np.mean(gpi_parts))

    st.session_state.gpi_raw.append(gpi_raw)
    st.session_state.gpi_raw = st.session_state.gpi_raw[-HISTORY:]

    prev = st.session_state.gpi_ema[-1] if st.session_state.gpi_ema else None
    gpi_ema = int(ema(prev, gpi_raw))
    st.session_state.gpi_ema.append(gpi_ema)
    st.session_state.gpi_ema = st.session_state.gpi_ema[-HISTORY:]

    # 🚨 Safety stop
    if gpi_ema >= DANGER_GPI:
        send_cmd("s")
        send_cmd("bz")

    # 📋 Logging
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "GPI_RAW": gpi_raw,
        "GPI_EMA": gpi_ema
    }
    for s in MQ_SENSORS:
        row[f"{s}_ADC"] = st.session_state.sensors[s]["raw"][-1]
        row[f"{s}_Rs_R0"] = st.session_state.sensors[s]["rs_r0"][-1]
        row[f"{s}_Health"] = st.session_state.sensors[s]["health"]
    st.session_state.log_rows.append(row)

# ===================== UI =====================
def aqi_label(val):
    for lo, hi, name, color in AQI_BANDS:
        if lo <= val <= hi:
            return name, color
    return "Unknown", "gray"

label, color = aqi_label(gpi_ema)
st.markdown(f"## 🔥 GPI: **{gpi_ema}** — :{color}[{label}]")

# ===================== ROBOT CONTROLS =====================
st.subheader("🎮 Robot Controls")
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("⬆ Forward"): send_cmd("f")
if c2.button("⬅ Left"): send_cmd("l")
if c3.button("➡ Right"): send_cmd("r")
if c4.button("⬇ Back"): send_cmd("b")
if c5.button("⏹ Stop"): send_cmd("s")

b1, b2 = st.columns(2)
if b1.button("🔊 Buzzer ON"): send_cmd("bz")
if b2.button("🔇 Buzzer OFF"): send_cmd("bo")

# ===================== SENSOR HEALTH =====================
st.subheader("📡 Sensor Health")
cols = st.columns(len(MQ_SENSORS))
for i, s in enumerate(MQ_SENSORS):
    h = st.session_state.sensors[s]["health"]
    if h == "OK":
        cols[i].success(f"{s}\nOK")
    else:
        cols[i].warning(f"{s}\n{h}")

# ===================== PLOTS =====================
st.subheader("📈 Rs/R₀ Trends")
for s in MQ_SENSORS:
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=st.session_state.sensors[s]["rs_r0"], mode="lines"))
    fig.update_layout(height=250, title=s)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🔥 GPI (EMA)")
fig = go.Figure()
fig.add_trace(go.Scatter(y=st.session_state.gpi_ema, mode="lines+markers"))
fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

# ===================== SAVE SESSION =====================
st.subheader("💾 Save Session")

def next_filename():
    date = datetime.now().strftime("%Y_%m_%d")
    os.makedirs("sessions", exist_ok=True)
    n = 1
    while True:
        f = f"sessions/gas_session_{date}__{n}.xlsx"
        if not os.path.exists(f):
            return f
        n += 1

if st.button("💾 Save to Excel"):
    if len(st.session_state.log_rows) < 5:
        st.warning("Not enough data yet.")
    else:
        df = pd.DataFrame(st.session_state.log_rows)
        fname = next_filename()
        df.to_excel(fname, index=False)
        st.success(f"Saved: {fname}")

time.sleep(REFRESH_SEC)
st.rerun()
