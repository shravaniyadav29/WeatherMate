import os

import requests
from fastapi import FastAPI, HTTPException

app = FastAPI(title="WeatherMate Backend")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


@app.get("/")
def home():
    return {
        "message": "WeatherMate Backend is running"
    }


@app.get("/weather")
def get_weather(city: str):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenWeather API key is not configured on the server."
        )

    try:
        response = requests.get(
            f"{OPENWEATHER_BASE_URL}/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=15,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Weather request failed.")
            )

        return response.json()

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to OpenWeather."
        )


@app.get("/forecast")
def get_forecast(city: str):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenWeather API key is not configured on the server."
        )

    try:
        response = requests.get(
            f"{OPENWEATHER_BASE_URL}/forecast",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=15,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("message", "Forecast request failed.")
            )

        return response.json()

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to OpenWeather."
        )