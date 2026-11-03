@echo off
setlocal

REM NOTE: This assumes that the .venv is in the same directory as this batch script
call %~dp0\.venv\Scripts\activate.bat

spyder

endlocal