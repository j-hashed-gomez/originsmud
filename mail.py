import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendverificationcode(email, username, validation_code):
    # Configurar el remitente y destinatario
    sender_email = "noreply@originsmud.es"
    receiver_email = email

    # Crear el mensaje
    subject = f"Bienvenido a OriginsMUD, tu código de verificación es {validation_code}"
    body = f"""
    Bienvenido a OriginsMUD, {username},

    Aún queda un paso pendiente para la creación de tu personaje y es introducir el siguiente código de verificación: <strong>{validation_code}</strong>.

    Muchas gracias y ¡Diviértete!
    """

    # Crear el contenedor del mensaje de correo
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    # Enviar el correo utilizando Postfix como servidor SMTP
    try:
        with smtplib.SMTP("localhost", 25) as server:
            server.sendmail(sender_email, receiver_email, message.as_string())
            print(f"Correo enviado con éxito a {receiver_email}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
