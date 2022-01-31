cmake_minimum_required(VERSION 3.10)

include_directories(include)

set(CMAKE_BUILD_TYPE Debug)

add_library(lzload SHARED
  src/lzload.c
  )

target_link_libraries(lzload
  dl
  )

install(TARGETS lzload DESTINATION lib)

add_executable(lzload-test
  test/lzload-test.c
  )

target_link_libraries(lzload-test
  lzload
  )

add_executable(loading-test
  test/loading-test.c
  )

target_link_libraries(loading-test
  lzload
  )

add_executable(dlopen-test
  test/dlopen-test.c
  )

target_link_libraries(dlopen-test
  lzload
  )

add_executable(thread-test
  test/thread-test.c
  )

target_link_libraries(thread-test
  lzload
  pthread
  )
