set BUILD_DIR=%BLENDER_DIR%..\build_windows
set BUILD_TYPE=Release
:argv_loop
if NOT "%1" == "" (

	REM Help Message
	if "%1" == "help" (
		set SHOW_HELP=1
		goto EOF
	)
	REM Build Types
	if "%1" == "debug" (
		set BUILD_TYPE=Debug
	REM Build Configurations
	) else if "%1" == "noge" (
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -DWITH_GAMEENGINE=OFF -DWITH_PLAYER=OFF
		set BUILD_NGE=_noge
	) else if "%1" == "builddir" (
		set BUILD_DIR_OVERRRIDE="%BLENDER_DIR%..\%2"
		shift /1
	) else if "%1" == "with_tests" (
		set TESTS_CMAKE_ARGS=-DWITH_GTESTS=On
	) else if "%1" == "full" (
		set TARGET=Full
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% ^
		    -C"%BLENDER_DIR%\build_files\cmake\config\blender_full.cmake"
	) else if "%1" == "lite" (
		set TARGET=Lite
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -C"%BLENDER_DIR%\build_files\cmake\config\blender_lite.cmake"
	) else if "%1" == "cycles" (
		set TARGET=Cycles
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -C"%BLENDER_DIR%\build_files\cmake\config\cycles_standalone.cmake"
	) else if "%1" == "headless" (
		set TARGET=Headless
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -C"%BLENDER_DIR%\build_files\cmake\config\blender_headless.cmake"
	) else if "%1" == "bpy" (
		set TARGET=Bpy
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -C"%BLENDER_DIR%\build_files\cmake\config\bpy_module.cmake"
	) else if "%1" == "clang" (
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS%
		set WITH_CLANG=1
	) else if "%1" == "release" (
		set TARGET=Release
	) else if "%1" == "x86" (
		set BUILD_ARCH=x86
	) else if "%1" == "x64" (
		set BUILD_ARCH=x64
	) else if "%1" == "2017" (
		set BUILD_VS_YEAR=2017
	) else if "%1" == "2017pre" (
		set BUILD_VS_YEAR=2017
		set VSWHERE_ARGS=-prerelease
	) else if "%1" == "2015" (
		set BUILD_VS_YEAR=2015
	) else if "%1" == "2013" (
		set BUILD_VS_YEAR=2013
	) else if "%1" == "packagename" (
		set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -DCPACK_OVERRIDE_PACKAGENAME="%2"
		shift /1
	) else if "%1" == "nobuild" (
		set NOBUILD=1
	) else if "%1" == "showhash" (
		SET BUILD_SHOW_HASHES=1
	REM Non-Build Commands
	) else if "%1" == "update" (
		SET BUILD_UPDATE=1
	) else if "%1" == "ninja" (
		SET BUILD_WITH_NINJA=1
	) else if "%1" == "clean" (
		set MUST_CLEAN=1
	) else if "%1" == "verbose" (
		set VERBOSE=1
	) else (
		echo Command "%1" unknown, aborting!
		exit /b 1
	)
	shift /1
	goto argv_loop
)
:EOF
exit /b 0