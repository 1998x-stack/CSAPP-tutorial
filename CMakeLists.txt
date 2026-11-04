cmake_minimum_required(VERSION 3.20)
project(CSAPPLabs VERSION 0.3.0 LANGUAGES C)

include(CTest)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_package(Threads REQUIRED)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

function(add_lab name source)
  add_executable(${name} ${source})
  if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(${name} PRIVATE -Wall -Wextra -Wpedantic -Werror)
  endif()
endfunction()

add_lab(lab_endianness labs/bit-operations/representation.c)
add_lab(lab_bit_math labs/bit-operations/bit_math.c)
add_lab(lab_matrix_layout labs/assembly/matrix_layout.c)
add_lab(lab_cache_geometry labs/cache/cache_geometry.c)
add_lab(lab_cache_sim labs/cache/cache_sim.c)
add_lab(lab_file_offset labs/processes/file_offset.c)
add_lab(lab_dynamic_array labs/memory/dynamic_array.c)
add_lab(lab_bounded_queue labs/concurrency/bounded_queue.c)
target_link_libraries(lab_bounded_queue PRIVATE Threads::Threads)

function(golden name target golden)
  add_test(NAME ${name}
    COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/check_case.py
      --expected ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/golden/${golden}
      -- "$<TARGET_FILE:${target}>" ${ARGN}
  )
  set_tests_properties(${name} PROPERTIES TIMEOUT 15)
endfunction()

golden(bit_math lab_bit_math bit_math.txt)
golden(matrix_layout lab_matrix_layout matrix_layout.txt)
golden(cache_geometry lab_cache_geometry cache_geometry.txt)
golden(cache_lru lab_cache_sim cache_lru.txt 4 2 4 ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/fixtures/lru.trace)
golden(cache_direct lab_cache_sim cache_direct.txt 2 1 2 ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/fixtures/direct.trace)
golden(file_offset lab_file_offset file_offset.txt)
golden(dynamic_array lab_dynamic_array dynamic_array.txt)
golden(bounded_queue lab_bounded_queue bounded_queue.txt)

# Repeat a concurrent workload to catch intermittent deadlocks and lost items.
add_test(NAME bounded_queue_stress
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/check_case.py
    --repeat 20
    --expected ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/golden/bounded_queue.txt
    -- "$<TARGET_FILE:lab_bounded_queue>"
)
set_tests_properties(bounded_queue_stress PROPERTIES TIMEOUT 60)


add_test(NAME cache_invalid_geometry
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/check_case.py
    --exit-code 2
    --expected ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/golden/cache_invalid_geometry.txt
    -- "$<TARGET_FILE:lab_cache_sim>" 3 1 2 ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/fixtures/direct.trace
)
add_test(NAME cache_invalid_trace
  COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/check_case.py
    --exit-code 2
    --expected ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/golden/cache_invalid_trace.txt
    -- "$<TARGET_FILE:lab_cache_sim>" 2 1 2 ${CMAKE_CURRENT_SOURCE_DIR}/tests/labs/fixtures/invalid.trace
)
add_test(NAME endian_smoke COMMAND lab_endianness)
set_tests_properties(endian_smoke PROPERTIES PASS_REGULAR_EXPRESSION "endianness=(little|big|other)" TIMEOUT 10)
