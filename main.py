import requests
import os
from database import save_weather, get_weather_history, get_city_history, delete_weather_history, get_weather_statistics, get_temperature_records

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def show_weather():
    city = input("Enter city name: ").strip()

    # Check empty input
    if not city:
        print("❌ City name cannot be empty.")
        return

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            print("\n🌦️ Weather Information")
            print("------------------------")
            print("City:", data["name"])
            print("Temperature:", data["main"]["temp"], "°C")
            print("Humidity:", data["main"]["humidity"], "%")
            print("Wind Speed:", data["wind"]["speed"], "m/s")
            print("Condition:", data["weather"][0]["description"])

            save_weather(
                data["name"],
                data["main"]["temp"],
                data["main"]["humidity"],
                data["wind"]["speed"],
                data["weather"][0]["description"]
            )

        elif response.status_code == 404:
            print("❌ City not found. Please enter a valid city name.")

        else:
            print("❌ Weather API error. Please try again.")

    except requests.exceptions.Timeout:
        print("❌ Request timed out. Please check your internet connection.")

    except requests.exceptions.ConnectionError:
        print("❌ No internet connection. Please check your network.")

    except requests.exceptions.RequestException:
        print("❌ Something went wrong while connecting to the weather service.")



def show_history():
    records = get_weather_history()

    print("\n📋 Weather History")
    print("------------------------")

    if not records:
        print("No weather history found.")
        return

    for record in records:
        print("City:", record[0])
        print("Temperature:", record[1], "°C")
        print("Humidity:", record[2], "%")
        print("Wind Speed:", record[3], "m/s")
        print("Condition:", record[4])
        print("Searched At:", record[5])
        print("------------------------")

def search_city_history():
    city = input("Enter city name: ").strip()

    if not city:
        print("❌ City name cannot be empty.")
        return

    records = get_city_history(city)

    print(f"\n🔎 Weather History for {city}")
    print("------------------------")

    if not records:
        print("❌ No history found for this city.")
        return

    for record in records:
        print("City:", record[0])
        print("Temperature:", record[1], "°C")
        print("Humidity:", record[2], "%")
        print("Wind Speed:", record[3], "m/s")
        print("Condition:", record[4])
        print("Searched At:", record[5])
        print("------------------------")


def delete_history():
    record_id = input("Enter the ID of the record to delete: ").strip()

    if not record_id.isdigit():
        print("❌ Please enter a valid numeric ID.")
        return

    deleted_rows = delete_weather_history(int(record_id))

    if deleted_rows > 0:
        print("✅ Weather history deleted successfully!")
    else:
        print("❌ No record found with that ID.")


def show_forecast():
    city = input("Enter city name: ")

    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        print("\n📅 5-Day Weather Forecast")
        print("------------------------")

        for item in data["list"][::8]:
            date = item["dt_txt"]
            temperature = item["main"]["temp"]
            condition = item["weather"][0]["description"]

            print("Date:", date)
            print("Temperature:", temperature, "°C")
            print("Condition:", condition)
            print("------------------------")

    else:
        print("❌ City not found or API error.")


def show_statistics():
    result = get_weather_statistics()

    print("\n📊 Weather Statistics")
    print("------------------------")

    if result[3] == 0:
        print("No weather data available.")
        return

    average_temp = result[0]
    highest_temp = result[1]
    lowest_temp = result[2]
    total_searches = result[3]

    print("Average Temperature:", round(average_temp, 2), "°C")
    print("Highest Temperature:", highest_temp, "°C")
    print("Lowest Temperature:", lowest_temp, "°C")
    print("Total Searches:", total_searches)


def search_temperature_range():
    try:
        min_temp = float(input("Enter minimum temperature: "))
        max_temp = float(input("Enter maximum temperature: "))

        if min_temp > max_temp:
            print("❌ Minimum temperature cannot be greater than maximum temperature.")
            return

        records = get_temperature_records(min_temp, max_temp)

        print(f"\n🌡️ Weather Records from {min_temp}°C to {max_temp}°C")
        print("------------------------")

        if not records:
            print("❌ No records found.")
            return

        for record in records:
            print("City:", record[0])
            print("Temperature:", record[1], "°C")
            print("Humidity:", record[2], "%")
            print("Wind Speed:", record[3], "m/s")
            print("Condition:", record[4])
            print("Searched At:", record[5])
            print("------------------------")

    except ValueError:
        print("❌ Please enter valid numbers.")


while True:
    print("\n🌦️ Weather Information System")
    print("1. Check Current Weather")
    print("2. View Weather History")
    print("3. Search History by City")
    print("4. 5-Day Forecast")
    print("5. Delete Weather History")
    print("6. Weather Statistics")
    print("7. Search by Temperature Range")
    print("8. Exit")

    choice = input("Enter your choice: ").strip()

    if choice == "1":
        show_weather()

    elif choice == "2":
        show_history()

    elif choice == "3":
        search_city_history()

    elif choice == "4":
        show_forecast()

    elif choice == "5":
        delete_history()

    elif choice == "6":
         show_statistics()

    elif choice == "7":
        search_temperature_range()

    elif choice == "8":
        print("Thank you for using Weather Information System!")
        break

    else:
        print("❌ Invalid choice. Please enter 1, 2, 3, 4, 5, 6 or 7")
        