set BUILD_GENERATOR_POST=
set BUILD_PLATFORM_SELECT=
set MSBUILD_PLATFORM=x64

if "%BUILD_WITH_SCCACHE%"=="1" (
		echo sccache is only supported with ninja as the build system. 
		exit /b 1 
)

if "%WITH_CLANG%"=="1" (
	REM We want to use an external manifest with Clang
	set CLANG_CMAKE_ARGS=-T"ClangCl" -DWITH_WINDOWS_EXTERNAL_MANIFEST=ON 

	REM Create the build directory, so that we can create the Directory.build.props file
	if NOT EXIST %BUILD_DIR%\nul (
		mkdir %BUILD_DIR%
	)

	REM This is required as per https://learn.microsoft.com/en-us/cpp/build/clang-support-msbuild?view=msvc-170#custom_llvm_location
	REM Which allows any copy of LLVM to be used, not just the one that ships with VS
	echo ^<Project^> >> %BUILD_DIR%\Directory.build.props
	echo   ^<PropertyGroup^> >> %BUILD_DIR%\Directory.build.props
	echo     ^<LLVMInstallDir^>%LLVM_DIR%^</LLVMInstallDir^> >> %BUILD_DIR%\Directory.build.props
	echo     ^<LLVMToolsVersion^>%CLANG_VERSION%^</LLVMToolsVersion^> >> %BUILD_DIR%\Directory.build.props
	echo   ^</PropertyGroup^> >> %BUILD_DIR%\Directory.build.props
	echo ^</Project^> >> %BUILD_DIR%\Directory.build.props
)

if "%WITH_ASAN%"=="1" (
		set ASAN_CMAKE_ARGS=-DWITH_COMPILER_ASAN=On
)

if "%WITH_PYDEBUG%"=="1" (
	set PYDEBUG_CMAKE_ARGS=-DWINDOWS_PYTHON_DEBUG=On
)

if "%BUILD_ARCH%"=="arm64" (
	set MSBUILD_PLATFORM=arm64
	set BUILD_PLATFORM_SELECT=-A ARM64
)

set BUILD_CMAKE_ARGS=%BUILD_CMAKE_ARGS% -G "Visual Studio %BUILD_VS_VER% %BUILD_VS_YEAR%%BUILD_GENERATOR_POST%" %BUILD_PLATFORM_SELECT% %TESTS_CMAKE_ARGS% %CLANG_CMAKE_ARGS% %ASAN_CMAKE_ARGS% %PYDEBUG_CMAKE_ARGS%

if NOT EXIST %BUILD_DIR%\nul (
	mkdir %BUILD_DIR%
)

if "%MUST_CLEAN%"=="1" (
	echo Cleaning %BUILD_DIR%
	msbuild ^
		%BUILD_DIR%\Bforartists.sln ^
		/target:clean ^
		/property:Configuration=%BUILD_TYPE% ^
		/verbosity:minimal ^
		/p:platform=%MSBUILD_PLATFORM%
)

if NOT EXIST %BUILD_DIR%\Bforartists.sln set MUST_CONFIGURE=1
if "%NOBUILD%"=="1" set MUST_CONFIGURE=1

if "%MUST_CONFIGURE%"=="1" (

	if NOT "%verbose%" == "" (
		echo "%CMAKE% %BUILD_CMAKE_ARGS% -H%BLENDER_DIR% -B%BUILD_DIR%"
	)

	cmake ^
		%BUILD_CMAKE_ARGS% ^
		-H%BLENDER_DIR% ^
		-B%BUILD_DIR% 
	
	if errorlevel 1 (
		echo "Configuration Failed"
		exit /b 1
	)
)
echo echo off > %BUILD_DIR%\rebuild.cmd
echo if "%%VSCMD_VER%%" == "" ^( >> %BUILD_DIR%\rebuild.cmd
echo   call "%VCVARS%" %BUILD_ARCH% >> %BUILD_DIR%\rebuild.cmd
echo ^) >> %BUILD_DIR%\rebuild.cmd
echo "%CMAKE%" . >> %BUILD_DIR%\rebuild.cmd
echo echo %%TIME%% ^> buildtime.txt >> %BUILD_DIR%\rebuild.cmd
echo msbuild ^
	%BUILD_DIR%\INSTALL.vcxproj ^
	/property:Configuration=%BUILD_TYPE% ^
	/maxcpucount:2 ^
	/verbosity:minimal ^
	/p:platform=%MSBUILD_PLATFORM% ^
	/flp:Summary;Verbosity=minimal;LogFile=%BUILD_DIR%\Build.log >> %BUILD_DIR%\rebuild.cmd
echo echo %%TIME%% ^>^> buildtime.txt >> %BUILD_DIR%\rebuild.cmd
