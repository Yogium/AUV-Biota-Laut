# 1. Set the minimum version of CMake required
cmake_minimum_required(VERSION 3.10)

# 2. Name your project
project(AUV_Camera)

# 3. Tell CMake to go find the OpenCV library on your system
find_package(OpenCV REQUIRED)

# 4. Include the OpenCV header directories
include_directories(${OpenCV_INCLUDE_DIRS})

# 5. Tell CMake to create an executable from your C++ file
add_executable(dataAcquisition dataAcquisition.cpp)

# 6. Link the massive OpenCV libraries to your tiny executable
target_link_libraries(dataAcquisition ${OpenCV_LIBS})