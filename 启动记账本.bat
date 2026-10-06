@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 goto runpyw
goto runpy

:runpyw
for %%f in (*.py) do start "" pythonw "%%f"
goto end

:runpy
for %%f in (*.py) do python "%%f"
if errorlevel 1 pause

:end
