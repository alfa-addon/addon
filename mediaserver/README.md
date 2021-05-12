# __Importante: Soporte de Mediaserver con Python 2 roto: se reparará en cuanto sea posible__
# ¿Qué es MediaServer?
*Es una versión de Alfa que no necesita de Kodi para funcionar.*

Esta es una versión independiente que únicamente necesita un equipo que pueda ejecutar el servidor (Python 2 o 3), y un dispositivo con navegador web para navegar en Mediaserver.

Mediaserver se puede navegar desde cualquier dispositivo que cuente con un navegador web, útil para aquellos equipos que no pueden ejecutar Kodi ya sea por antigüedad o falta de soporte.

__**NOTA: Hay un bug con Mediaserver en Firefox de escritorio, por lo que por el momento Mediaserver no correrá en Firefox de escritorio__

------------

## Prerrequisitos:
### Servidor
- Se requiere que esté instalado Python (2.7+ o 3.6+)
  - Para Windows y varios sistemas puede descargarse [desde aquí](https://www.python.org/downloads/release/python-2718/ "desde aquí")
  - Para Linux basados en Debian puede instalarse con `sudo apt-get install python3`

### Cliente
- Cualquier dispositivo con un navegador compatible con WebSockets (prácticamente cualquier dispositivo/navegador capaz de cargar YouTube por poner un ejemplo)

## Instrucciones de instalación:
- Descarga la última versión de Alfa desde el [*repositorio de GitHub*](https://github.com/alfa-addon/addon "*repositorio de GitHub*") ([__enlace directo__](https://github.com/alfa-addon/addon/archive/refs/heads/master.zip "__enlace directo__"))
- Descomprime el archivo descargado (addon-master.zip), el cual nos dejará 2 carpetas, plugin.video.alfa y mediaserver
- Abre la carpeta mediaserver y copia todo su contenido
- Regresa, abre la carpeta plugin.video.alfa y pega el contenido de mediaserver, reemplazando los archivos existentes
- Mediaserver estará listo para ejecutarse

### Cómo iniciar MediaServer
- Windows
Abrimos la carpeta plugin.video.alfa que recién configuramos y abrimos el archivo `iniciar.cmd`
- Linux
Abrimos la carpeta plugin.video.alfa, con el menú contextual abrimos un terminal en la carpeta e ingresamos
```python
python2 alfa.py
```

En pantalla se mostrará la dirección para acceder a MediaServer desde un navegador web. Por ejemplo:

`http://192.168.0.10:8080`

Podremos acceder a MediaServer desde cualquier dispositivo con un navegador web relativamente reciente (ordenadores, móviles, TV Boxes, consolas, Rapsberry,...)
**NOTA: Firefox de escritorio no funciona de momento.