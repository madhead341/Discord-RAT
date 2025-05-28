@echo off
echo Installing required Python packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Installation complete.
pause
