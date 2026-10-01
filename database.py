import os
import mysql.connector


def connect_database():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("MYSQL_PASSWORD"),
        database="weather_db",
        use_pure=True
    )

    return connection


def save_weather(city, temperature, humidity, wind_speed, condition):
    connection = connect_database()
    cursor = connection.cursor()

    query = """
    INSERT INTO weather_history
    (city, temperature, humidity, wind_speed, weather_condition)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (city, temperature, humidity, wind_speed, condition)

    cursor.execute(query, values)
    connection.commit()

    cursor.close()
    connection.close()

    print("Weather data saved to MySQL!")

def get_weather_history():
    connection = connect_database()
    cursor = connection.cursor()

    query = """
    SELECT city, temperature, humidity, wind_speed,
           weather_condition, searched_at
    FROM weather_history
    ORDER BY searched_at DESC
    """

    cursor.execute(query)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records

def get_city_history(city):
    connection = connect_database()
    cursor = connection.cursor()

    query = """
    SELECT city, temperature, humidity, wind_speed,
           weather_condition, searched_at
    FROM weather_history
    WHERE city = %s
    ORDER BY searched_at DESC
    """

    cursor.execute(query, (city,))

    records = cursor.fetchall()

    cursor.close()
    connection.close()
    return records

def delete_weather_history(record_id):
    connection = connect_database()
    cursor = connection.cursor()

    query = "DELETE FROM weather_history WHERE id = %s"

    cursor.execute(query, (record_id,))
    connection.commit()

    deleted_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return deleted_rows

def get_weather_statistics():
    connection = connect_database()
    cursor = connection.cursor()

    query = """
    SELECT
        AVG(temperature),
        MAX(temperature),
        MIN(temperature),
        COUNT(*)
    FROM weather_history
    """

    cursor.execute(query)

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result

def get_temperature_records(min_temp, max_temp):
    connection = connect_database()
    cursor = connection.cursor()

    query = """
    SELECT city, temperature, humidity, wind_speed,
           weather_condition, searched_at
    FROM weather_history
    WHERE temperature BETWEEN %s AND %s
    ORDER BY temperature DESC
    """

    cursor.execute(query, (min_temp, max_temp))
    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records

def save_recent_search(city):
    connection = connect_database()
    cursor = connection.cursor()

    # Remove the city if it already exists
    cursor.execute(
        "DELETE FROM recent_searches WHERE LOWER(city) = LOWER(%s)",
        (city,)
    )

    # Add it again so it becomes the newest search
    cursor.execute(
        "INSERT INTO recent_searches (city) VALUES (%s)",
        (city,)
    )

    # Keep only the latest 5 searches
    cursor.execute("""
        DELETE FROM recent_searches
        WHERE id NOT IN (
            SELECT id
            FROM (
                SELECT id
                FROM recent_searches
                ORDER BY searched_at DESC, id DESC
                LIMIT 5
            ) AS latest
        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


def get_recent_searches():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT city
        FROM recent_searches
        ORDER BY searched_at DESC, id DESC
        LIMIT 5
    """)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return [record[0] for record in records]