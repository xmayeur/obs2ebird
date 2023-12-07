 #!/bin/sh
 pyinstaller --onedir --windowed \
 --add-data './images/background.jpg:images' \
 --add-data './images/folder.png:images' \
 --noconfirm \
 --icon images/bird.png \
 --collect-submodules  './obs2ebird.py' \
 --collect-submodules  './get_secrets.py' \
 o2eb.py
