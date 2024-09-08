import db_connection
import mysql.connector
import logging
import os
import base64
from datetime import datetime, timedelta
import random
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Lista para almacenar las IPs temporalmente bloqueadas
temp_blocked_ips = []

# Cargar las claves desde las variables de entorno
private_key_pem = os.getenv('ORIGINSMUD_PRIVATE')
public_key_pem = os.getenv('ORIGINSMUD_PUBLIC')

if not private_key_pem or not public_key_pem:
    logging.error("No se pudieron cargar las claves ORIGINSMUD_PRIVATE o ORIGINSMUD_PUBLIC desde las variables de entorno.")
else:
    logging.debug(f"Clave privada cargada (primeros 50 caracteres): {private_key_pem[:50]}")
    logging.debug(f"Clave pública cargada (primeros 50 caracteres): {public_key_pem[:50]}")

# Reemplazar los caracteres especiales de salto de línea y convertir a bytes
private_key_pem = private_key_pem.replace('\\n', '\n').encode()
public_key_pem = public_key_pem.replace('\\n', '\n').encode()

# Cargar la clave privada desde las variables de entorno
private_key = serialization.load_pem_private_key(private_key_pem, password=None)

# Cargar la clave pública desde las variables de entorno
public_key = serialization.load_pem_public_key(public_key_pem)

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

# Función para cifrar contraseñas (y convertir a Base64)
def encrypt_password(password):
    try:
        password_bytes = password.encode()

        # Cifrar la contraseña con la clave pública
        encrypted = public_key.encrypt(
            password_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Convertir el resultado a Base64 para almacenamiento
        encrypted_base64 = base64.b64encode(encrypted).decode('utf-8')
        return encrypted_base64
    except Exception as e:
        logging.error(f"Error al cifrar la contraseña: {e}")
        raise

# Función para descifrar contraseñas
def decrypt_password(encrypted_password_base64):
    try:
        # Decodificar Base64 y descifrar la contraseña
        encrypted_bytes = base64.b64decode(encrypted_password_base64.encode('utf-8'))
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode()
    except Exception as e:
        logging.error(f"Error al descifrar la contraseña: {e}")
        raise

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

            encrypted_password = encrypt_password(password)
            validation_code = generate_validation_code()

            insert_query = """
                INSERT INTO users (username, password, mail, privileges, validated, validation_code)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (username, encrypted_password, email, 100, 0, validation_code))
            connection.commit()

            conn.send(f"Usuario creado con éxito. Verifique su correo electrónico con el código: {validation_code}\n".encode('utf-8'))
            conn.close()
            return
        
        # Usuario existe, validar la contraseña y el estado de validación
        conn.send("Ingrese su contraseña: ".encode('utf-8'))
        password = conn.recv(1024).decode().strip()
        encrypted_password = encrypt_password(password)

        # Debug detallado: Mostrar la información del usuario desde la base de datos
        db_decrypted_password = decrypt_password(user['password'])
        logging.debug(f"Datos introducidos por el usuario - Nombre de usuario: {username}, Contraseña cifrada: {encrypted_password}")
        logging.debug(f"Datos en la base de datos - Nombre de usuario: {user['username']}, Contraseña cifrada: {user['password']}, Contraseña descifrada: {db_decrypted_password}")

        if user['validated'] == 0:
            conn.send("Ingrese el código de validación enviado a su correo electrónico: ".encode('utf-8'))
            validation_code = conn.recv(1024).decode().strip()

            if str(user['validation_code']) == validation_code and user['password'] == encrypted_password:
                update_query = "UPDATE users SET validated = 1 WHERE username = %s"
                cursor.execute(update_query, (username,))
                connection.commit()
                conn.send(f"Validación completada. Bienvenido {username}!\n".encode('utf-8'))
            else:
                conn.send("Código de validación o contraseña incorrectos.\n".encode('utf-8'))
                conn.close()
                return
        elif user['validated'] == 1 and user['password'] == encrypted_password:
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

