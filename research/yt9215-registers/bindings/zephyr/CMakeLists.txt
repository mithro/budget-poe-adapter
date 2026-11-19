# SPDX-License-Identifier: Apache-2.0

if(CONFIG_YT921X)
  # The portable access library and the generated register header live in
  # the C binding next to this module.
  set(YT921X_C_DIR ${CMAKE_CURRENT_LIST_DIR}/../c)

  zephyr_include_directories(include ${YT921X_C_DIR})

  zephyr_library_named(yt921x)
  zephyr_library_sources(
    drivers/yt921x_zephyr.c
    ${YT921X_C_DIR}/yt921x.c
  )
endif()
