import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
import ssl
import certifi

data = pd.read_csv("POWER_Point_Monthly_20150101_20251231_018d97N_072d82E_UTC.csv", skiprows=14)

st.markdown("""
<style>
.main {
    background-color: #f7f9fc;
}

h1 {
    color: #1f2937;
}

h2, h3 {
    color: #374151;
}

div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #e5e7eb;
    padding: 15px;
    border-radius: 10px;
}

div[data-testid="stMetric"] label {
    color: #374151 !important;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #111827 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🌦️ Mumbai Climate Analysis Dashboard")
st.caption("Historical Climate Trends • Current Weather Monitoring")
st.write("📍 Mumbai, Maharashtra | 📅 Historical data: 2015–2025")


# live weather data
st.divider()
st.header("Live Mumbai Weather")

weather_url = (
    "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    "?lat=18.97&lon=72.82"
)

weather_req = urllib.request.Request(
    weather_url,
    headers={
        "User-Agent": "MumbaiClimateDashboard/1.0 (contact: YOUR_EMAIL_ADDRESS)"
    }
)

try:
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    with urllib.request.urlopen(
        weather_req,
        timeout=25,
        context=ssl_context
    ) as response:
        weather_data = json.loads(response.read().decode())

    timeseries = weather_data["properties"]["timeseries"]

    # Current weather
    current = timeseries[0]["data"]["instant"]["details"]

    temperature = current.get("air_temperature", 0)
    humidity = current.get("relative_humidity", 0)
    wind_speed = current.get("wind_speed", 0)

    current_period = (
        timeseries[0]["data"].get("next_1_hours")
        or timeseries[0]["data"].get("next_6_hours")
        or {}
    )

    current_precipitation = current_period.get(
        "details", {}
    ).get("precipitation_amount", 0)

    current_summary = current_period.get("summary", {})
    weather_condition = current_summary.get(
        "symbol_code", "Condition unavailable"
    ).replace("_", " ").title()

    st.subheader("Current Mumbai Weather")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🌡️ Temperature", f"{temperature} °C")
    col2.metric("💧 Humidity", f"{humidity} %")
    col3.metric("🌧️ Precipitation", f"{current_precipitation} mm")
    col4.metric("💨 Wind Speed", f"{wind_speed * 3.6:.1f} km/h")

    st.info(f"Current condition: {weather_condition}")

    # --------------------------------------------------
    # SEVEN-DAY FORECAST
    # --------------------------------------------------

    st.subheader("📅 7-Day Weather Forecast")

    forecast_rows = []

    for item in timeseries:

        local_time = (
            pd.to_datetime(item["time"], utc=True)
            .tz_convert("Asia/Kolkata")
        )

        instant = item["data"]["instant"]["details"]

        period = (
            item["data"].get("next_1_hours")
            or item["data"].get("next_6_hours")
            or {}
        )

        period_details = period.get("details", {})

        forecast_rows.append({
            "Date": local_time.date(),
            "Temperature": instant.get("air_temperature"),
            "Rainfall": period_details.get("precipitation_amount", 0)
        })

    forecast_source = pd.DataFrame(forecast_rows)

    forecast_df = (
        forecast_source.groupby("Date")
        .agg(
            **{
                "Max Temperature (°C)": ("Temperature", "max"),
                "Min Temperature (°C)": ("Temperature", "min"),
                "Rainfall (mm)": ("Rainfall", "sum")
            }
        )
        .head(7)
        .reset_index()
    )

    forecast_df["Date"] = pd.to_datetime(
        forecast_df["Date"]
    ).dt.strftime("%d %b %Y")

    st.dataframe(
        forecast_df.round(1),
        use_container_width=True,
        hide_index=True
    )

    if len(forecast_df) < 7:
        st.warning("The weather provider returned fewer than seven forecast days.")

except Exception as e:
    st.warning(
        "Live weather is temporarily unavailable. "
        "Please try again later."
    )
    st.caption(f"Weather service error: {e}")


st.header("📊 Historical Climate Analysis")
st.write("Explore Mumbai's climate data from 2015 to 2025.")


parameter_names = {
    "T2M": "Temperature",
    "T2M_MAX": "Maximum Temperature",
    "T2M_MIN": "Minimum Temperature",
    "RH2M": "Relative Humidity",
    "WS2M": "Wind Speed",
    "PRECTOTCORR_SUM": "Precipitation"
}

parameter_units = {
    "T2M": "°C",
    "T2M_MAX": "°C",
    "T2M_MIN": "°C",
    "RH2M": "%",
    "WS2M": "m/s",
    "PRECTOTCORR_SUM": "mm"
}

selected_name = st.selectbox(
    "Choose a parameter to analyze",
    list(parameter_names.values())
)


selected_parameter = {
    value: key for key, value in parameter_names.items()
}[selected_name]

unit = parameter_units[selected_parameter]

filtered_data = data[data["PARAMETER"] == selected_parameter]

st.subheader(f"📈 Annual {selected_name} ({unit})")

st.line_chart(
    filtered_data.set_index("YEAR")["ANN"]
)

selected_year = st.selectbox("Select a year", filtered_data["YEAR"].unique())

year_data = filtered_data[filtered_data["YEAR"] == selected_year]

st.subheader(f"📅 Monthly {selected_name} for {selected_year} ({unit})")

monthly_data = year_data[
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
     "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
].T

st.line_chart(monthly_data)

st.subheader("Climate Change Trend Analysis")

years = filtered_data["YEAR"].astype(int)
values = filtered_data["ANN"].astype(float)

slope = np.polyfit(years, values, 1)[0]

first_value = values.iloc[0]
last_value = values.iloc[-1]
change = last_value - first_value

percentage_change = (change / first_value) * 100

col1, col2, col3 = st.columns(3)

col1.metric(
    "Change (2015–2025)",
    f"{change:.2f} {unit}"
)

col2.metric(
    "Percentage Change",
    f"{percentage_change:.2f}%"
)

col3.metric(
    "Annual Trend",
    f"{slope:.2f} {unit}/year"
)

trend = "increasing" if slope > 0 else "decreasing"

st.success(f"Detected historical trend: {trend}")

