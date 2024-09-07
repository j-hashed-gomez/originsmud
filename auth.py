import db_connection
import mysql.connector
import logging
from datetime import datetime, timedelta

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

# Función de autenticación
def authenticate_user(conn, addr):
    ip = addr[0]  # Dirección IP del cliente
    retries = 0   # Contador de intentos fallidos
    
    # Verificar si la IP está bloqueada
    if is_ip_blocked(ip):
        conn.send(b"Su IP está temporalmente bloqueada. Intente de nuevo más tarde.\n")
        conn.close()
        return False
    
    # Conectar a la base de datos
    connection = db_connection.connect_to_database()
    if not connection:
        conn.send(b"Error al conectar a la base de datos. Intente de nuevo más tarde.\n")
        conn.close()
        return False
    
    cursor = connection.cursor(dictionary=True)
    
    while retries < 3:
        # Solicitar username y password
        conn.send(b"Ingrese su nombre de usuario: ")
        username = conn.recv(1024).decode().strip()
        conn.send(b"Ingrese su contrasena: ")
        password = conn.recv(1024).decode().strip()
        
        # Consultar en la base de datos si el usuario y la contraseña son correctos
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        
        if result:
            # Usuario autenticado correctamente
            welcome_message = f"Bienvenido a OriginsMUD, {username}!\n"
            conn.send(welcome_message.encode())
            logging.info(f"Usuario {username} autenticado correctamente desde {ip}")
            cursor.close()
            connection.close()
            return True
        else:
            # Fallo de autenticación
            retries += 1
            conn.send(b"Nombre de usuario o contrasena incorrectos. Intente de nuevo.\n")
            logging.warning(f"Intento fallido de autenticación desde {ip}")
    
    # Si falla 3 veces, bloquear la IP
    if retries >= 3:
        temp_blocked_ips.append({
            "ip": ip,
            "date": datetime.now()
        })
        conn.send(b"Ha fallado 3 veces. Su IP esta temporalmente bloqueada por 1 minuto.\n")
        logging.warning(f"IP {ip} bloqueada temporalmente por 1 minuto.")
    
    cursor.close()
    connection.close()
    conn.close()
    return False
