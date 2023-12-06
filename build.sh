 #!/bin/sh
 pyinstaller --onedir --windowed \
 --add-data './images/background.jpg:images' \
 --add-data './images/folder.png:images' \
 --add-data './config.yml:.' \
 --noconfirm \
 --icon images/bird.png \
 o2eb.py
