# Microsoft Developer Studio Project File - Name="RAS_openglrasterizer" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Static Library" 0x0104

CFG=RAS_openglrasterizer - Win32 Profile
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "RAS_openglrasterizer.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "RAS_openglrasterizer.mak" CFG="RAS_openglrasterizer - Win32 Profile"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "RAS_openglrasterizer - Win32 Release" (based on "Win32 (x86) Static Library")
!MESSAGE "RAS_openglrasterizer - Win32 Debug" (based on "Win32 (x86) Static Library")
!MESSAGE "RAS_openglrasterizer - Win32 MT DLL Debug" (based on "Win32 (x86) Static Library")
!MESSAGE "RAS_openglrasterizer - Win32 MT DLL Release" (based on "Win32 (x86) Static Library")
!MESSAGE "RAS_openglrasterizer - Win32 Profile" (based on "Win32 (x86) Static Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
RSC=rc.exe

!IF  "$(CFG)" == "RAS_openglrasterizer - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer"
# PROP Target_Dir ""
LINK32=link.exe -lib
# ADD BASE CPP /nologo /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_MBCS" /D "_LIB" /YX /FD /c
# ADD CPP /nologo /MT /W3 /GX /O2 /I "..\..\..\..\lib\windows\string\include" /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "NDEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /c
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo
# ADD LIB32 /nologo /out:"..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\RAS_openglrasterizer.lib"

!ELSEIF  "$(CFG)" == "RAS_openglrasterizer - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\debug"
# PROP Target_Dir ""
LINK32=link.exe -lib
# ADD BASE CPP /nologo /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_MBCS" /D "_LIB" /YX /FD /GZ /c
# ADD CPP /nologo /MTd /W3 /Gm /GX /Zi /Od /I "..\..\..\..\lib\windows\string\include" /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "_DEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /GZ /c
# SUBTRACT CPP /Fr
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo
# ADD LIB32 /nologo /out:"..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\debug\RAS_openglrasterizer.lib"

!ELSEIF  "$(CFG)" == "RAS_openglrasterizer - Win32 MT DLL Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "RAS_openglrasterizer___Win32_MT_DLL_Debug"
# PROP BASE Intermediate_Dir "RAS_openglrasterizer___Win32_MT_DLL_Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\mtdll_debug"
# PROP Intermediate_Dir "..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\mtdll_debug"
# PROP Target_Dir ""
LINK32=link.exe -lib
# ADD BASE CPP /nologo /Gm /GX /ZI /Od /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "_DEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /GZ /c
# ADD CPP /nologo /MDd /Gm /GX /ZI /Od /I "..\..\..\..\lib\windows\string\include" /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "_DEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /GZ /c
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo /out:"..\..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\debug\RAS_openglrasterizer.lib"
# ADD LIB32 /nologo

!ELSEIF  "$(CFG)" == "RAS_openglrasterizer - Win32 MT DLL Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "RAS_openglrasterizer___Win32_MT_DLL_Release"
# PROP BASE Intermediate_Dir "RAS_openglrasterizer___Win32_MT_DLL_Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\mtdll"
# PROP Intermediate_Dir "..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\mtdll"
# PROP Target_Dir ""
LINK32=link.exe -lib
# ADD BASE CPP /nologo /GX /O2 /I "..\..\..\..\source\kernel\gen_system" /I ".../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "NDEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /c
# ADD CPP /nologo /MD /GX /O2 /I "..\..\..\..\lib\windows\string\include" /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "NDEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /c
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo /out:"..\..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\RAS_openglrasterizer.lib"
# ADD LIB32 /nologo

!ELSEIF  "$(CFG)" == "RAS_openglrasterizer - Win32 Profile"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "RAS_openglrasterizer___Win32_Profile"
# PROP BASE Intermediate_Dir "RAS_openglrasterizer___Win32_Profile"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "RAS_openglrasterizer___Win32_Profile"
# PROP Intermediate_Dir "RAS_openglrasterizer___Win32_Profile"
# PROP Target_Dir ""
LINK32=link.exe -lib
# ADD BASE CPP /nologo /W3 /Gm /GX /ZI /Od /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "_DEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /GZ /c
# ADD CPP /nologo /W3 /Gm /GX /Zi /O2 /I "..\..\..\..\lib\windows\string\include" /I "..\..\..\..\source\kernel\gen_system" /I "../../../../lib/windows/moto/include" /I "..\..\..\..\source\gameengine\Rasterizer" /D "_DEBUG" /D "WIN32" /D "_MBCS" /D "_LIB" /YX /J /FD /c
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo /out:"..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\debug\RAS_openglrasterizer.lib"
# ADD LIB32 /nologo /out:"..\..\..\..\..\obj\windows\gameengine\rasterizer\openglrasterizer\profile\RAS_openglrasterizer.lib"

!ENDIF 

# Begin Target

# Name "RAS_openglrasterizer - Win32 Release"
# Name "RAS_openglrasterizer - Win32 Debug"
# Name "RAS_openglrasterizer - Win32 MT DLL Debug"
# Name "RAS_openglrasterizer - Win32 MT DLL Release"
# Name "RAS_openglrasterizer - Win32 Profile"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# Begin Source File

SOURCE=..\..\..\..\source\gameengine\Rasterizer\RAS_OpenGLRasterizer\RAS_CheckVertexArrays.cpp
# End Source File
# Begin Source File

SOURCE=..\..\..\..\source\gameengine\Rasterizer\RAS_OpenGLRasterizer\RAS_OpenGLRasterizer.cpp
# End Source File
# Begin Source File

SOURCE=..\..\..\..\source\gameengine\Rasterizer\RAS_OpenGLRasterizer\RAS_VAOpenGLRasterizer.cpp
# End Source File
# End Group
# Begin Group "Header Files"

# PROP Default_Filter "h;hpp;hxx;hm;inl"
# Begin Source File

SOURCE=..\..\..\..\source\gameengine\Rasterizer\RAS_OpenGLRasterizer\RAS_CheckVertexArrays.h
# End Source File
# Begin Source File

SOURCE=..\..\..\..\source\gameengine\Rasterizer\RAS_OpenGLRasterizer\RAS_OpenGLRasterizer.h
# End Source File
# Begin Source File

SOURCE=..\..\..\..\source\gameengine\Rasterizer\RAS_OpenGLRasterizer\RAS_VAOpenGLRasterizer.h
# End Source File
# End Group
# End Target
# End Project
