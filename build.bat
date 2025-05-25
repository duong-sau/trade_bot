@echo off
:: Build Bot.py
pyinstaller --onefile Bot.py

:: Build Main.py
pyinstaller --onefile Main.py

:: Build Price.py
pyinstaller --onefile Price.py

:: Build Websocket.py
pyinstaller --onefile Websocket.py
pause