#ifndef CONFIG_H_
#define CONFIG_H_

/* Workaround a bug in boost 1.68, until we upgrade to a newer version. */
#if defined(__clang__) && defined(WIN32)
  #include <boost/type_traits/is_assignable.hpp>
  using namespace boost;
#endif
// Move settings to cmake to make CMake happy :)

// #define WITH_SCALE
// #define WITH_CUDA

const int GRAIN_SIZE = 1024;

#ifdef LOG_OUTPUT

#define lprintf(...) printf(__VA_ARGS__)
#define lputs(...) puts(__VA_ARGS__)

#else

#define lprintf(...) void(0)
#define lputs(...) void(0)

#endif

#include <chrono>

namespace qflow {

// simulation of Windows GetTickCount()
unsigned long long inline GetCurrentTime64() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count();
}
} // namespace qflow

#endif
