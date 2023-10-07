/* SPDX-FileCopyrightText: 2013 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 * Declaration of GHOST_Context class.
 */

#pragma once

#include "GHOST_IContext.hh"
#include "GHOST_Types.h"

#include <cstdlib>  // for nullptr

class GHOST_Context : public GHOST_IContext {
 public:
  /**
   * Constructor.
   * \param stereoVisual: Stereo visual for quad buffered stereo.
   */
  GHOST_Context(bool stereoVisual) : m_stereoVisual(stereoVisual) {}

  /**
   * Destructor.
   */
  virtual ~GHOST_Context() {}

  /**
   * Swaps front and back buffers of a window.
   * \return A boolean success indicator.
   */
  virtual GHOST_TSuccess swapBuffers() override = 0;

  /**
   * Activates the drawing context of this window.
   * \return A boolean success indicator.
   */
  virtual GHOST_TSuccess activateDrawingContext() override = 0;

  /**
   * Release the drawing context of the calling thread.
   * \return A boolean success indicator.
   */
  virtual GHOST_TSuccess releaseDrawingContext() override = 0;

  /**
   * Call immediately after new to initialize.  If this fails then immediately delete the object.
   * \return Indication as to whether initialization has succeeded.
   */
  virtual GHOST_TSuccess initializeDrawingContext() = 0;

  /**
   * Updates the drawing context of this window. Needed
   * whenever the window is changed.
   * \return Indication of success.
   */
  virtual GHOST_TSuccess updateDrawingContext()
  {
    return GHOST_kFailure;
  }

  /**
   * Checks if it is OK for a remove the native display
   * \return Indication as to whether removal has succeeded.
   */
  virtual GHOST_TSuccess releaseNativeHandles() = 0;

  /**
   * Sets the swap interval for #swapBuffers.
   * \param interval: The swap interval to use.
   * \return A boolean success indicator.
   */
  virtual GHOST_TSuccess setSwapInterval(int /*interval*/)
  {
    return GHOST_kFailure;
  }

  /**
   * Gets the current swap interval for #swapBuffers.
   * \param intervalOut: Variable to store the swap interval if it can be read.
   * \return Whether the swap interval can be read.
   */
  virtual GHOST_TSuccess getSwapInterval(int &)
  {
    return GHOST_kFailure;
  }

  /**
   * Get user data.
   */
  void *getUserData()
  {
    return m_user_data;
  }

  /**
   * Set user data (intended for the caller to use as needed).
   */
  void setUserData(void *user_data)
  {
    m_user_data = user_data;
  }

  /**
   * Stereo visual created. Only necessary for 'real' stereo support,
   * ie quad buffered stereo. This is not always possible, depends on
   * the graphics h/w
   */
  inline bool isStereoVisual() const
  {
    return m_stereoVisual;
  }

  /**
   * Returns if the context is rendered upside down compared to OpenGL.
   */
  virtual inline bool isUpsideDown() const
  {
    return false;
  }

  /**
   * Gets the OpenGL frame-buffer associated with the OpenGL context
   * \return The ID of an OpenGL frame-buffer object.
   */
  virtual unsigned int getDefaultFramebuffer() override
  {
    return 0;
  }

#ifdef WITH_VULKAN_BACKEND
  /**
   * Get Vulkan handles for the given context.
   *
   * These handles are the same for a given context.
   * Should only be called when using a Vulkan context.
   * Other contexts will not return any handles and leave the
   * handles where the parameters are referring to unmodified.
   *
   * \param r_instance: After calling this function the VkInstance
   *     referenced by this parameter will contain the VKInstance handle
   *     of the context associated with the `context` parameter.
   * \param r_physical_device: After calling this function the VkPhysicalDevice
   *     referenced by this parameter will contain the VKPhysicalDevice handle
   *     of the context associated with the `context` parameter.
   * \param r_device: After calling this function the VkDevice
   *     referenced by this parameter will contain the VKDevice handle
   *     of the context associated with the `context` parameter.
   * \param r_graphic_queue_family: After calling this function the uint32_t
   *     referenced by this parameter will contain the graphic queue family id
   *     of the context associated with the `context` parameter.
   * \param r_queue: After calling this function the VkQueue
   *     referenced by this parameter will contain the VKQueue handle
   *     of the context associated with the `context` parameter.
   * \returns GHOST_kFailure when context isn't a Vulkan context.
   *     GHOST_kSuccess when the context is a Vulkan context and the
   *     handles have been set.
   */
  virtual GHOST_TSuccess getVulkanHandles(void * /*r_instance*/,
                                          void * /*r_physical_device*/,
                                          void * /*r_device*/,
                                          uint32_t * /*r_graphic_queue_family*/,
                                          void * /*r_queue*/) override
  {
    return GHOST_kFailure;
  };

  virtual GHOST_TSuccess getVulkanSwapChainFormat(
      GHOST_VulkanSwapChainData * /*r_swap_chain_data */) override
  {
    return GHOST_kFailure;
  }

  virtual GHOST_TSuccess setVulkanSwapBuffersCallbacks(
      std::function<void(const GHOST_VulkanSwapChainData *)> /*swap_buffers_pre_callback*/,
      std::function<void(void)> /*swap_buffers_post_callback*/) override
  {
    return GHOST_kFailure;
  }
#endif

 protected:
  bool m_stereoVisual;

  /** Caller specified, not for internal use. */
  void *m_user_data = nullptr;

#ifdef WITH_OPENGL_BACKEND
  static void initClearGL();
#endif

#ifdef WITH_CXX_GUARDEDALLOC
  MEM_CXX_CLASS_ALLOC_FUNCS("GHOST:GHOST_Context")
#endif
};

#ifdef _WIN32
bool win32_chk(bool result, const char *file = nullptr, int line = 0, const char *text = nullptr);
bool win32_silent_chk(bool result);

#  ifndef NDEBUG
#    define WIN32_CHK(x) win32_chk((x), __FILE__, __LINE__, #    x)
#  else
#    define WIN32_CHK(x) win32_chk(x)
#  endif

#  define WIN32_CHK_SILENT(x, silent) ((silent) ? win32_silent_chk(x) : WIN32_CHK(x))
#endif /* _WIN32 */
