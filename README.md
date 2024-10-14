# Monitorizacion_archivos
Este script hecho en python monitoriza la creacion de ficheros en linux. Genera logs sobre los archivos creados, eliminados y modificados ademas de alerta por correo sobre aquellos archivos con permisos elevados.

### Funcionamiento
#### El script necesita dos archivos:
* directorios.json
  Se usa un archivo .json para indicar los directorios a monitorizar. EJ:
  0 -> No monitorizar de manera recursiva
  1 -> Monitorizar de manera recursiva
  {
    "/": 0,
    "/home": 1,
    "/root": 1,
    "/var/tmp": 1,
    "/tmp": 1
  }
* ignorar_archivos.txt
    En este archivo se colocan los archivos o las coincidencias de archivos que no se quieren monitorizar.
    ##### Nota: Para NO monitorizar directorios que estan dentro de los diectorios a monitorizar de manera recursiva, se deben añadir a este archivo esos directorios.

### Para el correo es necesario cambiar las variables:
* CORREO = 'tu_correo'
* PASS = 'contraseña_aplicacion' -> se consigue al tener activado la doble autentificacion en seguridad en gmail y al buscar 'contraseña de aplicaciones'.
* CORREO_DESTINO = 'correo_destino'

### Consideraciones:
* La opcion del correo no esta desactivada. Si no se quiere usar basta con comentar la linea self.enviar_correo() en las funciones on_created y on_modified.


## Puedes configurar este script como un servicio, para ello puedes hacer esto:

#### 1.- crear el archivo de servicio en systemd
* sudo nano /etc/systemd/system/script.service

#### 2.- colocar lo siguiente:
[Unit]
Description=Script Monitorizacion Archivos
After=network.target

[Service]
ExecStart=/usr/bin/python3 scriptFicheros.py
WorkingDirectory=/ruta_directorio_script
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target

#### 3.- Reiniciar demonio
* sudo systemctl daemon-reload
