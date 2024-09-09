import socket
import threading
import logging
from datetime import datetime
import commands
import sys

# Configuración de logs centralizada para que todo salga por stdout
logging.basicConfig(
    level=logging.DEBUG,  # Nivel DEBUG para obtener todos los detalles
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

# Array para almacenar las conexiones
connections = []

# Función que maneja las conexiones entrantes
def handle_client(conn, addr, auth_callback):
    connection_data = {
        "ip": addr[0],          # IP del cliente
        "date": datetime.now()   # Fecha y hora de la conexión
    }
    connections.append(connection_data)
    logging.info(f"Nueva conexión desde {addr[0]} en {connection_data['date']}")

    # Llamar a la función de autenticación desde auth.py
    try:
        user_privileges = auth_callback(conn, addr)
        if not user_privileges:
            return  # Si no se autenticó, salir de la función
    except Exception as e:
        logging.error(f"Error durante la autenticación con {addr[0]}: {e}")
        return

    try:
        while True:
            if conn.fileno() == -1:
                logging.info(f"Conexión con {addr[0]} cerrada previamente.")
                break

            try:
                data = conn.recv(1024)
                if not data:
                    break

                try:
                    decoded_data = data.decode('utf-8').strip()
                    logging.info(f"Recibido de {addr[0]}: {decoded_data}")
                except UnicodeDecodeError as e:
                    logging.error(f"Error de decodificación de UTF-8 desde {addr[0]}: {e}")
                    conn.send("Error de formato en los datos recibidos.\n".encode('utf-8'))
                    continue

            except OSError as e:
                logging.error(f"Error en la conexión con {addr[0]}: {e}")
                break

            # Verificar si el comando es "quit"
            if decoded_data == "quit":
                commands.quit_command(conn, addr, connections)
                break

            # Verificar si el comando existe y si tiene permisos para ejecutarlo
            if decoded_data == "list_commands" or decoded_data == "comandos":
                commands.list_commands(conn, user_privileges)
            else:
                can_execute = commands.can_execute_command(decoded_data, user_privileges)

                if can_execute is None:
                    conn.send("Perdona, no entiendo lo que dices.\n".encode('utf-8'))
                elif can_execute:
                    # Mostrar el mensaje "Ejecutando comando" sólo para otros comandos
                    conn.send(f"Ejecutando comando: {decoded_data}\n".encode('utf-8'))
                else:
                    conn.send(f"No tienes los privilegios necesarios para ejecutar '{decoded_data}'.\n".encode('utf-8'))


    except OSError as e:
        logging.error(f"Error en la conexión con {addr[0]}: {e}")
    finally:
        if conn.fileno() != -1:
            try:
                conn.close()
                logging.info(f"Conexión con {addr[0]} cerrada.")
            except OSError as e:
                logging.error(f"Error al cerrar la conexión con {addr[0]}: {e}")
        if connection_data in connections:
            connections.remove(connection_data)

# Función para iniciar el servidor
def start_server(auth_callback):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5432))  # Escuchar en todas las interfaces
    server_socket.listen(5)  # Permitir hasta 5 conexiones pendientes
    logging.info("Servidor escuchando en el puerto 5432...")

    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr, auth_callback))
        client_thread.start()
