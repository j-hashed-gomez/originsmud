# Utilizar la imagen oficial de Debian como base
FROM ubuntu:latest

# Actualizar los paquetes e instalar Postfix, Python y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nano \
    postfix \
    rsyslog \
    && apt-get clean

# Configurar Postfix para que acepte correos desde localhost
RUN echo "inet_interfaces = loopback-only" >> /etc/postfix/main.cf \
    && echo "mydestination = localhost, originsmud.es" >> /etc/postfix/main.cf \
    && echo "myhostname = originsmud.es" > /etc/postfix/main.cf \
    && echo "inet_protocols = ipv4" >> /etc/postfix/main.cf

# Reiniciar Postfix para aplicar la configuración
RUN service postfix restart

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Crear y activar un entorno virtual
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copiar el archivo requirements.txt al contenedor
COPY requirements.txt /app/

# Instalar las dependencias de Python desde el archivo requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar todos los archivos del repositorio al contenedor en el directorio /app
COPY . /app

# Dar permisos de ejecución al script originsmud_server.py si es necesario
RUN chmod +x /app/originsmud_server.py

# Exponer el puerto TCP 5432
EXPOSE 5432

# Iniciar el servicio Postfix y luego ejecutar el script de Python
#CMD [ "tail", "-f", "/dev/null" ]
CMD [ "python3", "/app/originsmud_main.py" ]
