 #!/bin/sh
 pyinstaller --onedir --windowed \
 --add-data './images/background.jpg:images' \
 --add-data './images/folder.png:images' \
 --noconfirm \
 --icon images/bird.png \
 o2eb.py
