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

            # Consultar en la base de datos si el usuario y la contraseña son correctos
            query = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
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

    # Si falla 3 veces, bloquear la IP
    if retries >= 3:
        temp_blocked_ips.append({
            "ip": ip,
            "date": datetime.now()
        })
        conn.send("Ha fallado 3 veces. Su IP esta temporalmente bloqueada por 1 minuto.\n".encode('utf-8'))
        logging.warning(f"IP {ip} bloqueada temporalmente por 1 minuto.")

    return False
