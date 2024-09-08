import mysql.connector
import logging

# Función para conectarse a la base de datos
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="your_db_host",
            user="your_db_user",
            password="your_db_password",
            database="your_db_name"
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
