# ¿Qué es MediaServer?
Esta versión de Alfa no necesita de ningún programa para instalarse, ni siquiera Kodi. Es una versión independiente que únicamente necesita un equipo que pueda ejecutar Python 2.7 (en el cual se instalará MediaServer) y un dispositivo con navegador web para utilizar la interfaz (puede ser el mismo u otro dispositivo).

La interfaz se puede utilizar desde cualquier dispositivo que cuente con un navegador web, útil para aquellos equipos que no pueden ejecutar Kodi ya sea por su antigüedad o por que no tienen un sistema operativo compatible.

------------

## Prerrequisitos:
- Se requiere que esté instalado Python 2.7
  - Puede instalarse [desde aquí](https://www.python.org/downloads/release/python-2718/ "desde aquí") *(Windows)* o con `sudo apt install python2` *(Linux)*
- Algunos canales en Alfa requieren algunos módulos que no vienen en la instalación por defecto de Python. Estos se pueden instalar desde la línea de comandos (CMD en Windows o la aplicación de terminal en macOS/Linux)
  
  En la línea de comandos, ejecutamos:
```shell
pip2 install BeautifulSoup4
pip2 install html5lib
```

#### Nota para usuarios de Linux:
En distribuciones Linux recientes (por ejemplo Ubuntu 20.04), Python 2.7 está considerado obsoleto, por lo que `python2-pip` no se puede instalar vía APT, haciendo imposible instalar mediante `pip2` los módulos requeridos por MediaServer.

Alternativamente, para instalar `pip2` sin utilizar APT se pueden ejecutar los siguientes comandos en la terminal:
```shell
wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
sudo python2 get-pip.py
sudo pip install --upgrade pip
```


## Instrucciones de instalación:
- Descargar la última versión de Alfa desde el [repositorio de GitHub](https://github.com/alfa-addon/addon "repositorio de GitHub") (opcion **Code** -> **Download zip**)
- Descomprimimos el archivo descargado (addon-master.zip), el cual nos dejará 2 carpetas, plugin.video.alfa y mediaserver
- Abrimos la carpeta mediaserver y copiamos todo su contenido
- Abrimos la carpeta plugin.video.alfa y pegamos el contenido de mediaserver, reemplazando los archivos existentes
- Mediaserver estará listo para ejecutarse

## Cómo iniciar MediaServer
- Windows
Abrimos la carpeta plugin.video.alfa, en la barra de direcciones escribimos `cmd` y en la ventana de comandos ingresamos
```python
python alfa.py
```
- Linux
Abrimos la carpeta plugin.video.alfa, clic derecho en un espacio vacío > Abrir un terminal y en la terminal ingresamos
```python
python2 alfa.py
```

En la terminal se mostrará la dirección para acceder a MediaServer desde un navegador web. Por ejemplo:

`http://192.168.0.10:8080`

Podremos acceder a MediaServer desde cualquier dispositivo con un navegador web (ordenadores, móviles, TV Boxes, consolas, microordenadores,...)