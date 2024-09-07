import originsmud_server
import db_connection

if __name__ == "__main__":
    print("Iniciando servidor OriginsMUD...")

    # Comprobar la conexión a la base de datos
    connection = db_connection.connect_to_database()
    if connection:
        print("Conexión a la base de datos establecida.")
    else:
        print("Error al conectar a la base de datos. Verifica las configuraciones.")
        exit(1)  # Salir si no hay conexión a la base de datos

    # Iniciar el servidor
    originsmud_server.start_server()
