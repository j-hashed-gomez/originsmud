import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendverificationcode(email, username, validation_code):
    sender_email = "no_reply@originsmud.es"  # Cambia esto a tu email de envío
    sender_password = "tu_contraseña"      # Cambia esto a la contraseña del email
    subject = f"Bienvenido a OriginsMUD, tu código de verificación es {validation_code}"

    # Crear el cuerpo del correo
    body = f"""
    <p>Bienvenido a OriginsMUD, <strong>{username}</strong>,</p>
    <p>Aún queda un paso pendiente para la creación de tu personaje y es introducir el siguiente código de verificación: <strong>{validation_code}</strong>.</p>
    <p>Este código se te preguntará en tu próximo inicio de sesión con el personaje.</p>
    <p>Muchas gracias y ¡Diviértete!</p>
    """

    # Configurar el correo
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        # Conectar con el servidor SMTP
        with smtplib.SMTP_SSL("localhost", 465) as server:  # Cambia esto por tu servidor SMTP
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
            print(f"Correo enviado con éxito a {email}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
