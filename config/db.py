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
            last_name VARCHAR(100) NULL,
            username VARCHAR(100) NULL,
            disciplane VARCHAR(255) NULL,
            user_group VARCHAR(100) NULL
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



def create_new_registered_user_table():
    try:
        connection = psycopg2.connect(user=env.str('USER'),
                                    password=env.str('PASSWORD'),
                                    host="127.0.0.1",
                                    port="5432",
                                    database=env.str('DATABASE'))
        cursor = connection.cursor()
        create_table_query = '''CREATE TABLE IF NOT EXISTS Register (
            ID SERIAL PRIMARY KEY,
            FIO VARCHAR(100) NOT NULL,
            username VARCHAR(100) NULL,
            discipline VARCHAR(255) NULL,
            user_group VARCHAR(100) NULL
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

            

def add_new_user(*data):
    try:
        connection = psycopg2.connect(user=env.str('USER'),
                                    password=env.str('PASSWORD'),
                                    host="127.0.0.1",
                                    port="5432",
                                    database=env.str('DATABASE'))
        cursor = connection.cursor()
        query = '''INSERT INTO Users(telegram_id, first_name, last_name, username, disciplane, user_group)
        VALUES(%s, %s, %s, %s, %s, %s);'''
        cursor.execute(query, data)
        connection.commit()
        print("User info add successfully in PostgreSQL ")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")