# VXTrayTools
Windows Tray Tool to access specific folders and files



If you want to rebuild from sources, you need some requirements
```pip install configobj```

For building the exe package use something like:
```pyinstaller --onedir -w VXtrayTools.py --icon icon_vx.ico --name VXtrayTools --runtime-hook add_libs.py```

It is also possible to compile to a single file with _--onefile_ option, but in my testing the startup times is increased dramatically.