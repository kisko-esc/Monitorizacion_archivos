#!/bin/bash/ env python3

import sys
import os
import json
import subprocess
import pkg_resources
import re
from datetime import datetime
import ast

# Instalar la libreria necesaria
lib = "watchdog"

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def comprobacion():
    try:
        existe = pkg_resources.require(lib)
        if existe:
            return True

    except pkg_resources.DistributionNotFound:
        print("La biblioteca 'watchdog' no esta instalada. Intentando instalar...")

        try:
            install_package("watchdog")
            print("Instalacion exitosa")
            return True
        
        except Exception as e:
            print(f"Error durante la instalacion de 'watchdog': {e}")

        sys.exit(1)

    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)

if comprobacion():
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import time
    import mimetypes

class Ficheros(FileSystemEventHandler):
    def __init__(self):
        self.archivos_creados = []
        self.log_archivos = './archivos_creados.txt' # Archivo donde se almacenaran los datos de la variable archivos_creados 

        self.actual_dir = os.path.dirname(os.path.realpath(__file__)) # Directorio actual
        self.log = './logFicheros.txt'
    
    def run(self):
        global now
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        observer = Observer()

        # Directorios a monitorizar
        for path, recursive in self.directorios():
            observer.schedule(self, path=path, recursive=bool(recursive))
        
        observer.start()

        try:
            if os.path.exists(self.log_archivos):
                self.leer_archivos()
                
            while True:
                time.sleep(1)
                now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                sys.stdout = open(self.log, '+a') # Redirigir la salida de los print() a un fichero log
                
        except KeyboardInterrupt:
            observer.stop()
            sys.stdout.close()

        observer.join()

        sys.stdout = sys.__stdout__ # devolver la salida por consola
    
    # Eventos
    
    def on_created(self, event):
        if not self.excepciones(event.src_path) and os.path.exists(event.src_path):
            tipo_archivo = mimetypes.guess_type(event.src_path)[0]
            permisos_archivo = self.permisos(event.src_path)

            print(" ")
            print(f'[+] - Archivo Creado: {event.src_path}')
            print(f'Tipo Archivo: {tipo_archivo}')
            print(f'Hora: {now}')
            print(f'Permisos: {permisos_archivo}')
            
            '''
                Registrar archivos creados en una variable:
                Consume Ram y además es una variable temporal, por lo que al reiniciar el programa
                estos datos se pierden. Por ello se registran estos datos en un fichero txt para luego ir
                detectando los cambios de permisos de esos archivos.
            ''' 
            archivo = [event.src_path, tipo_archivo, permisos_archivo]
            self.registrar_archivos(archivo)

            # Acciones | Enviar correo
            self.acciones(event.src_path, permisos_archivo, tipo_archivo)

    def on_deleted(self, event):
        if not self.excepciones(event.src_path):
            print(" ")
            print(f'[-] - Archivo Eliminado: {event.src_path}')
            print(f'Hora: {now}')

            self.eliminar_linea_archivo(event.src_path)
            
    def on_modified(self, event):
        if not self.excepciones(event.src_path) and os.path.exists(event.src_path):
            tipo_archivo = mimetypes.guess_type(event.src_path)[0]
            permisos_archivo = self.permisos(event.src_path)

            for archivo in self.archivos_creados:
                if archivo[0] == event.src_path and archivo[2] != self.permisos(event.src_path):
                    print(' ')
                    print(f"[!] - Permisos modificados para: {archivo[0]}")
                    print(f"Permisos originales: {archivo[2]}")
                    print(f'Permisos actuales: {permisos_archivo}')

                    # Modificar variable self.archivos_creados y fichero archivos_creados.txt
                    self.eliminar_linea_archivo(event.src_path)
                    datos = [event.src_path, tipo_archivo, permisos_archivo]
                    self.registrar_archivos(datos)

                    # Acciones | Enviar Correo
                    self.acciones(event.src_path, permisos_archivo, tipo_archivo)


    # Funciones para la monitorización

    def excepciones(self, path):
        '''
            Excepcion de archivos a monitorizar.
            Tambien pueden ser directorios.
        '''
        FILE = os.path.join(self.actual_dir, 'ignorar_archivos.txt')
        with open(FILE, 'r') as ignorar:
            for pattern in ignorar:
                pattern = pattern.strip()
                if re.search(re.escape(pattern), path):
                    return True
            return False


    def directorios(self):
        '''
            Directorios a monitorizar
        '''
        FILE = os.path.join(self.actual_dir, 'directorios.json')
        try:
            with open(FILE, 'r') as j:
                datos = json.load(j)
                for dir, val in zip(datos.keys(), datos.values()):
                    if os.path.exists(dir):
                        yield dir, val

        except FileNotFoundError:
            print("[ERROR] - No existe un Archivo json con los directorios a monitorizar. Cree dicho archivo")
            print(r'[Ejemplo] - {"/Directorio/a/monitorizar":1, ...etc} Siendo 1 -> True y 0 -> False el querer monitorizar dicho directorio de manera recursiva o no')
            sys.exit(1)

        except Exception as e:
            print(f"Ha ocurrido un error:\n{e}")
            sys.exit(1)
    
    def acciones(self, path, permisos, tipo_archivo):
        # Detectar permisos elevados
        if '7' in str(permisos) and not os.path.isdir(path):
            #os.chmod(path, 000) # quitar todos los permisos

            print(' ')
            print("[!] - Permisos elevados detectados")

            msg = f'[!] - Permisos elevados detectados!\n\nArchivo: {path}\nPermisos: {permisos}\nTipo Archivo: {tipo_archivo}\nHora: {now}'
            self.enviar_correo("[!] - Permisos elevados detectados", msg)
            print("-- Correo enviado --")


    def permisos(self, path):
        try:
            permisos = oct(os.stat(path).st_mode)[-3:]
            return permisos
        
        except FileNotFoundError as e:
            print(f"Error. No existe el directorio {path}\n{e}")
    # Correo

    def enviar_correo(self, asunto, msg):

        import smtplib
        from email.message import EmailMessage

        CORREO = 'tu_correo'
        PASS = 'contraseña_aplicacion'
        CORREO_DESTINO = 'correo_destino'

        email = EmailMessage()
        email['From'] = CORREO
        email['To'] = CORREO_DESTINO
        email['Subject'] = asunto

        # Establecer el cuerpo del mensaje como texto plano con codificación UTF-8
        email.set_content(msg, subtype='plain', charset='utf-8')

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(CORREO, PASS)
            smtp.send_message(email)

    
    # Registrar y recordar los archivos que se crearon

    def registrar_archivos(self, file):
        '''
            Registro el archivo creado tanto en el fichero txt como en la variable temporal self.archivos_creados
        '''
        with open(self.log_archivos, '+a') as f:
            f.write(str(file)+'\n')
            self.archivos_creados.append(file)
                    
    def leer_archivos(self):
        '''
            Su funcion es recordar los archivos que se crearon con la ejecucion anterior del script, si este se reinicia.
        '''
        with open(self.log_archivos, 'r') as f:
            for i in f:
                self.archivos_creados.append(ast.literal_eval(i.strip()))

    def eliminar_linea_archivo(self, file):
        self.archivos_creados.clear() # borro lista actual

        with open(self.log_archivos, '+r') as linea, open(f'{self.log_archivos}.tmp', 'a') as temp_file:
            for i in linea:
                if not re.search(r'\[\'' + re.escape(file) + r'\'', i):
                    temp_file.write(i)
                    self.archivos_creados.append(ast.literal_eval(i.strip())) # añado nuevos elementos a la variable temporal
        os.replace(f'{self.log_archivos}.tmp', self.log_archivos) # Reemplazo el archivo temporal por el original
        
if __name__ == '__main__':
    fichero = Ficheros()
    fichero.run()

