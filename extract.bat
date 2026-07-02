@echo off
set PY=python
where python >nul 2>&1 || set PY=python3
where %PY% >nul 2>&1 || set PY=python3.14
where %PY% >nul 2>&1 || (echo [Error] Python not found & pause & exit /b 1)
if not "%~1"=="" ("%PY%" "%~dp0launcher.py" "%~1") else ("%PY%" "%~dp0launcher.py")
