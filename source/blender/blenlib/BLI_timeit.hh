/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#ifndef __BLI_TIMEIT_HH__
#define __BLI_TIMEIT_HH__

#include <chrono>
#include <iostream>
#include <string>

#include "BLI_sys_types.h"

namespace blender {
namespace Timeit {

using Clock = std::chrono::steady_clock;
using TimePoint = Clock::time_point;
using Nanoseconds = std::chrono::nanoseconds;

void print_duration(Nanoseconds duration);

class ScopedTimer {
 private:
  std::string m_name;
  TimePoint m_start;

 public:
  ScopedTimer(std::string name) : m_name(std::move(name))
  {
    m_start = Clock::now();
  }

  ~ScopedTimer()
  {
    TimePoint end = Clock::now();
    Nanoseconds duration = end - m_start;

    std::cout << "Timer '" << m_name << "' took ";
    print_duration(duration);
    std::cout << '\n';
  }
};

}  // namespace Timeit
}  // namespace blender

#define SCOPED_TIMER(name) blender::Timeit::ScopedTimer scoped_timer(name)

#endif /* __BLI_TIMEIT_HH__ */
