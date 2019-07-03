# setup.py
# Para crear el ejecutable de Alfa mediaserver en windows
# Se usa py2exe
# Linea de comandos para la creacion:  python setup.py py2exe -p channels,servers,lib,platformcode
from distutils.core import setup
import glob
import py2exe

setup(
      packages=['channels','servers','lib','platformcode','platformcode/controllers','lib/urllib3','lib/urllib3/packages','lib/urllib3/util',
                'lib/requests',
                'lib/cloudscraper','lib/cloudscraper/interpreters','lib/cloudscraper/user_agent'
               ],
      data_files=[("channels",glob.glob("channels\\*.py")),
                  ("channels",glob.glob("channels\\*.json")),
                  ("servers",glob.glob("servers\\*.py")),
                  ("servers",glob.glob("servers\\*.json")),
                  ("",glob.glob("addon.xml")),
                 ],
      console=["alfa.py"]
      )

