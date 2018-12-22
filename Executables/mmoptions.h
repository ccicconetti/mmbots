/*
Licensed under the MIT License <http://opensource.org/licenses/MIT>.
Copyright (c) 2018 Claudio Cicconetti <https://about.me/ccicconetti>

Permission is hereby  granted, free of charge, to any  person obtaining a copy
of this software and associated  documentation files (the "Software"), to deal
in the Software  without restriction, including without  limitation the rights
to  use, copy,  modify, merge,  publish, distribute,  sublicense, and/or  sell
copies  of  the Software,  and  to  permit persons  to  whom  the Software  is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE  IS PROVIDED "AS  IS", WITHOUT WARRANTY  OF ANY KIND,  EXPRESS OR
IMPLIED,  INCLUDING BUT  NOT  LIMITED TO  THE  WARRANTIES OF  MERCHANTABILITY,
FITNESS FOR  A PARTICULAR PURPOSE AND  NONINFRINGEMENT. IN NO EVENT  SHALL THE
AUTHORS  OR COPYRIGHT  HOLDERS  BE  LIABLE FOR  ANY  CLAIM,  DAMAGES OR  OTHER
LIABILITY, WHETHER IN AN ACTION OF  CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE  OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

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
