@echo off
echo Starting Bforartists with the Vulkan backend

rem BFA - the executable is named bforartists
"%~dp0\bforartists" --gpu-backend vulkan
