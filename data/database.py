import psycopg2

try:
    connection = psycopg2.connect(
        dbname="tweets_db",
        user="aaronrobinson",
        password="test",
        host="localhost",
        port="5432"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record, "\n")
    cursor.close()
    connection.close()
except Exception as error:
    print("Error while connecting to PostgreSQL", error)