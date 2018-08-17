REM Genera los archivos para el ejecutable en windows de Alfa Mediaserver
REM Y tambien genera el zip para Mediaserver
REM Los 2 los genera en la raiz del disco
winrar a -r \Alfa-Mediaserver-.zip \plugin.video.alfa\
python setup.py py2exe -p channels,servers,lib,platformcode
xcopy lib dist\lib /y /s /i
xcopy platformcode dist\platformcode /y /s /i
xcopy resources dist\resources /y /s /i
winrar a -ep1 -r -iiconplatformcode\template\favicon.ico -sfx -zdatos.txt \Alfa-Mediaserver--win dist\
