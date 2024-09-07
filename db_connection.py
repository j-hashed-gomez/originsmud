import os
import mysql.connector
from mysql.connector import Error
import logging
import sys

# Configuración del log para que escriba en stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout  # Asegúrate de que los logs se envíen al stdout
)

def connect_to_database():
    try:
        # Leer las variables de entorno
        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        database = os.getenv('DB_NAME')

        # Verificar si las variables están configuradas
        if not all([host, port, user, password, database]):
            logging.error("Faltan una o más variables de entorno para la conexión.")
            return False

        # Conectar a la base de datos
        logging.info(f"Intentando conectar a la base de datos {database} en {host}:{port}...")
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

        if connection.is_connected():
            logging.info(f"Conexión a la base de datos {database} exitosa.")
            return connection

    except Error as e:
        logging.error(f"Error al conectar a la base de datos: {str(e)}")
        return False

    finally:
        # Cerrar conexión si se ha realizado correctamente
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            logging.info("Conexión cerrada.")
