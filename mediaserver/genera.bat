REM Genera los archivos para el ejecutable en windows de Alfa Mediaserver
python setup.py py2exe -p channels,servers,lib,platformcode
xcopy lib dist\lib /y /s /i
xcopy platformcode dist\platformcode /y /s /i
xcopy resources dist\resources /y /s /i
