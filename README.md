# VXTrayTools
Windows Tray Tool to access specific folders and files

![screenshot](vxtt.png?raw=true)

Download executable ready build from:
https://github.com/ModdingClass/VXTrayTools/releases/

Extract somewhere and adjust the **_ini_** files to suit your configuration.



---

If you want to rebuild from sources, you need some requirements
```pip install configobj```

For building the exe package use something like:
```
pyinstaller --onedir -w VXtrayTools.py --icon icon_vx.ico --name VXtrayTools --runtime-hook add_libs.py
```

Move the files below in the _libs_ folder:
```
libcrypto-1_1.dll
libffi-7.dll
libssl-1_1.dll
mfc140u.dll
pyexpat.pyd
pywintypes39.dll
select.pyd
unicodedata.pyd
VCRUNTIME140.dll
win32api.pyd
win32gui.pyd
win32ui.pyd
winxpgui.pyd
_asyncio.pyd
_bz2.pyd
_ctypes.pyd
_decimal.pyd
_hashlib.pyd
_lzma.pyd
_multiprocessing.pyd
_overlapped.pyd
_queue.pyd
_socket.pyd
_ssl.pyd
_win32sysloader.pyd
```
Keep only files below near the executable (**don't move those in the libs folder!!!**):
```
base_library.zip
config_files.ini
config_folders.ini
config_main.ini
icon_console.ico
icon_files.ico
icon_folders.ico
icon_vx.ico
libs
python39.dll
VXtrayTools.exe
```

It is also possible to compile to a single file with _--onefile_ option, but in my testing the startup times is increased dramatically.
