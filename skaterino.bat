@echo off
rem Drag a .blend or .glb map onto this file. Finds Blender in the usual place; edit BLENDER if yours differs.
set "BLENDER="
for /d %%D in ("C:\Program Files\Blender Foundation\Blender *") do set "BLENDER=%%~D\blender.exe"
if "%BLENDER%"=="" echo Blender was not found under C:\Program Files\Blender Foundation. Edit this .bat. & pause & exit /b 1
if "%~1"=="" echo Drag a .blend or .glb map onto this file. & pause & exit /b 1
"%BLENDER%" --background --factory-startup --python "%~dp0skaterino.py" -- "%~f1" %2 %3
pause
