 venv\scripts\activate
 pyinstaller --onedir --windowed ^
 --add-data 'images\background.jpg:images' ^
 --add-data 'images\folder.png:images' ^
 --noconfirm ^
 --icon images\bird.png ^
 --collect-submodules  'obs2ebird.py' ^
 --collect-submodules  'get_secrets.py' ^
 --hidden-import='PIL._tkinter_finder' ^
 o2eb.py
