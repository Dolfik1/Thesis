cmake_minimum_required(VERSION 3.11)
project(mailru_data_converter)
include(FetchContent)

set(CMAKE_CXX_STANDARD 17)

FetchContent_Declare(
  yajl
  GIT_REPOSITORY https://github.com/lloyd/yajl.git
)

FetchContent_GetProperties(yajl)
if(NOT yajl_POPULATED)
  FetchContent_Populate(yajl)
  add_subdirectory(${yajl_SOURCE_DIR} ${yajl_BINARY_DIR})
endif()

FetchContent_GetProperties(dirent)
if(NOT yajl_POPULATED)
  FetchContent_Populate(dirent)
  add_subdirectory(${dirent_SOURCE_DIR} ${dirent_BINARY_DIR})
endif()

add_executable(mailru_data_converter src/main.c src/process.c)

target_include_directories(mailru_data_converter PRIVATE ${yajl_BINARY_DIR}/yajl-2.1.1/include)
target_link_libraries(mailru_data_converter yajl_s)