import socket
import threading
import logging
from datetime import datetime

# Configuración del log para que escriba en stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Array para almacenar las conexiones
connections = []

# Función que maneja las conexiones entrantes, se mueve la autenticación fuera de este módulo
def handle_client(conn, addr, auth_callback):
    # Guardar la IP y la fecha/hora de conexión
    connection_data = {
        "ip": addr[0],          # IP del cliente
        "date": datetime.now()   # Fecha y hora de la conexión
    }
    connections.append(connection_data)
    logging.info(f"Nueva conexión desde {addr[0]} en {connection_data['date']}")

    # Llamar a la función de autenticación desde el main
    auth_callback(conn, addr)

    try:
        # Mantener la conexión abierta mientras el cliente está conectado
        while True:
            data = conn.recv(1024)
            if not data:
                break
            logging.info(f"Recibido de {addr[0]}: {data.decode('utf-8')}")
    except ConnectionResetError:
        logging.error(f"Conexión con {addr[0]} cerrada inesperadamente.")
    finally:
        conn.close()
        logging.info(f"Conexión con {addr[0]} cerrada.")

# Función para iniciar el servidor, llamada desde el archivo principal
def start_server(auth_callback):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5432))  # Escuchar en todas las interfaces
    server_socket.listen(5)  # Permitir hasta 5 conexiones pendientes
    logging.info("Servidor escuchando en el puerto 5432...")

    # Loop para aceptar múltiples conexiones
    while True:
        conn, addr = server_socket.accept()  # Aceptar nueva conexión
        client_thread = threading.Thread(target=handle_client, args=(conn, addr, auth_callback))
        client_thread.start()  # Hilo independiente para manejar cada cliente
