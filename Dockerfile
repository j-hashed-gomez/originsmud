# Utilizar la imagen oficial de Debian como base
FROM debian:latest

# Actualizar los paquetes e instalar sendmail, Python y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nano \
    sendmail \
    sendmail-bin \
    && apt-get clean

# Configurar sendmail para que escuche solo en localhost
RUN echo "DAEMON_OPTIONS('Port=smtp,Addr=127.0.0.1, Name=MTA')dnl" >> /etc/mail/sendmail.mc \
    && echo "FEATURE('relay_local_from')dnl" >> /etc/mail/sendmail.mc \
    && echo "Cwlocalhost originsmud.es" >> /etc/mail/sendmail.mc \
    && echo "LOCAL_DOMAIN('localhost')dnl" >> /etc/mail/sendmail.mc \
    && echo "DOMAIN('originsmud.es')dnl" >> /etc/mail/sendmail.mc \
    && m4 /etc/mail/sendmail.mc > /etc/mail/sendmail.cf \
    && newaliases \
    && service sendmail restart

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

# Iniciar el servicio sendmail y luego ejecutar el script de Python
CMD service sendmail start && python3 /app/originsmud_main.py
