import db_connection
import logging
import os
import bcrypt
from datetime import datetime, timedelta
import random
from mail import sendverificationcode, mail_resetpassword

# Lista para almacenar las IPs temporalmente bloqueadas
temp_blocked_ips = []

# Función para verificar si la IP está bloqueada
def is_ip_blocked(ip):
    for blocked_ip in temp_blocked_ips:
        if blocked_ip['ip'] == ip:
            if datetime.now() < blocked_ip['date'] + timedelta(minutes=1):
                return True
            else:
                temp_blocked_ips.remove(blocked_ip)
                return False

# Función para hashear la contraseña
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Función para verificar la contraseña
def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

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

    conn.send("Ingrese su nombre de usuario: ".encode('utf-8'))
    username = conn.recv(1024).decode().strip()

    query = "SELECT * FROM users WHERE username = %s"
    user = db_connection.dbquery(query, (username,), fetchone=True)

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

        hashed_password = hash_password(password)
        validation_code = generate_validation_code()

        sendverificationcode(email, username, validation_code)

        insert_query = """
            INSERT INTO users (username, password, mail, privileges, validated, validation_code)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        db_connection.dbquery(insert_query, (username, hashed_password, email, 100, 0, validation_code))
        conn.send(f"Usuario creado con éxito. Verifique su correo electrónico en {email}.\n".encode('utf-8'))
        conn.close()
        return

    if user['active'] == 0:
        conn.send("Su cuenta ha sido deshabilitada. Por favor, consulte con un administrador.\n".encode('utf-8'))
        conn.close()
        return

    for attempt in range(3):
        conn.send("Ingrese su contraseña: ".encode('utf-8'))
        password = conn.recv(1024).decode().strip()

        if verify_password(user['password'], password):
            if user['validated'] == 1:
                conn.send(f"Bienvenido de nuevo, {username}!\n".encode('utf-8'))
                return
            else:
                conn.send("Ingrese el código de validación enviado a su correo electrónico: ".encode('utf-8'))
                for i in range(3):
                    validation_code = conn.recv(1024).decode().strip()
                    if str(user['validation_code']) == validation_code:
                        update_query = "UPDATE users SET validated = 1 WHERE username = %s"
                        db_connection.dbquery(update_query, (username,))
                        conn.send(f"Validación completada. Bienvenido {username}!\n".encode('utf-8'))
                        return
                    else:
                        conn.send("Código de validación incorrecto. Intente de nuevo.\n".encode('utf-8'))
                conn.send("Ha fallado 3 veces. La conexión será cerrada.\n".encode('utf-8'))
                conn.close()
                return
        else:
            conn.send(f"Contraseña incorrecta. Le quedan {2 - attempt} intentos.\n".encode('utf-8'))

    # Después de 3 intentos fallidos, pregunta sobre la recuperación de la contraseña
    conn.send("Ha intentado demasiadas veces. ¿Desea iniciar el proceso de recuperación de contraseña? (s/n): ".encode('utf-8'))
    response = conn.recv(1024).decode().strip().lower()

    if response == 's':
        conn.send("Ingrese su dirección de correo electrónico: ".encode('utf-8'))
        email = conn.recv(1024).decode().strip()

        query = "SELECT * FROM users WHERE username = %s AND mail = %s"
        user_email = db_connection.dbquery(query, (username, email), fetchone=True)

        if not user_email:
            conn.send("La cuenta de correo no existe en nuestro sistema.\n".encode('utf-8'))
            conn.close()
            return

        new_password = str(random.randint(10000, 99999))
        hashed_password = hash_password(new_password)

        update_query = "UPDATE users SET password = %s WHERE username = %s AND mail = %s"
        db_connection.dbquery(update_query, (hashed_password, username, email))

        mail_resetpassword(email, new_password)
        conn.send("Revise su bandeja de entrada para la nueva contraseña.\n".encode('utf-8'))
        conn.close()
        return
    else:
        conn.send("De acuerdo, pues inténtalo de nuevo.\n".encode('utf-8'))
        conn.close()
