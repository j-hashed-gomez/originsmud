import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import logging

# Configuración de logs centralizada para que todo salga por stdout
logging.basicConfig(
    level=logging.DEBUG,  # Nivel DEBUG para obtener todos los detalles
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

def sendverificationcode(email, username, validation_code):
    sender_email = "noreply@originsmud.es"
    receiver_email = email

    subject = f"Bienvenido a OriginsMUD, tu código de verificación es {validation_code}"
    body = f"""
    Bienvenido a OriginsMUD, {username},

    Aún queda un paso pendiente para la creación de tu personaje y es introducir el siguiente código de verificación: <strong>{validation_code}</strong>.

    Muchas gracias y ¡Diviértete!
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        logging.debug(f"Enviando correo de verificación a {receiver_email}...")
        with smtplib.SMTP("localhost", 25) as server:
            server.sendmail(sender_email, receiver_email, message.as_string())
            logging.info(f"Correo enviado con éxito a {receiver_email}")
    except Exception as e:
        logging.error(f"Error al enviar el correo de verificación a {receiver_email}: {e}")


def mail_resetpassword(email, new_password):
    sender_email = "noreply@originsmud.es"
    receiver_email = email

    subject = "Restablecimiento de contraseña de OriginsMUD"
    body = f"""
    Hola,

    Tu nueva contraseña para OriginsMUD es: <strong>{new_password}</strong>.

    Por favor, inicia sesión con esta nueva contraseña y cámbiala tan pronto como puedas.

    ¡Gracias y diviértete!
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        logging.debug(f"Enviando correo de restablecimiento de contraseña a {receiver_email}...")
        with smtplib.SMTP("localhost", 25) as server:
            server.sendmail(sender_email, receiver_email, message.as_string())
            logging.info(f"Correo de restablecimiento de contraseña enviado con éxito a {receiver_email}")
    except Exception as e:
        logging.error(f"Error al enviar el correo de restablecimiento a {receiver_email}: {e}")
