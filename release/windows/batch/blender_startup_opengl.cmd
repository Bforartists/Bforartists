@echo off
echo Starting Bforartists with the OpenGL backend

rem BFA - the executable is named bforartists
"%~dp0\bforartists" --gpu-backend opengl
