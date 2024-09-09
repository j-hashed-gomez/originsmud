import db_connection
import logging
import sys

# Configuración de logs centralizada para que todo salga por stdout
logging.basicConfig(
    level=logging.DEBUG,  # Nivel DEBUG para obtener todos los detalles
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

# Clase Command para almacenar la información de cada comando
class Command:
    def __init__(self, command_id, command, privileges_required, short_description, long_description):
        self.command_id = command_id
        self.command = command
        self.privileges_required = privileges_required
        self.short_description = short_description
        self.long_description = long_description

# Lista que contendrá los objetos de comandos
commands_list = []

# Función para cargar los comandos desde la base de datos
def load_commands_from_db():
    query = "SELECT * FROM commands"
    commands = db_connection.dbquery(query)

    if commands:
        for cmd in commands:
            new_command = Command(
                command_id=cmd['command_id'],
                command=cmd['command'],
                privileges_required=cmd['privileges_required'],
                short_description=cmd['short_description'],
                long_description=cmd['long_description']
            )
            commands_list.append(new_command)
        logging.info(f"Comandos cargados desde la base de datos: {len(commands_list)} comandos.")
    else:
        logging.error("No se pudieron cargar los comandos desde la base de datos.")

# Función para verificar si el usuario tiene los privilegios para ejecutar un comando
def can_execute_command(command_name, user_privileges):
    for cmd in commands_list:
        if cmd.command == command_name:
            if user_privileges >= cmd.privileges_required:
                return True
            else:
                return False
    return None  # Retorna None si no se encuentra el comando

# Función para manejar el comando quit
def quit_command(conn, addr, connections):
    conn.send("Muchas gracias. ¡Vuelve pronto!\n".encode('utf-8'))
    conn.close()
    # Remover la conexión del array de conexiones activas
    for connection in connections:
        if connection["ip"] == addr[0]:
            connections.remove(connection)
            break
    logging.info(f"Conexión con {addr[0]} terminada mediante el comando 'quit'.")

# Cargar los comandos al iniciar el módulo
load_commands_from_db()
