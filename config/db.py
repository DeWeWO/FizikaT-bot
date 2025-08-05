import psycopg2
from psycopg2 import Error
from environs import Env
env = Env()
env.read_env()

def create_users_table():
    try:
        connection = psycopg2.connect(user=env.str('USER'),
                                    password=env.str('PASSWORD'),
                                    host="127.0.0.1",
                                    port="5432",
                                    database=env.str('DATABASE'))
        cursor = connection.cursor()
        create_table_query = '''CREATE TABLE IF NOT EXISTS Users (
            ID SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100),
            username VARCHAR(100),
            disciplane VARCHAR(255),
            user_group VARCHAR(100)
            );'''
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully in PostgreSQL ")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")