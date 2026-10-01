import asyncio
import difflib
import base64
import os
from datetime import datetime, timezone, timedelta

import flet as ft
import requests

import database


# ============================================================
# REAL-WORLD SUNRISE / SUNSET LOGOS
# ============================================================

def weather_detail_logo(kind):
    if kind == "sunrise":
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M10 46h44" stroke="#D9E7FF" stroke-width="4" stroke-linecap="round"/><path d="M20 46a12 12 0 0 1 24 0" fill="#FFD166"/><path d="M32 10v8M17 17l6 6M47 17l-6 6M10 29h9M45 29h9" stroke="#FFD166" stroke-width="3.5" stroke-linecap="round"/></svg>"""
    else:
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M10 46h44" stroke="#D9E7FF" stroke-width="4" stroke-linecap="round"/><path d="M20 46a12 12 0 0 1 24 0" fill="#FFD166"/><path d="M32 54v-8M17 47l6-6M47 47l-6-6M10 35h9M45 35h9" stroke="#FFD166" stroke-width="3.5" stroke-linecap="round"/></svg>"""
    return base64.b64encode(svg.encode("utf-8")).decode("utf-8")


BACKEND_URL = os.getenv(
    "WEATHER_BACKEND_URL",
    "http://127.0.0.1:8000"
)
# ============================================================
# COLORS
# ============================================================

BG = "#07111B"
CARD = "#CC0D1B2A"
CARD2 = "#CC102235"

WHITE = "#FFFFFF"
GREY = "#B8C4CE"

BLUE = "#42A5F5"
LIGHT_BLUE = "#90CAF9"

GREEN = "#66BB6A"
RED = "#EF5350"

YELLOW = "#FFD166"


# ============================================================
# CITY BACKGROUND IMAGE API - WIKIMEDIA COMMONS
# ============================================================

def get_city_image(city):
    """
    Find a real photograph specifically related to the searched city.

    The API search is deliberately strict: the selected Wikimedia
    filename/title must contain the city name. This prevents the same
    generic landscape image from being reused for every city.
    """

    if not city:
        return None

    url = "https://commons.wikimedia.org/w/api.php"

    city_clean = city.strip()
    city_words = [
        word.lower()
        for word in city_clean
        .replace(",", " ")
        .split()
        if len(word) >= 3
    ]

    if not city_words:
        return None

    blocked_words = {
        "map", "diagram", "logo", "icon", "chart", "symbol",
        "station", "screenshot", "flag", "coat of arms",
        "poster", "painting", "illustration", "drawing",
        "portrait", "collage", "graphic", "render",
        "sculpture", "museum", "frame", "canvas",
        "weather", "satellite", "route", "street map",
        "location map", "district map", "municipal map",
    }

    headers = {
        "User-Agent": (
            "WeatherMate/1.0 "
            "(student weather information project)"
        )
    }

    # Exact city-focused searches are attempted first.
    search_terms = [
        f'"{city_clean}" skyline',
        f'"{city_clean}" cityscape',
        f'"{city_clean}" city photograph',
        f'"{city_clean}" landmark photograph',
        city_clean,
    ]

    for search_text in search_terms:

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": search_text,
            "gsrnamespace": 6,
            "gsrlimit": 50,
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1920,
            "format": "json",
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=15,
                headers=headers,
            )

            response.raise_for_status()

            data = response.json()

            pages = (
                data.get("query", {})
                .get("pages", {})
            )

            candidates = []

            for page in pages.values():

                title = page.get(
                    "title",
                    "",
                )

                title_lower = title.lower()

                if any(
                    word in title_lower
                    for word in blocked_words
                ):
                    continue

                # IMPORTANT:
                # Require the city name to actually appear in
                # the image title. This stops generic images from
                # becoming every city's background.
                city_match = any(
                    word in title_lower
                    for word in city_words
                )

                if not city_match:
                    continue

                image_info = page.get(
                    "imageinfo",
                    [],
                )

                if not image_info:
                    continue

                info = image_info[0]

                mime = info.get(
                    "mime",
                    "",
                ).lower()

                if mime not in {
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                }:
                    continue

                width = int(
                    info.get("width") or 0
                )

                height = int(
                    info.get("height") or 0
                )

                if width < 1000 or height < 500:
                    continue

                if height <= 0:
                    continue

                aspect_ratio = width / height

                if aspect_ratio < 1.30:
                    continue

                image_url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                if not image_url:
                    continue

                score = 100

                if "skyline" in title_lower:
                    score += 50

                if "cityscape" in title_lower:
                    score += 45

                if "landmark" in title_lower:
                    score += 30

                if "photograph" in title_lower:
                    score += 15

                # Prefer wider photographs.
                score += min(
                    width / 1000,
                    15,
                )

                candidates.append(
                    (
                        score,
                        width,
                        image_url,
                        title,
                    )
                )

            if candidates:

                candidates.sort(
                    key=lambda item: (
                        item[0],
                        item[1],
                    ),
                    reverse=True,
                )

                selected = candidates[0]

                print(
                    f"City background selected for "
                    f"{city_clean}: {selected[3]}"
                )

                return selected[2]

        except Exception as error:

            print(
                "City background API search error:",
                error,
            )

    print(
        f"No city-specific photograph found for {city_clean}."
    )

    return None


def load_city_background(city):
    """Download the searched city's photograph as a Base64 image."""

    image_url = get_city_image(city)

    if not image_url:
        return None

    return download_background_image(
        image_url
    )


def load_city_background(city):
    """Download a city photograph and return a Base64 data URL."""

    image_url = get_city_image(city)

    if not image_url:
        print(
            f"No city background found for {city}."
        )
        return None

    return download_background_image(
        image_url
    )


# ============================================================
# ============================================================
# API BACKGROUND IMAGE - WIKIMEDIA COMMONS
# ============================================================

def get_background_image_url():
    """Find a real landscape photograph through the Wikimedia Commons API."""

    url = "https://commons.wikimedia.org/w/api.php"

    # Search specifically for photographs/landscapes and avoid artwork.
    search_terms = [
        'landscape clouds photograph filetype:bitmap',
        'sky clouds landscape photograph filetype:bitmap',
        'mountains clouds photograph filetype:bitmap',
        'nature sky photograph filetype:bitmap',
    ]

    blocked_words = [
        "map", "diagram", "logo", "icon", "chart", "symbol",
        "station", "screenshot", "flag", "coat of arms",
        "poster", "painting", "illustration", "drawing", "art",
        "portrait", "collage", "graphic", "render", "sculpture",
        "frame", "museum", "canvas",
    ]

    headers = {
        "User-Agent": (
            "WeatherMate/1.0 "
            "(student weather information project)"
        )
    }

    for search_text in search_terms:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": search_text,
            "gsrnamespace": 6,
            "gsrlimit": 50,
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1920,
            "format": "json",
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=15,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})

            # Prefer wide, high-resolution images so the background looks
            # like a real full-screen photograph instead of a framed artwork.
            candidates = []

            for page in pages.values():
                title = page.get("title", "").lower()

                if any(word in title for word in blocked_words):
                    continue

                image_info = page.get("imageinfo", [])
                if not image_info:
                    continue

                info = image_info[0]
                mime = info.get("mime", "").lower()

                if mime not in {
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                }:
                    continue

                width = int(info.get("width") or 0)
                height = int(info.get("height") or 0)

                if width < 1200 or height < 600:
                    continue

                if height == 0:
                    continue

                aspect_ratio = width / height

                # Full-screen desktop backgrounds should be reasonably wide.
                if aspect_ratio < 1.35:
                    continue

                image_url = info.get("thumburl") or info.get("url")
                if not image_url:
                    continue

                candidates.append((aspect_ratio, width, image_url))

            if candidates:
                candidates.sort(
                    key=lambda item: (
                        item[0],
                        item[1],
                    ),
                    reverse=True,
                )
                selected = candidates[0][2]
                print("Real landscape background selected.")
                return selected

        except Exception as error:
            print("Background API search error:", error)

    return None

def download_background_image(image_url):
    """Download the API image and convert it to a Flet-compatible Base64 URL."""

    if not image_url:
        return None

    try:
        response = requests.get(
            image_url,
            timeout=25,
            headers={
                "User-Agent": (
                    "WeatherMate/1.0 "
                    "(student weather information project)"
                )
            },
        )
        response.raise_for_status()

        content_type = (
            response.headers.get("Content-Type", "")
            .split(";")[0]
            .strip()
            .lower()
        )

        if content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            print("Background API returned unsupported type:", content_type)
            return None

        if not response.content:
            print("Background API returned an empty image.")
            return None

        image_data = base64.b64encode(response.content).decode("ascii")
        return f"data:{content_type};base64,{image_data}"

    except Exception as error:
        print("Background download error:", error)
        return None


def load_api_background():
    """Load one background image once when WeatherMate starts."""

    print("Loading WeatherMate background image from API...")

    image_url = get_background_image_url()
    if not image_url:
        print("No suitable background image URL received.")
        return None

    image_base64 = download_background_image(image_url)

    if image_base64:
        print("Background image downloaded successfully.")
    else:
        print("Background image download failed.")

    return image_base64



# ============================================================
# CITY VALIDATION
# ============================================================

COMMON_CITIES = [
    "Mumbai", "Pune", "Sangli", "Kolhapur", "Satara",
    "Nashik", "Nagpur", "Aurangabad", "Chhatrapati Sambhajinagar",
    "Solapur", "Thane", "Navi Mumbai", "Amravati", "Akola",
    "Latur", "Nanded", "Jalgaon", "Dhule", "Ahmednagar",
    "Sangamner", "Karad", "Delhi", "New Delhi", "Bengaluru",
    "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad",
    "Surat", "Jaipur", "Lucknow", "Kanpur", "Indore", "Bhopal",
    "Patna", "Chandigarh", "Noida", "Gurugram", "Gurgaon",
    "Mysore", "Mysuru", "Visakhapatnam", "Vijayawada",
    "Bhubaneswar", "Ranchi", "Raipur", "Dehradun", "Goa",
    "Panaji", "London", "New York", "Los Angeles", "Chicago",
    "Toronto", "Dubai", "Singapore", "Sydney", "Melbourne",
    "Paris", "Berlin", "Tokyo", "Bangkok", "Kuala Lumpur",
]


def find_city_typo(city):
    """Return the likely correct common city name for a typo."""
    normalized = " ".join(city.lower().split())

    choices = {
        " ".join(name.lower().split()): name
        for name in COMMON_CITIES
    }

    match = difflib.get_close_matches(
        normalized,
        choices.keys(),
        n=1,
        cutoff=0.78,
    )

    if not match:
        return None

    if match[0] == normalized:
        return None

    return choices[match[0]]


def validate_city_input(city):
    """
    Validate the user's text before sending it to the API.

    Returns:
        (True, "") for valid input
        (False, message) for invalid/typo input
    """
    city = city.strip()

    if not city:
        return False, "Please enter a city name."

    if len(city) < 3:
        return False, "City name is too short."

    if len(city) > 100:
        return False, "City name is too long."

    # Allow letters, spaces, apostrophes and hyphens.
    for character in city:
        if not (
            character.isalpha()
            or character.isspace()
            or character in "'-"
        ):
            return False, (
                "Please enter a valid city name "
                "using letters only."
            )

    typo = find_city_typo(city)

    if typo:
        return False, (
            f"Did you mean {typo}? "
            f"Please enter the correct city name."
        )

    return True, ""


# ============================================================
# WEATHERMATE BACKEND - CURRENT WEATHER
# ============================================================

BACKEND_URL = os.getenv(
    "WEATHER_BACKEND_URL",
    "http://127.0.0.1:8000"
)


def get_weather(city):

    try:
        response = requests.get(
            f"{BACKEND_URL}/weather",
            params={"city": city},
            timeout=15,
        )

        if response.status_code != 200:
            print("Backend weather error:", response.text)
            return None

        return response.json()

    except requests.RequestException as error:
        print("Backend weather connection error:", error)
        return None


# ============================================================
# WEATHERMATE BACKEND - 5 DAY FORECAST
# ============================================================

def get_forecast(city):

    try:
        response = requests.get(
            f"{BACKEND_URL}/forecast",
            params={"city": city},
            timeout=15,
        )

        if response.status_code != 200:
            print("Backend forecast error:", response.text)
            return None

        return response.json()

    except requests.RequestException as error:
        print("Backend forecast connection error:", error)
        return None


# ============================================================
# OPEN-METEO - HOURLY FORECAST
# ============================================================

def get_hourly_forecast(latitude, longitude):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "weather_code,"
            "is_day"
        ),
        "forecast_days": 2,
        "timezone": "auto",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        return None

    return response.json()


# ============================================================
# WEATHER ICON
# ============================================================

def get_weather_icon(condition, icon_code="01d"):
    """Return a current-weather icon using OpenWeather's day/night code."""

    condition = condition.lower()
    is_night = str(icon_code).lower().endswith("n")

    if "thunder" in condition:
        return (ft.Icons.THUNDERSTORM, "#B39DDB")

    if "rain" in condition or "drizzle" in condition:
        return (ft.Icons.WATER_DROP, "#64B5F6")

    if "snow" in condition:
        return (ft.Icons.AC_UNIT, "#A9D8F5")

    if "clear" in condition:
        if is_night:
            return (ft.Icons.NIGHTS_STAY, WHITE)
        return (ft.Icons.WB_SUNNY, YELLOW)

    if "cloud" in condition:
        return (ft.Icons.CLOUD, "#D7DEE8")

    if any(word in condition for word in ["mist", "fog", "haze", "smoke"]):
        return (ft.Icons.CLOUD, "#AEB8C4")

    return (ft.Icons.PUBLIC, BLUE)


# ============================================================
# OPEN-METEO ICON
# ============================================================

def get_hourly_icon(code, is_day=True):

    if code == 0:

        if is_day:
            return (
                ft.Icons.WB_SUNNY,
                YELLOW
            )

        return (
            ft.Icons.NIGHTS_STAY,
            WHITE
        )

    if code in [
        1,
        2,
        3,
        45,
        48
    ]:

        return (
            ft.Icons.CLOUD,
            "#D7DEE8"
        )

    if code in [
        51,
        53,
        55,
        56,
        57,
        61,
        63,
        65,
        66,
        67,
        80,
        81,
        82
    ]:

        return (
            ft.Icons.WATER_DROP,
            "#64B5F6"
        )

    if code in [
        71,
        73,
        75,
        77,
        85,
        86
    ]:

        return (
            ft.Icons.AC_UNIT,
            "#A9D8F5"
        )

    if code in [
        95,
        96,
        99
    ]:

        return (
            ft.Icons.THUNDERSTORM,
            "#B39DDB"
        )

    return (
        ft.Icons.PUBLIC,
        BLUE
    )


# ============================================================
# FORMAT HOUR
# ============================================================

def format_hour(value):

    try:

        dt = datetime.fromisoformat(value)

        return dt.strftime("%I %p")

    except Exception:

        return value


# ============================================================
# FORMAT DATE
# ============================================================

def format_date(value):

    try:

        dt = datetime.fromisoformat(value)

        return dt.strftime("%a, %d %b")

    except Exception:

        return value


# ============================================================
# SUNRISE / SUNSET
# ============================================================

def format_sun_time(timestamp, timezone_offset):

    try:

        if timestamp is None:

            return "--:--"

        city_timezone = timezone(
            timedelta(
                seconds=timezone_offset
            )
        )

        result = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).astimezone(
            city_timezone
        )

        return result.strftime(
            "%I:%M %p"
        )

    except Exception:

        return "--:--"


# ============================================================
# CURRENT CITY DATE / TIME
# ============================================================
def format_city_datetime(timestamp, timezone_offset):

    try:

        if timestamp is None:

            return "--"

        city_timezone = timezone(
            timedelta(
                seconds=timezone_offset
            )
        )

        result = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).astimezone(
            city_timezone
        )

        date_value = result.strftime("%A, %d %B %Y")
        time_value = result.strftime("%I:%M %p")

        return date_value, time_value

    except Exception:

        return "--", "--"


# ============================================================
# MAIN APPLICATION
# ============================================================

def main(page: ft.Page):

    # ========================================================
    # PAGE SETTINGS
    # ========================================================

    page.title = "WeatherMate"

    page.bgcolor = BG

    page.padding = 0

    page.spacing = 0

    page.theme_mode = ft.ThemeMode.DARK

    try:

        page.window.maximized = True
        page.window.resizable = True

    except Exception:

        pass


    # ========================================================
    # ONE API BACKGROUND FOR HOME + CITY SCREEN
    # ========================================================

    background_base64 = load_api_background()

    # Wrap the image in an expanding Container so the background
    # always occupies the complete Stack area.
    background_image = ft.Image(
        src=(
            background_base64
            or ""
        ),
        width=page.width or 1366,
        height=page.height or 700,
        fit=ft.BoxFit.COVER,
        visible=bool(background_base64),
    )

    background_layer = ft.Container(
        expand=True,
        bgcolor="#07111B",
        alignment=ft.Alignment.CENTER,
        content=background_image,
    )

    def resize_background(e=None):
        background_image.width = page.width or 1366
        background_image.height = page.height or 700
        page.update()

    page.on_resize = resize_background

    background_overlay = ft.Container(
        expand=True,
        bgcolor="#2007111B",
    )


    # ========================================================
    # VARIABLES
    # ========================================================

    current_city = ""

    current_hourly = None

    recent_cities = []


    # ========================================================
    # HEADER
    # ========================================================

    logo = ft.Icon(
        ft.Icons.WB_SUNNY,
        size=44,
        color=YELLOW,
    )

    title = ft.Text(
        "WeatherMate",
        size=30,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    subtitle = ft.Text(
        "Your personal weather information system",
        size=13,
        color=GREY,
    )

    header = ft.Row(
        [
            logo,
            ft.Column(
                [
                    title,
                    subtitle,
                ],
                spacing=1,
            ),
        ],
        spacing=10,
    )


    # ========================================================
    # SEARCH FIELD
    # ========================================================

    search_field = ft.TextField(
        hint_text="Enter city name",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        border_radius=14,
        bgcolor=CARD,
        border_color="#607D8B",
        focused_border_color=BLUE,
        color=WHITE,
        hint_style=ft.TextStyle(
            color="#90A4AE"
        ),
    )

    status_text = ft.Text(
        "",
        size=13,
        color=GREY,
    )


    # ========================================================
    # CITY IMAGE
    # ========================================================
    # No separate city image is used.
    # The same API background remains behind the city screen.


    # ========================================================
    # CURRENT WEATHER
    # ========================================================

    city_text = ft.Text(
        "Search for a city",
        size=32,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    current_date_text = ft.Text(
        "",
        size=14,
        color=GREY,
        text_align=ft.TextAlign.CENTER,
        visible=False,
    )

    current_time_text = ft.Text(
        "",
        size=15,
        weight=ft.FontWeight.BOLD,
        color=LIGHT_BLUE,
        text_align=ft.TextAlign.CENTER,
        visible=False,
    )

    temperature_text = ft.Text(
        "--°C",
        size=58,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    condition_text = ft.Text(
        "Weather information will appear here",
        size=17,
        color=WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    main_weather_icon = ft.Icon(
        ft.Icons.PUBLIC,
        size=58,
        color=BLUE,
    )


    current_weather_area = ft.Container(
        content=ft.Column(
            [
                city_text,

                current_date_text,

                current_time_text,

                temperature_text,

                condition_text,

                main_weather_icon,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        ),

        bgcolor=CARD,

        border_radius=24,

        padding=12,
    )


    # ========================================================
    # DETAIL VALUES
    # ========================================================

    feels_like_text = ft.Text(
        "--°C",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    humidity_text = ft.Text(
        "--%",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    wind_text = ft.Text(
        "-- m/s",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    visibility_text = ft.Text(
        "-- km",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    pressure_text = ft.Text(
        "-- hPa",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    sunrise_text = ft.Text(
        "--:--",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    sunset_text = ft.Text(
        "--:--",
        size=17,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )


    # ========================================================
    # DETAIL CARD
    # ========================================================

    def detail_card(icon, label, value):

        if isinstance(icon, tuple):
            icon_widget = ft.Image(
                src=(
                    "data:image/svg+xml;base64,"
                    + weather_detail_logo(icon[0])
                ),
                width=34,
                height=34,
                fit=ft.BoxFit.CONTAIN,
            )
        else:
            icon_widget = ft.Icon(
                icon,
                color=LIGHT_BLUE,
                size=27,
            )

        return ft.Container(

            content=ft.Column(
                [
                    icon_widget,

                    ft.Text(
                        label,
                        size=11,
                        color=GREY,
                    ),

                    value,
                ],

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                spacing=3,
            ),

            bgcolor=CARD,

            border=ft.Border.all(
                1,
                BLUE,
            ),

            border_radius=14,

            padding=10,

            width=140,
        )


    # ========================================================
    # DETAILS ROW
    # ========================================================

    details_row = ft.Row(

        [
            # Sunrise is always the FIRST detail card.
            detail_card(
                ("sunrise",),
                "Sunrise",
                sunrise_text,
            ),

            detail_card(
                ft.Icons.THERMOSTAT,
                "Feels Like",
                feels_like_text,
            ),

            detail_card(
                ft.Icons.WATER_DROP,
                "Humidity",
                humidity_text,
            ),

            detail_card(
                ft.Icons.AIR,
                "Wind",
                wind_text,
            ),

            detail_card(
                ft.Icons.VISIBILITY,
                "Visibility",
                visibility_text,
            ),

            detail_card(
                ft.Icons.SPEED,
                "Pressure",
                pressure_text,
            ),

            # Sunset is always the LAST detail card.
            detail_card(
                ("sunset",),
                "Sunset",
                sunset_text,
            ),
        ],

        spacing=10,

        scroll=ft.ScrollMode.AUTO,
    )


    # ========================================================
    # HOURLY FORECAST
    # ========================================================

    hourly_title = ft.Text(
        "⏰ Hourly Forecast",
        size=22,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    hourly_row = ft.Row(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )


    # ========================================================
    # 5 DAY FORECAST
    # ========================================================

    forecast_title = ft.Text(
        "📅 5-Day Forecast",
        size=22,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    forecast_row = ft.Row(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )


    # ========================================================
    # RECENT SEARCHES
    # ========================================================

    recent_title = ft.Text(
        "🕘 Recent Searches",
        size=22,
        weight=ft.FontWeight.BOLD,
        color=WHITE,
    )

    recent_column = ft.Column(
        spacing=6,
    )


    # ========================================================
    # SECTION BOX
    # ========================================================

    def section_box(content):

        return ft.Container(

            content=content,

            bgcolor="#B3091827",

            border=ft.Border.all(
                1,
                BLUE,
            ),

            border_radius=16,

            padding=10,
        )


    # ========================================================
    # REFRESH RECENT SEARCHES
    # ========================================================

    def refresh_recent():

        recent_column.controls.clear()

        try:

            if hasattr(
                database,
                "get_recent_searches"
            ):

                recent = database.get_recent_searches()

            else:

                recent = recent_cities

        except Exception as error:

            print(
                "Recent search error:",
                error
            )

            recent = recent_cities


        if not recent:

            recent_column.controls.append(

                ft.Text(
                    "No recent searches.",
                    color=GREY,
                )

            )

        else:

            for city in recent:

                def select_recent(
                    e,
                    selected_city=city
                ):

                    search_field.value = selected_city

                    search_weather(
                        selected_city
                    )


                recent_column.controls.append(

                    ft.Container(

                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.HISTORY,
                                    color=LIGHT_BLUE,
                                ),

                                ft.Text(
                                    city,
                                    color=WHITE,
                                    expand=True,
                                ),

                                ft.IconButton(
                                    icon=ft.Icons.SEARCH,
                                    icon_color=LIGHT_BLUE,
                                    on_click=select_recent,
                                ),
                            ]
                        ),

                        bgcolor=CARD,

                        border_radius=9,

                        padding=6,
                    )
                )


        page.update()


    # ========================================================
    # DISPLAY HOURLY FORECAST
    # ========================================================

    def display_hourly(
        data,
        sunrise_timestamp=None,
        sunset_timestamp=None,
        timezone_offset=0,
    ):

        hourly_row.controls.clear()

        if not data:

            hourly_row.controls.append(

                ft.Text(
                    "Hourly forecast unavailable.",
                    color=GREY,
                )

            )

            page.update()

            return


        hourly = data.get(
            "hourly",
            {}
        )

        times = hourly.get(
            "time",
            []
        )

        temperatures = hourly.get(
            "temperature_2m",
            []
        )

        humidity = hourly.get(
            "relative_humidity_2m",
            []
        )

        wind = hourly.get(
            "wind_speed_10m",
            []
        )

        codes = hourly.get(
            "weather_code",
            []
        )

        hourly_is_day = hourly.get(
            "is_day",
            []
        )


        if not times:

            hourly_row.controls.append(

                ft.Text(
                    "Hourly forecast unavailable.",
                    color=GREY,
                )

            )

            page.update()

            return


        # Use the searched city's local time.
        city_now = datetime.now(
            timezone.utc
        ) + timedelta(
            seconds=timezone_offset
        )

        city_now = city_now.replace(
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=None,
        )

        start_index = 0

        for index, time_text in enumerate(times):

            try:

                forecast_time = datetime.fromisoformat(
                    time_text
                )

                if forecast_time >= city_now:

                    start_index = index

                    break

            except Exception:

                continue


        # Exactly the next 8 hourly forecast cards.
        end_index = min(
            start_index + 8,
            len(times)
        )


        # Convert today's sunrise/sunset to the searched city's local time.
        sunrise_local = None
        sunset_local = None

        try:

            if sunrise_timestamp is not None:

                sunrise_local = datetime.fromtimestamp(
                    sunrise_timestamp,
                    tz=timezone.utc,
                ) + timedelta(
                    seconds=timezone_offset
                )

                sunrise_local = sunrise_local.replace(
                    tzinfo=None
                )

            if sunset_timestamp is not None:

                sunset_local = datetime.fromtimestamp(
                    sunset_timestamp,
                    tz=timezone.utc,
                ) + timedelta(
                    seconds=timezone_offset
                )

                sunset_local = sunset_local.replace(
                    tzinfo=None
                )

        except Exception:

            sunrise_local = None
            sunset_local = None


        for i in range(
            start_index,
            end_index
        ):

            try:

                forecast_time = datetime.fromisoformat(
                    times[i]
                )

            except Exception:

                continue


            code = (
                codes[i]
                if i < len(codes)
                else 0
            )


            # Base value from Open-Meteo.
            is_day = (
                bool(hourly_is_day[i])
                if i < len(hourly_is_day)
                else False
            )


            # IMPORTANT:
            # Clear Sky can show the sun ONLY between sunrise and sunset.
            # After sunset it must show the white moon.
            if sunrise_local is not None and sunset_local is not None:

                if forecast_time.date() == sunset_local.date():

                    is_day = (
                        sunrise_local
                        <= forecast_time
                        < sunset_local
                    )

                elif forecast_time.date() > sunset_local.date():

                    # The next hours after midnight are still nighttime
                    # until the next sunrise.
                    is_day = False


            icon, icon_color = get_hourly_icon(
                code,
                is_day
            )


            temp = (
                temperatures[i]
                if i < len(temperatures)
                else 0
            )

            hum = (
                humidity[i]
                if i < len(humidity)
                else 0
            )

            wind_speed = (
                wind[i]
                if i < len(wind)
                else 0
            )


            card = ft.Container(

                content=ft.Column(
                    [
                        ft.Text(
                            format_hour(
                                times[i]
                            ),
                            color=GREY,
                            size=12,
                        ),

                        ft.Icon(
                            icon,
                            color=icon_color,
                            size=30,
                        ),

                        ft.Text(
                            f"{temp:.1f}°C",
                            color=WHITE,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),

                        ft.Text(
                            f"💧 {hum}%",
                            color=LIGHT_BLUE,
                            size=11,
                        ),

                        ft.Text(
                            f"💨 {wind_speed:.1f} m/s",
                            color=GREY,
                            size=10,
                        ),
                    ],

                    horizontal_alignment=(
                        ft.CrossAxisAlignment.CENTER
                    ),

                    spacing=4,
                ),

                bgcolor=CARD,

                border=ft.Border.all(
                    1,
                    BLUE,
                ),

                border_radius=12,

                padding=9,

                width=120,
            )

            hourly_row.controls.append(card)


        page.update()


    # ========================================================
    # DISPLAY 5 DAY FORECAST
    # ========================================================

    def display_forecast(data):

        forecast_row.controls.clear()

        if not data:

            forecast_row.controls.append(

                ft.Text(
                    "5-day forecast unavailable.",
                    color=GREY,
                )

            )

            page.update()

            return


        items = data.get(
            "list",
            []
        )

        daily_data = {}


        for item in items:

            date_value = item[
                "dt_txt"
            ].split(" ")[0]

            if date_value not in daily_data:

                daily_data[
                    date_value
                ] = item


        days = list(
            daily_data.values()
        )[:5]


        for item in days:

            weather = item[
                "weather"
            ][0]

            description = weather.get(
                "description",
                ""
            )

            icon_code = weather.get(
                "icon",
                "01d"
            )


            if icon_code.startswith("01"):

                icon = ft.Icons.WB_SUNNY
                icon_color = YELLOW

            elif icon_code.startswith("02"):

                icon = ft.Icons.CLOUD
                icon_color = "#D7DEE8"

            elif icon_code.startswith("03"):

                icon = ft.Icons.CLOUD
                icon_color = "#B0BEC5"

            elif icon_code.startswith("04"):

                icon = ft.Icons.CLOUD
                icon_color = "#90A4AE"

            elif icon_code.startswith("09"):

                icon = ft.Icons.WATER_DROP
                icon_color = "#64B5F6"

            elif icon_code.startswith("10"):

                icon = ft.Icons.WATER_DROP
                icon_color = "#64B5F6"

            elif icon_code.startswith("11"):

                icon = ft.Icons.THUNDERSTORM
                icon_color = "#B39DDB"

            elif icon_code.startswith("13"):

                icon = ft.Icons.AC_UNIT
                icon_color = "#A9D8F5"

            else:

                icon = ft.Icons.CLOUD
                icon_color = WHITE


            temperature = item[
                "main"
            ]["temp"]


            card = ft.Container(

                content=ft.Column(
                    [
                        ft.Text(
                            format_date(
                                item["dt_txt"]
                            ),
                            color=GREY,
                            size=12,
                        ),

                        ft.Icon(
                            icon,
                            size=38,
                            color=icon_color,
                        ),

                        ft.Text(
                            f"{temperature:.1f}°C",
                            size=19,
                            weight=ft.FontWeight.BOLD,
                            color=WHITE,
                        ),

                        ft.Text(
                            description.title(),
                            color=GREY,
                            size=11,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],

                    horizontal_alignment=(
                        ft.CrossAxisAlignment.CENTER
                    ),

                    spacing=5,
                ),

                width=150,

                bgcolor=CARD,

                border=ft.Border.all(
                    1,
                    BLUE,
                ),

                border_radius=13,

                padding=10,
            )

            forecast_row.controls.append(card)


        page.update()


    # ========================================================
    # SEARCH WEATHER
    # ========================================================

    def search_weather(city=None):

        nonlocal current_city
        nonlocal current_hourly

        # ----------------------------------------------------
        # GET CITY NAME
        # ----------------------------------------------------

        if city is None:

            city = search_field.value.strip()

        else:

            city = city.strip()


        # ----------------------------------------------------
        # EMPTY INPUT CHECK
        # ----------------------------------------------------

        if not city:

            status_text.value = (
                "Please enter a city name."
            )

            status_text.color = RED

            page.update()

            return


        # ----------------------------------------------------
        # CITY VALIDATION
        # ----------------------------------------------------

        valid_city, validation_message = (
            validate_city_input(city)
        )

        if not valid_city:

            status_text.value = validation_message
            status_text.color = RED

            page.update()

            return


        # ----------------------------------------------------
        # SEARCH MESSAGE
        # ----------------------------------------------------

        status_text.value = (
            f"Searching weather for {city}..."
        )

        status_text.color = GREY

        page.update()


        try:

            # ------------------------------------------------
            # CURRENT WEATHER
            # ------------------------------------------------

            weather = get_weather(city)


            if not weather:

                status_text.value = (
                    "City not found. Please check the city name."
                )

                status_text.color = RED

                page.update()

                return


            # ------------------------------------------------
            # API RESULT VALIDATION
            # ------------------------------------------------

            api_city_name = weather.get(
                "name",
                city,
            )

            normalized_input = (
                " ".join(city.lower().split())
            )

            normalized_api_city = (
                " ".join(api_city_name.lower().split())
            )

            if normalized_input != normalized_api_city:

                suggested_city = find_city_typo(city)

                if suggested_city:
                    status_text.value = (
                        f"Invalid city spelling. "
                        f"Did you mean {suggested_city}?"
                    )
                else:
                    status_text.value = (
                        f"Please check the city name. "
                        f"Weather API matched '{api_city_name}'."
                    )

                status_text.color = RED

                page.update()

                return


            # ------------------------------------------------
            # CURRENT CITY
            # ------------------------------------------------

            current_city = weather[
                "name"
            ]

            search_field.value = current_city


            # ------------------------------------------------
            # CITY-SPECIFIC BACKGROUND
            # ------------------------------------------------
            # After a successful search, replace the generic Home
            # background with a real photograph of the searched city.
            city_background_base64 = (
                load_city_background(
                    current_city
                )
            )

            if city_background_base64:

                # Replace the currently displayed image.
                background_image.src = (
                    city_background_base64
                )

                background_image.visible = True

                print(
                    "Applied city-specific background:",
                    current_city,
                )

            else:

                # Keep the general background only when
                # Wikimedia has no suitable city photograph.
                background_image.src = (
                    background_base64
                    or ""
                )

                background_image.visible = bool(
                    background_base64
                )

                print(
                    "Using general background for:",
                    current_city,
                )

            page.update()

            # ------------------------------------------------
            # MAIN WEATHER DATA
            # ------------------------------------------------

            main_data = weather[
                "main"
            ]

            temperature = main_data[
                "temp"
            ]

            feels_like = main_data[
                "feels_like"
            ]

            humidity = main_data[
                "humidity"
            ]

            pressure = main_data[
                "pressure"
            ]


            # ------------------------------------------------
            # WIND
            # ------------------------------------------------

            wind_speed = weather.get(
                "wind",
                {}
            ).get(
                "speed",
                0
            )


            # ------------------------------------------------
            # VISIBILITY
            # ------------------------------------------------

            visibility = (
                weather.get(
                    "visibility",
                    0
                ) / 1000
            )


            # ------------------------------------------------
            # WEATHER CONDITION
            # ------------------------------------------------

            weather_info = weather[
                "weather"
            ][0]

            description = weather_info[
                "description"
            ]


            # ------------------------------------------------
            # CURRENT WEATHER DISPLAY
            # ------------------------------------------------

            city_text.value = current_city

            # Show the searched city's local date and current time
            # directly below the city name. OpenWeather provides the
            # current UTC timestamp and the city's timezone offset.
            city_date, city_time = format_city_datetime(
                weather.get("dt"),
                weather.get("timezone", 0),
            )

            current_date_text.value = city_date
            current_time_text.value = city_time
            current_date_text.visible = True
            current_time_text.visible = True

            temperature_text.value = (
                f"{temperature:.1f}°C"
            )

            condition_text.value = (
                description.title()
            )


            icon_code = weather_info.get(
                "icon",
                "01d"
            )

            icon, icon_color = get_weather_icon(
                description,
                icon_code
            )

            main_weather_icon.icon = icon

            main_weather_icon.color = icon_color


            # ------------------------------------------------
            # DETAILS
            # ------------------------------------------------

            feels_like_text.value = (
                f"{feels_like:.1f}°C"
            )

            humidity_text.value = (
                f"{humidity}%"
            )

            wind_text.value = (
                f"{wind_speed:.1f} m/s"
            )

            visibility_text.value = (
                f"{visibility:.1f} km"
            )

            pressure_text.value = (
                f"{pressure} hPa"
            )


            # ------------------------------------------------
            # SUNRISE / SUNSET
            # ------------------------------------------------

            timezone_offset = weather.get(
                "timezone",
                0
            )


            sunrise_text.value = format_sun_time(
                weather.get(
                    "sys",
                    {}
                ).get(
                    "sunrise"
                ),
                timezone_offset
            )


            sunset_text.value = format_sun_time(
                weather.get(
                    "sys",
                    {}
                ).get(
                    "sunset"
                ),
                timezone_offset
            )


            # ------------------------------------------------
            # SAVE WEATHER TO MYSQL
            # ------------------------------------------------

            try:

                database.save_weather(
                    current_city,
                    temperature,
                    humidity,
                    wind_speed,
                    description,
                )

            except Exception as error:

                print(
                    "Weather database error:",
                    error
                )


            # ------------------------------------------------
            # SAVE RECENT SEARCH
            # ------------------------------------------------

            try:

                if hasattr(
                    database,
                    "save_recent_search"
                ):

                    database.save_recent_search(
                        current_city
                    )

            except Exception as error:

                print(
                    "Recent search database error:",
                    error
                )


            # ------------------------------------------------
            # UPDATE RECENT CITY LIST
            # ------------------------------------------------

            recent_cities[:] = [
                item
                for item in recent_cities
                if item.lower()
                != current_city.lower()
            ]


            recent_cities.insert(
                0,
                current_city
            )

            del recent_cities[5:]


            # ------------------------------------------------
            # 5 DAY FORECAST
            # ------------------------------------------------

            forecast = get_forecast(
                current_city
            )

            display_forecast(
                forecast
            )


            # ------------------------------------------------
            # HOURLY FORECAST
            # ------------------------------------------------

            latitude = weather[
                "coord"
            ]["lat"]

            longitude = weather[
                "coord"
            ]["lon"]


            current_hourly = get_hourly_forecast(
                latitude,
                longitude
            )


            display_hourly(
                current_hourly,
                weather.get(
                    "sys",
                    {}
                ).get(
                    "sunrise"
                ),
                weather.get(
                    "sys",
                    {}
                ).get(
                    "sunset"
                ),
                weather.get(
                    "timezone",
                    0
                ),
            )


            # ------------------------------------------------
            # REFRESH RECENT SEARCHES
            # ------------------------------------------------

            refresh_recent()


            # ------------------------------------------------
            # SUCCESS MESSAGE
            # ------------------------------------------------

            status_text.value = (
                f"Weather updated for {current_city}"
            )

            status_text.color = GREEN

            page.update()


        except requests.exceptions.Timeout:

            status_text.value = (
                "Request timed out. Please try again."
            )

            status_text.color = RED

            page.update()


        except requests.exceptions.RequestException:

            status_text.value = (
                "Internet connection problem."
            )

            status_text.color = RED

            page.update()


        except Exception as error:

            print(
                "Weather error:",
                error
            )

            status_text.value = (
                "Something went wrong. Check terminal."
            )

            status_text.color = RED

            page.update()


    # ========================================================
    # SEARCH BUTTON
    # ========================================================

    def search_clicked(e):

        search_weather()


    search_button = ft.Button(
        "Search",
        icon=ft.Icons.SEARCH,
        on_click=search_clicked,
        style=ft.ButtonStyle(
            bgcolor=BLUE,
            color=WHITE,
        ),
    )


    # ========================================================
    # ENTER KEY
    # ========================================================

    def search_submit(e):

        search_weather()


    search_field.on_submit = search_submit


    # ========================================================
    # CLEAR
    # ========================================================

    def clear_weather(e=None):

        nonlocal current_city
        nonlocal current_hourly

        current_city = ""

        current_hourly = None

        search_field.value = ""

        # Return to the general Home background.
        background_image.src = (
            background_base64
            or ""
        )
        background_image.visible = bool(background_base64)

        city_text.value = (
            "Search for a city"
        )

        current_date_text.value = ""
        current_date_text.visible = False

        current_time_text.value = ""
        current_time_text.visible = False

        temperature_text.value = (
            "--°C"
        )

        condition_text.value = (
            "Weather information will appear here"
        )


        feels_like_text.value = "--°C"

        humidity_text.value = "--%"

        wind_text.value = "-- m/s"

        visibility_text.value = "-- km"

        pressure_text.value = "-- hPa"

        sunrise_text.value = "--:--"

        sunset_text.value = "--:--"


        main_weather_icon.icon = (
            ft.Icons.PUBLIC
        )

        main_weather_icon.color = BLUE


        hourly_row.controls.clear()

        forecast_row.controls.clear()


        status_text.value = ""

        page.update()


    clear_button = ft.Button(
        "Clear",
        icon=ft.Icons.CLEAR,
        on_click=clear_weather,
    )


    # ========================================================
    # SEARCH BAR
    # ========================================================

    search_bar = ft.Row(
        [
            search_field,
            search_button,
            clear_button,
        ],
        spacing=8,
    )


    # ========================================================
    # MAIN CONTENT
    # ========================================================

    content = ft.Column(

        [
            # Header

            header,

            # Small gap

            ft.Container(
                height=8
            ),

            # Search

            search_bar,

            # Status

            status_text,

            # Small gap

            ft.Container(
                height=6
            ),

            # Current Weather

            current_weather_area,

            # Details

            ft.Container(
                height=8
            ),

            section_box(
                details_row
            ),

            # Hourly title

            ft.Container(
                height=12
            ),

            hourly_title,

            # Hourly cards

            ft.Container(
                height=4
            ),

            section_box(
                hourly_row
            ),

            # Forecast title

            ft.Container(
                height=12
            ),

            forecast_title,

            # Forecast cards

            ft.Container(
                height=4
            ),

            section_box(
                forecast_row
            ),

            # Recent title

            ft.Container(
                height=12
            ),

            recent_title,

            # Recent searches

            ft.Container(
                height=4
            ),

            section_box(
                recent_column
            ),

            # Bottom

            ft.Container(
                height=15
            ),
        ],

        spacing=0,

        expand=True,

        scroll=ft.ScrollMode.AUTO,

        horizontal_alignment=(
            ft.CrossAxisAlignment.STRETCH
        ),
    )


    # ========================================================
    # FOREGROUND
    # ========================================================

    foreground = ft.Container(

        content=content,

        expand=True,

        padding=ft.Padding.symmetric(
            horizontal=24,
            vertical=14,
        ),
    )


    # ========================================================
    # PAGE STACK
    # ========================================================

    page.add(

        ft.Stack(

            expand=True,

            controls=[
                background_layer,
                background_overlay,
                foreground,
            ],
        )
    )


    # ========================================================
    # LOAD RECENT SEARCHES
    # ========================================================

    try:

        if hasattr(
            database,
            "get_recent_searches"
        ):

            recent_cities[:] = (
                database.get_recent_searches()
            )

    except Exception as error:

        print(
            "Could not load recent searches:",
            error
        )


    refresh_recent()


    # ========================================================
    # HOURLY AUTO REFRESH
    # ========================================================

    async def hourly_updater():

        nonlocal current_hourly

        while True:

            await asyncio.sleep(
                3600
            )

            if current_city:

                try:

                    weather = get_weather(
                        current_city
                    )

                    if weather:

                        latitude = weather[
                            "coord"
                        ]["lat"]

                        longitude = weather[
                            "coord"
                        ]["lon"]


                        current_hourly = (
                            get_hourly_forecast(
                                latitude,
                                longitude
                            )
                        )


                        display_hourly(
                            current_hourly
                        )

                        page.update()


                except Exception as error:

                    print(
                        "Hourly refresh error:",
                        error
                    )


    page.run_task(
        hourly_updater
    )


# ============================================================
# START APPLICATION
# ============================================================

ft.run(main)