# Utilizar la imagen oficial de Debian como base
FROM debian:latest

# Actualizar los paquetes e instalar msmtp, Python y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nano \
    msmtp \
    && apt-get clean

# Configurar msmtp para enviar correos desde localhost
RUN echo "defaults" > /etc/msmtprc \
    && echo "auth off" >> /etc/msmtprc \
    && echo "tls off" >> /etc/msmtprc \
    && echo "logfile /var/log/msmtp.log" >> /etc/msmtprc \
    && echo "account default" >> /etc/msmtprc \
    && echo "host localhost" >> /etc/msmtprc \
    && echo "from noreply@originsmud.es" >> /etc/msmtprc \
    && echo "domain originsmud.es" >> /etc/msmtprc \
    && chmod 600 /etc/msmtprc

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

# Comando para iniciar el servidor
CMD ["python3", "/app/originsmud_main.py"]
