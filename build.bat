@echo off
setlocal
set BLENDER="C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
if not exist %BLENDER% (
  echo Blender 5.1 not found at %BLENDER%
  exit /b 1
)
%BLENDER% --background --python "%~dp0blender\build_lab.py"
