import originsmud_server
import db_connection
import auth
import logging
import sys

# Configuración de logs centralizada para que todo salga por stdout
logging.basicConfig(
    level=logging.DEBUG,  # Nivel DEBUG para obtener todos los detalles
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Solo loggear en stdout
    ]
)

# Ignorar los logs de postfix (solo si es necesario)
logging.getLogger('postfix').setLevel(logging.ERROR)

if __name__ == "__main__":
    logging.info("Iniciando servidor OriginsMUD...")

    # Comprobar la conexión a la base de datos
    logging.debug("Intentando conectar a la base de datos...")
    connection = db_connection.connect_to_database()
    
    if connection:
        logging.info("Conexión a la base de datos establecida.")
    else:
        logging.error("Error al conectar a la base de datos. Verifica las configuraciones.")
        exit(1)  # Salir si no hay conexión a la base de datos

    # Iniciar el servidor y pasar la función de autenticación
    logging.info("Iniciando el servidor...")
    originsmud_server.start_server(auth.authenticate_user)
    logging.info("Servidor iniciado correctamente.")
