import socket
import threading
from datetime import datetime
import logging
import sys

# Configuración del log para que escriba en stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout  # Asegúrate de que los logs se envíen al stdout
)

# Array para almacenar las conexiones
connections = []

# Función que maneja las conexiones entrantes
def handle_client(conn, addr):
    # Guardar la IP y la fecha/hora de conexión
    connection_data = {
        "ip": addr[0],          # IP del cliente
        "date": datetime.now()   # Fecha y hora de la conexión
    }
    connections.append(connection_data)
    logging.info(f"Nueva conexión desde {addr[0]} en {connection_data['date']}")

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

# Función para levantar el servidor
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5432))  # Escuchar en todas las interfaces
    server_socket.listen(5)  # Permitir hasta 5 conexiones pendientes
    logging.info("Servidor escuchando en el puerto 5432...")

    # Loop para aceptar múltiples conexiones
    while True:
        conn, addr = server_socket.accept()  # Aceptar nueva conexión
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()  # Hilo independiente para manejar cada cliente

if __name__ == "__main__":
    start_server()
