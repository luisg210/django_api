# Despliegue en servidor Debian

Guía para desplegar la API Django (`taskapi`) en un servidor Debian 12 con **Gunicorn + Nginx + PostgreSQL**.

## Prerrequisitos

- Servidor Debian 12 con acceso SSH como usuario `root` o con sudo.
- Dominio o IP pública apuntando al servidor.
- Repositorio con el código disponible (Git).

## 1. Actualizar el sistema e instalar dependencias

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx postgresql postgresql-contrib
```

> Este proyecto usa Python 3.11 (ver `runtime.txt`). Debian 12 incluye Python 3.11 por defecto.

## 2. Crear usuario de aplicación

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
su - deploy
```

## 3. Clonar el repositorio

```bash
cd /opt
sudo chown -R deploy:deploy /opt
git clone https://github.com/luisg210/flask_api.git django_api
cd django_api
```

## 4. Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configurar PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE USER taskapi WITH PASSWORD 'cambia-esta-contrasena';
CREATE DATABASE taskapi OWNER taskapi;
GRANT ALL PRIVILEGES ON DATABASE taskapi TO taskapi;
\q
```

## 6. Crear el archivo de variables de entorno `.env`

```bash
cat > .env << 'EOF'
SECRET_KEY=genera-una-clave-unica
DB_URL=postgres://taskapi:cambia-esta-contrasena@localhost:5432/taskapi
FRONT_END=https://tu-frontend.example.com
EOF
```

Generar una clave segura:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 7. Ajustes recomendados en producción

Antes de desplegar, edita `taskapi/settings.py`:

- Un `DEBUG = False`.
- `SECRET_KEY` desde el entorno: `os.getenv('SECRET_KEY')`.
- `ALLOWED_HOSTS = ['tu-dominio.com']`.
- Agrega `STATIC_ROOT = BASE_DIR / 'staticfiles'`.
- Agrega `CSRF_TRUSTED_ORIGINS` con tu dominio.

## 8. Migraciones, estáticos y prueba

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser   # opcional, para el admin
```

Probar que gunicorn arranca:

```bash
gunicorn taskapi.wsgi --bind 0.0.0.0:8000
```

## 9. Crear el servicio systemd para Gunicorn

```bash
sudo nano /etc/systemd/system/taskapi.service
```

```ini
[Unit]
Description=Gunicorn para taskapi
After=network.target postgresql.service

[Service]
User=deploy
Group=deploy
WorkingDirectory=/opt/django_api
EnvironmentFile=/opt/django_api/.env
ExecStart=/opt/django_api/venv/bin/gunicorn taskapi.wsgi --bind unix:/tmp/taskapi.sock --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

Habilitar e iniciar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable taskapi
sudo systemctl start taskapi
sudo systemctl status taskapi
```

## 10. Configurar Nginx como proxy inverso

```bash
sudo nano /etc/nginx/sites-available/taskapi
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location /static/ {
        alias /opt/django_api/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/tmp/taskapi.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar y recargar:

```bash
sudo ln -s /etc/nginx/sites-available/taskapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 11. Ejecutar migraciones al actualizar el código

En cada despliegue nuevo:

```bash
cd /opt/django_api
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart taskapi
```

## 12. (Opcional) TLS con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## Solución de problemas

- `sudo journalctl -u taskapi -e` — logs de Gunicorn.
- `sudo tail -f /var/log/nginx/error.log` — errores de Nginx.
- `sudo systemctl status taskapi` — estado del servicio.
- Verificar el socket: `curl --unix-socket /tmp/taskapi.sock http://localhost`