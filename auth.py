import db_connection
import mysql.connector
import logging
import os
from datetime import datetime, timedelta
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
    logging.debug("Claves cargadas correctamente.")

private_key_pem = private_key_pem.encode()
public_key_pem = public_key_pem.encode()

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

# Función para cifrar contraseñas
def encrypt_password(password):
    encrypted = public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted

# Función para descifrar contraseñas
def decrypt_password(encrypted_password):
    decrypted = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted.decode()

# Función de autenticación
def authenticate_user(conn, addr):
    ip = addr[0]  # Dirección IP del cliente
    retries = 0   # Contador de intentos fallidos
    
    # Verificar si la IP está bloqueada
    if is_ip_blocked(ip):
        conn.send("Su IP está temporalmente bloqueada. Intente de nuevo más tarde.\n".encode('utf-8'))
        return False
    
    # Crear la conexión a la base de datos
    connection = db_connection.connect_to_database()
    if not connection:
        conn.send("Error al conectar a la base de datos. Intente de nuevo más tarde.\n".encode('utf-8'))
        return False
    
    try:
        cursor = connection.cursor(dictionary=True)
        while retries < 3:
            # Solicitar username y password
            conn.send("Ingrese su nombre de usuario: ".encode('utf-8'))
            username = conn.recv(1024).decode().strip()
            conn.send("Ingrese su contrasena: ".encode('utf-8'))
            password = conn.recv(1024).decode().strip()

            # Encriptar la contraseña antes de enviarla a la base de datos
            encrypted_password = encrypt_password(password)

            # Consultar en la base de datos si el usuario y la contraseña son correctos
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, encrypted_password))
            result = cursor.fetchone()

            if result:
                # Usuario autenticado correctamente
                welcome_message = f"Bienvenido a OriginsMUD, {username}!\n"
                conn.send(welcome_message.encode('utf-8'))
                logging.info(f"Usuario {username} autenticado correctamente desde {ip}")
                return True
            else:
                # Fallo de autenticación
                retries += 1
                conn.send("Nombre de usuario o contrasena incorrectos. Intente de nuevo.\n".encode('utf-8'))
                logging.warning(f"Intento fallido de autenticación desde {ip}")

    except mysql.connector.Error as e:
        logging.error(f"Error en la consulta a la base de datos: {e}")
        conn.send("Error en la consulta a la base de datos.\n".encode('utf-8'))
    
    finally:
        # Cerrar la conexión a la base de datos
        db_connection.close_database_connection(connection)

    # Si falla 3 veces, bloquear la IP y purgar la sesión
    if retries >= 3:
        temp_blocked_ips.append({
            "ip": ip,
            "date": datetime.now()
        })
        conn.send("Ha fallado 3 veces. Su IP esta temporalmente bloqueada por 1 minuto.\n".encode('utf-8'))
        logging.warning(f"IP {ip} bloqueada temporalmente por 1 minuto.")
        
        # Purgar la sesión cerrando la conexión con el cliente
        conn.close()
        logging.info(f"Sesión purgada para la IP {ip} tras 3 intentos fallidos.")

    return False
