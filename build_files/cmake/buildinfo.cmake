# This is called by cmake as an extermal process from
# ./source/creator/CMakeLists.txt to write ./source/creator/buildinfo.h

# Extract working copy information for SOURCE_DIR into MY_XXX variables
# with a default in case anything fails, for examble when using git-svn
set(MY_WC_HASH "")
set(MY_WC_BRANCH "")
set(MY_WC_CHANGE "unknown")

# Guess if this is a SVN working copy and then look up the revision
if(EXISTS ${SOURCE_DIR}/.git/)
	if(EXISTS ${SOURCE_DIR}/.git/)
		# The FindSubversion.cmake module is part of the standard distribution
		include(FindGit)
		if(GIT_FOUND)
			execute_process(COMMAND git rev-parse --short HEAD
			                WORKING_DIRECTORY ${SOURCE_DIR}
			                OUTPUT_VARIABLE MY_WC_HASH
			                OUTPUT_STRIP_TRAILING_WHITESPACE)

			execute_process(COMMAND git rev-parse --abbrev-ref HEAD
			                WORKING_DIRECTORY ${SOURCE_DIR}
			                OUTPUT_VARIABLE MY_WC_BRANCH
			                OUTPUT_STRIP_TRAILING_WHITESPACE)

			# Get latest version tag
			execute_process(COMMAND git describe --match "v[0-9]*" --abbrev=0
			                WORKING_DIRECTORY ${SOURCE_DIR}
			                OUTPUT_VARIABLE _git_latest_version_tag
			                OUTPUT_STRIP_TRAILING_WHITESPACE)

			if(NOT _git_latest_version_tag STREQUAL "")
				execute_process(COMMAND git rev-list HEAD ^${_git_latest_version_tag} --count
				                WORKING_DIRECTORY ${SOURCE_DIR}
				                OUTPUT_VARIABLE MY_WC_CHANGE
				                OUTPUT_STRIP_TRAILING_WHITESPACE)
			else()
				# For the time being we don't have annotated release tags,
				# count all the revisions in branch.
				execute_process(COMMAND git rev-list HEAD --count
				                WORKING_DIRECTORY ${SOURCE_DIR}
				                OUTPUT_VARIABLE MY_WC_CHANGE
				                OUTPUT_STRIP_TRAILING_WHITESPACE)
			endif()

			# Update GIT index before getting dirty files
			execute_process(COMMAND git update-index -q --refresh
			                WORKING_DIRECTORY ${SOURCE_DIR}
			                OUTPUT_STRIP_TRAILING_WHITESPACE)

			execute_process(COMMAND git diff-index --name-only HEAD --
			                WORKING_DIRECTORY ${SOURCE_DIR}
			                OUTPUT_VARIABLE _git_changed_files
			                OUTPUT_STRIP_TRAILING_WHITESPACE)

			if(NOT _git_changed_files STREQUAL "")
				set(MY_WC_CHANGE "${MY_WC_CHANGE}M")
			endif()

			unset(_git_changed_files)
			unset(_git_latest_version_tag)
		endif()
	endif()
else()
	# Some crazy folks like me could have hacked git-svn chekout in a way
	# so svnversion gives proper svn revision for themm which required having
	# empty .svn folder.
	#
	# For such a crazy blokes put svn check into an else branch.
	#
	#                                                              (sergey)
	if(EXISTS ${SOURCE_DIR}/.svn/)
		# The FindSubversion.cmake module is part of the standard distribution
		include(FindSubversion)

		if(Subversion_FOUND)
			Subversion_WC_INFO(${SOURCE_DIR} MY)
			set(MY_WC_CHANGE "${MY_WC_REVISION}")
		endif()
	endif()
endif()

# BUILD_PLATFORM and BUILD_PLATFORM are taken from CMake
# but BUILD_DATE and BUILD_TIME are plataform dependant
if(UNIX)
	execute_process(COMMAND date "+%Y-%m-%d" OUTPUT_VARIABLE BUILD_DATE OUTPUT_STRIP_TRAILING_WHITESPACE)
	execute_process(COMMAND date "+%H:%M:%S" OUTPUT_VARIABLE BUILD_TIME OUTPUT_STRIP_TRAILING_WHITESPACE)
endif()
if(WIN32)
	execute_process(COMMAND cmd /c date /t OUTPUT_VARIABLE BUILD_DATE OUTPUT_STRIP_TRAILING_WHITESPACE)
	execute_process(COMMAND cmd /c time /t OUTPUT_VARIABLE BUILD_TIME OUTPUT_STRIP_TRAILING_WHITESPACE)
endif()

# Write a file with the SVNVERSION define
file(WRITE buildinfo.h.txt
	"#define BUILD_HASH \"${MY_WC_HASH}\"\n"
	"#define BUILD_CHANGE \"${MY_WC_CHANGE}\"\n"
	"#define BUILD_BRANCH \"${MY_WC_BRANCH}\"\n"
	"#define BUILD_DATE \"${BUILD_DATE}\"\n"
	"#define BUILD_TIME \"${BUILD_TIME}\"\n"
)

# Copy the file to the final header only if the version changes
# and avoid needless rebuilds
# TODO: verify this comment is true, as BUILD_TIME probably changes
execute_process(COMMAND ${CMAKE_COMMAND} -E copy_if_different
                        buildinfo.h.txt buildinfo.h)
