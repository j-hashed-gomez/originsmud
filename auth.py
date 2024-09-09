import db_connection
import logging
import os
import bcrypt
from datetime import datetime, timedelta
import random
from mail import sendverificationcode, mail_resetpassword
import sys

# Configuración de logs centralizada para que todo salga por stdout
logging.basicConfig(
    level=logging.DEBUG,  # Nivel DEBUG para obtener todos los detalles
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

# Lista para almacenar las IPs temporalmente bloqueadas
temp_blocked_ips = []

# Función para verificar si la IP está bloqueada
def is_ip_blocked(ip):
    for blocked_ip in temp_blocked_ips:
        if blocked_ip['ip'] == ip:
            if datetime.now() < blocked_ip['date'] + timedelta(minutes=1):
                logging.debug(f"La IP {ip} está bloqueada temporalmente.")
                return True
            else:
                temp_blocked_ips.remove(blocked_ip)
                logging.debug(f"La IP {ip} ya no está bloqueada.")
                return False

# Función para hashear la contraseña
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    logging.debug(f"Contraseña hasheada correctamente.")
    return hashed.decode('utf-8')

# Función para verificar la contraseña
def verify_password(stored_password, provided_password):
    result = bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
    if result:
        logging.debug("La contraseña proporcionada es correcta.")
    else:
        logging.debug("La contraseña proporcionada es incorrecta.")
    return result

# Función para crear un nuevo código de validación
def generate_validation_code():
    code = random.randint(100000, 999999)
    logging.debug(f"Código de validación generado: {code}")
    return code

# Función de autenticación
def authenticate_user(conn, addr):
    ip = addr[0]
    retries = 0
    
    logging.debug(f"Intentando autenticar la IP {ip}.")
    
    if is_ip_blocked(ip):
        conn.send("Su IP está temporalmente bloqueada. Intente de nuevo más tarde.\n".encode('utf-8'))
        return None

    conn.send("Ingrese su nombre de usuario: ".encode('utf-8'))
    username = conn.recv(1024).decode().strip()
    logging.debug(f"Nombre de usuario recibido: {username}")

    query = "SELECT * FROM users WHERE username = %s"
    user = db_connection.dbquery(query, (username,), fetchone=True)

    if not user:
        logging.warning(f"El usuario {username} no existe.")
        conn.send("El usuario no existe. ¿Desea crear un nuevo usuario? (si/no): ".encode('utf-8'))
        response = conn.recv(1024).decode().strip().lower()

        if response == 'no':
            conn.send("Despedida. La conexión será cerrada.\n".encode('utf-8'))
            conn.close()
            return None

        conn.send("Ingrese su dirección de correo electrónico: ".encode('utf-8'))
        email = conn.recv(1024).decode().strip()
        conn.send("Ingrese una contraseña: ".encode('utf-8'))
        password = conn.recv(1024).decode().strip()

        hashed_password = hash_password(password)
        validation_code = generate_validation_code()

        logging.debug(f"Creando nuevo usuario: {username}, Email: {email}, Código de validación: {validation_code}")
        sendverificationcode(email, username, validation_code)

        insert_query = """
            INSERT INTO users (username, password, mail, privileges, validated, validation_code)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        db_connection.dbquery(insert_query, (username, hashed_password, email, 100, 0, validation_code))
        conn.send(f"Usuario creado con éxito. Verifique su correo electrónico en {email}.\n".encode('utf-8'))
        logging.info(f"Usuario {username} creado con éxito.")
        conn.close()
        return None

    if user['active'] == 0:
        logging.warning(f"La cuenta de {username} está deshabilitada.")
        conn.send("Su cuenta ha sido deshabilitada. Por favor, consulte con un administrador.\n".encode('utf-8'))
        conn.close()
        return None

    for attempt in range(3):
        conn.send("Ingrese su contraseña: ".encode('utf-8'))
        password = conn.recv(1024).decode().strip()

        if verify_password(user['password'], password):
            if user['validated'] == 1:
                conn.send(f"Bienvenido de nuevo, {username}!\n".encode('utf-8'))
                logging.info(f"Usuario {username} autenticado con éxito.")
                return user['privileges']
            else:
                conn.send("Ingrese el código de validación enviado a su correo electrónico: ".encode('utf-8'))
                for i in range(3):
                    validation_code = conn.recv(1024).decode().strip()
                    if str(user['validation_code']) == validation_code:
                        update_query = "UPDATE users SET validated = 1 WHERE username = %s"
                        db_connection.dbquery(update_query, (username,))
                        conn.send(f"Validación completada. Bienvenido {username}!\n".encode('utf-8'))
                        logging.info(f"Usuario {username} validado correctamente.")
                        return user['privileges']
                    else:
                        conn.send("Código de validación incorrecto. Intente de nuevo.\n".encode('utf-8'))
                        logging.warning(f"Código de validación incorrecto para {username}.")
                conn.send("Ha fallado 3 veces. La conexión será cerrada.\n".encode('utf-8'))
                logging.error(f"Fallos múltiples en la validación del código para {username}.")
                conn.close()
                return None
        else:
            conn.send(f"Contraseña incorrecta. Le quedan {2 - attempt} intentos.\n".encode('utf-8'))
            logging.warning(f"Contraseña incorrecta para {username}. Intentos restantes: {2 - attempt}.")

    # Después de 3 intentos fallidos, pregunta sobre la recuperación de la contraseña
    conn.send("Ha intentado demasiadas veces. ¿Desea iniciar el proceso de recuperación de contraseña? (s/n): ".encode('utf-8'))
    response = conn.recv(1024).decode().strip().lower()

    if response == 's':
        conn.send("Ingrese su dirección de correo electrónico: ".encode('utf-8'))
        email = conn.recv(1024).decode().strip()

        logging.debug(f"Iniciando recuperación de contraseña para {username} con el correo {email}.")
        
        query = "SELECT * FROM users WHERE username = %s AND mail = %s"
        user_email = db_connection.dbquery(query, (username, email), fetchone=True)

        if not user_email:
            conn.send("La cuenta de correo no existe en nuestro sistema.\n".encode('utf-8'))
            logging.warning(f"No se encontró el usuario {username} con el correo {email}.")
            conn.close()
            return None

        new_password = str(random.randint(10000, 99999))
        hashed_password = hash_password(new_password)

        update_query = "UPDATE users SET password = %s WHERE username = %s AND mail = %s"
        db_connection.dbquery(update_query, (hashed_password, username, email))

        logging.debug(f"Contraseña actualizada para el usuario {username}. Enviando correo.")
        mail_resetpassword(email, new_password)

        conn.send("Revise su bandeja de entrada para la nueva contraseña.\n".encode('utf-8'))
        logging.info(f"Proceso de recuperación de contraseña completado para {username}.")
        conn.close()
        return None
    else:
        conn.send("De acuerdo, pues inténtalo de nuevo.\n".encode('utf-8'))
        logging.debug(f"El usuario {username} optó por no iniciar el proceso de recuperación de contraseña.")
        conn.close()
        return None
