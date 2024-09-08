import db_connection
import mysql.connector
import logging
import os
from datetime import datetime, timedelta
import random

# Lista para almacenar las IPs temporalmente bloqueadas
temp_blocked_ips = []

# Función para verificar si la IP está bloqueada
def is_ip_blocked(ip):
    for blocked_ip in temp_blocked_ips:
        if blocked_ip['ip'] == ip:
            if datetime.now() < blocked_ip['date'] + timedelta(minutes=1):
                return True
            else:
                # Eliminar IP del array si ha pasado el tiempo de bloqueo
                temp_blocked_ips.remove(blocked_ip)
                return False
    return False

# Función para crear un nuevo código de validación
def generate_validation_code():
    return random.randint(100000, 999999)

# Función de autenticación
def authenticate_user(conn, addr):
    ip = addr[0]
    retries = 0
    
    if is_ip_blocked(ip):
        conn.send("Su IP está temporalmente bloqueada. Intente de nuevo más tarde.\n".encode('utf-8'))
        return False
    
    connection = db_connection.connect_to_database()
    if not connection:
        conn.send("Error al conectar a la base de datos. Intente de nuevo más tarde.\n".encode('utf-8'))
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        conn.send("Ingrese su nombre de usuario: ".encode('utf-8'))
        username = conn.recv(1024).decode().strip()

        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if not user:
            conn.send("El usuario no existe. ¿Desea crear un nuevo usuario? (si/no): ".encode('utf-8'))
            response = conn.recv(1024).decode().strip().lower()

            if response == 'no':
                conn.send("Despedida. La conexión será cerrada.\n".encode('utf-8'))
                conn.close()
                return

            conn.send("Ingrese su dirección de correo electrónico: ".encode('utf-8'))
            email = conn.recv(1024).decode().strip()
            conn.send("Ingrese una contraseña: ".encode('utf-8'))
            password = conn.recv(1024).decode().strip()

            validation_code = generate_validation_code()

            insert_query = """
                INSERT INTO users (username, password, mail, privileges, validated, validation_code)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (username, password, email, 100, 0, validation_code))
            connection.commit()

            conn.send(f"Usuario creado con éxito. Verifique su correo electrónico con el código: {validation_code}\n".encode('utf-8'))
            conn.close()
            return
        
        # Usuario existe, validar la contraseña y el estado de validación
        conn.send("Ingrese su contraseña: ".encode('utf-8'))
        password = conn.recv(1024).decode().strip()

        # Debug detallado: Mostrar la información del usuario desde la base de datos
        logging.debug(f"Usuario introducido: {username}")
        logging.debug(f"Password introducido: {password}")
        logging.debug(f"Datos en la DB - Nombre de usuario: {user['username']}, Password: {user['password']}")
        logging.debug(f"Código de validación en la DB: {user['validation_code']}")

        if user['validated'] == 0:
            conn.send("Ingrese el código de validación enviado a su correo electrónico: ".encode('utf-8'))
            validation_code = conn.recv(1024).decode().strip()

            logging.debug(f"Código de validación introducido por el usuario: {validation_code}")

            if str(user['validation_code']) == validation_code and user['password'] == password:
                update_query = "UPDATE users SET validated = 1 WHERE username = %s"
                cursor.execute(update_query, (username,))
                connection.commit()
                conn.send(f"Validación completada. Bienvenido {username}!\n".encode('utf-8'))
            else:
                conn.send("Código de validación o contraseña incorrectos.\n".encode('utf-8'))
                conn.close()
                return
        elif user['validated'] == 1 and user['password'] == password:
            conn.send(f"Bienvenido de nuevo, {username}!\n".encode('utf-8'))
        else:
            retries += 1
            conn.send("Contraseña incorrecta. Intente de nuevo.\n".encode('utf-8'))
            if retries >= 3:
                temp_blocked_ips.append({"ip": ip, "date": datetime.now()})
                conn.send("Ha fallado 3 veces. IP bloqueada por 1 minuto.\n".encode('utf-8'))
                conn.close()
                return

    except mysql.connector.Error as e:
        logging.error(f"Error en la consulta a la base de datos: {e}")
        conn.send("Error en la consulta a la base de datos.\n".encode('utf-8'))
    finally:
        db_connection.close_database_connection(connection)
