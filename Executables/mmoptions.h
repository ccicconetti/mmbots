#pragma once

#include "Support/clioptions.h"

namespace uiiit {
namespace support {

class MmOptions final : public CliOptions
{
 public:
  MmOptions(int                                          argc,
            char**                                       argv,
            boost::program_options::options_description& aDesc)
      : CliOptions(argc, argv, aDesc)
      , theRoot()
      , theToken() {
    // clang-format off
    theDesc.add_options()
    ("root",
     boost::program_options::value<std::string>(&theRoot)
       ->default_value("http://localhost:6500"),
     "Root of the HTTP server.")
    ("token",
     boost::program_options::value<std::string>(&theToken)
       ->default_value(""),
     "Use this token to validate Mattermost requests.")
    ;
    // clang-format on
    parse();
  }

  const std::string& root() const noexcept {
    return theRoot;
  }

  const std::string& token() const noexcept {
    return theToken;
  }

 private:
  std::string theRoot;
  std::string theToken;
};

} // namespace support
} // namespace uiiit
