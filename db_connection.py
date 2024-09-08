import mysql.connector
import logging
import os

# Función para conectarse a la base de datos usando variables de entorno
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )
        logging.info("Conexión a la base de datos exitosa.")
        return connection
    except mysql.connector.Error as e:
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None

# Función para ejecutar consultas a la base de datos
def dbquery(query, params=None, fetchone=False):
    connection = connect_to_database()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchone() if fetchone else cursor.fetchall()
        connection.commit()
        return result
    except mysql.connector.Error as e:
        logging.error(f"Error en la consulta a la base de datos: {e}")
        return None
    finally:
        cursor.close()
        connection.close()
        logging.info("Conexión a la base de datos cerrada correctamente.")
