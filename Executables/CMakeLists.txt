add_executable(sushibot
  ${CMAKE_CURRENT_SOURCE_DIR}/sushibot.cpp
)

target_link_libraries(sushibot
  uiiitrest
  uiiitsupport
  ${GLOG}
  ${Boost_LIBRARIES}
)

add_executable(coffeebot
  ${CMAKE_CURRENT_SOURCE_DIR}/coffeebot.cpp
)

target_link_libraries(coffeebot
  uiiitrest
  uiiitsupport
  ${GLOG}
  ${Boost_LIBRARIES}
)

add_executable(phonebot
  ${CMAKE_CURRENT_SOURCE_DIR}/phonebot.cpp
)

target_link_libraries(phonebot
  uiiitrest
  uiiitsupport
  ${GLOG}
  ${Boost_LIBRARIES}
)

add_executable(responderbot
  ${CMAKE_CURRENT_SOURCE_DIR}/responderbot.cpp
)

target_link_libraries(responderbot
  uiiitrest
  uiiitsupport
  ${GLOG}
  ${Boost_LIBRARIES}
)

