import os

def sendverificationcode(email, username, validation_code):
    subject = f"Bienvenido a OriginsMUD, tu código de verificación es {validation_code}"
    body = f"""
    Bienvenido a OriginsMUD, {username},
    
    Aún queda un paso pendiente para la creación de tu personaje y es introducir el siguiente código de verificación: {validation_code}.
    
    Muchas gracias y ¡Diviértete!
    """

    # Crear el mensaje en formato requerido para msmtp
    message = f"Subject: {subject}\nTo: {email}\nFrom: noreply@originsmud.es\n\n{body}"

    # Guardar el mensaje en un archivo temporal y enviarlo con msmtp
    with open("/tmp/email.txt", "w") as f:
        f.write(message)

    # Enviar el correo usando msmtp
    os.system("msmtp -t < /tmp/email.txt")
