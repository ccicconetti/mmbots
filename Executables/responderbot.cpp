/*
 ___ ___ __     __ ____________
|   |   |  |   |__|__|__   ___/  Ubiquitout Internet @ IIT-CNR
|   |   |  |  /__/  /  /  /      Mattermost bots
|   |   |  |/__/  /   /  /       Examples to show usage of uiiit::rest
|_______|__|__/__/   /__/        https://github.com/ccicconetti/mmbots/

Licensed under the MIT License <http://opensource.org/licenses/MIT>.
Copyright (c) 2019 Claudio Cicconetti https://ccicconetti.github.io/

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

#include "Rest/server.h"
#include "Support/glograii.h"
#include "Support/macros.h"
#include "Support/split.h"
#include "Support/tostring.h"

#include "mmoptions.h"

#include <glog/logging.h>

#include <nlohmann/json.hpp>

#include <boost/algorithm/string.hpp>
#include <boost/program_options.hpp>

#include <list>
#include <set>
#include <string>

using json   = nlohmann::json;
namespace po = boost::program_options;

/**
 * Example JSON file:
 *
 * <pre>

  [{
    "name": "set1",
    "prio": 0,
    "keywords": [
      "first-key", "second-key"
    ],
    "response": "This is a fixed response"
  }, {
    "name": "set2",
    "prio": 1,
    "keywords": [
      "another-key"
    ],
    "response": "User said %keyword%!"
  }]

 * </pre>
 */
class ResponderTable
{
  NONCOPYABLE_NONMOVABLE(ResponderTable);

  struct Desc {
    bool operator<(const Desc& aAnother) const noexcept {
      return thePrio < aAnother.thePrio;
    }

    std::string match(const std::string& aKeyword) const {
      if (theKeywords.find(aKeyword) == theKeywords.end()) {
        return std::string();
      }
      auto myRet = theResponse;
      boost::replace_all(myRet, "%keyword%", aKeyword);
      return myRet;
    }

    std::string toString() const {
      std::stringstream myStream;
      myStream << theName << " (" << thePrio << ") {"
               << ::toString(theKeywords, ",") << "} -> " << theResponse;
      return myStream.str();
    }

    int                   thePrio;
    std::string           theName;
    std::string           theResponse;
    std::set<std::string> theKeywords;
  };

 public:
  explicit ResponderTable(const std::string& aConfFile)
      : theDescs() {
    std::ifstream myFile(aConfFile);
    if (myFile) {
      json myJson;
      myFile >> myJson;
      for (auto it = myJson.begin(); it != myJson.end(); ++it) {
        const auto& myDescJson = it.value();
        Desc        myDesc;
        myDesc.theName     = myDescJson["name"].get<std::string>();
        myDesc.thePrio     = myDescJson["prio"].get<int>();
        myDesc.theResponse = myDescJson["response"].get<std::string>();
        for (const auto myKeyword : myDescJson["keywords"]) {
          myDesc.theKeywords.insert(
              boost::algorithm::to_upper_copy(myKeyword.get<std::string>()));
        }
        LOG(INFO) << myDesc.toString();
        theDescs.emplace(std::move(myDesc));
      }

    } else {
      throw std::runtime_error("Cannot read from configuration file at " +
                               aConfFile);
    }
  }

  std::string operator()(const std::string& aText) const {
    std::string myText;
    for (const auto& myChar : aText) {
      if (std::isspace(myChar)) {
        myText.push_back(' ');
      } else if (std::isalnum(myChar)) {
        myText.push_back(std::toupper(myChar));
      }
    }
    for (const auto myKeyword :
         uiiit::support::split<std::list<std::string>>(myText, " ")) {
      LOG(INFO) << myKeyword;
      for (const auto& myDesc : theDescs) {
        const auto myResp = myDesc.match(myKeyword);
        if (not myResp.empty()) {
          return myResp;
        }
      }
    }
    return std::string();
  }

 private:
  std::set<Desc> theDescs;
};

class ResponderServer : public uiiit::rest::Server
{
  NONCOPYABLE_NONMOVABLE(ResponderServer);

 public:
  explicit ResponderServer(const std::string& aUri,
                           const std::string& aToken,
                           const std::string& aConfFile)
      : uiiit::rest::Server(aUri)
      , theResponderTable(aConfFile)
      , theToken(aToken) {
    (*this)(web::http::methods::POST,
            "(.*)",
            [this](web::http::http_request aReq) { handleCoffee(aReq); });
  }

 private:
  void handleCoffee(web::http::http_request aReq) {
    web::json::value myBody;
    aReq.extract_string()
        .then([&myBody](pplx::task<utility::string_t> aPrevTask) {
          myBody = web::json::value::parse(aPrevTask.get());
        })
        .wait();
    VLOG(1) << aReq.remote_address() << ' ' << myBody;

    web::json::value myValue;
    if (myBody["token"].as_string() == theToken) {
      const auto myResp = theResponderTable(myBody["text"].as_string());
      if (not myResp.empty()) {
        myValue["text"] = web::json::value(myResp);
        VLOG(1) << myResp;
      }
      aReq.reply(web::http::status_codes::OK, myValue);

    } else {
      LOG(WARNING) << "Unauthorized access from " << aReq.remote_address();
      myValue["text"] = web::json::value("Invalid token");
      aReq.reply(web::http::status_codes::Unauthorized, myValue);
    }
  }

 private:
  ResponderTable    theResponderTable;
  const std::string theToken;
};

int main(int argc, char* argv[]) {
  uiiit::support::GlogRaii myGlogRaii(argv[0]);

  try {
    std::string             myConfFile;
    po::options_description myDesc("Allowed options");
    // clang-format off
    myDesc.add_options()
    ("conf",
     po::value<std::string>(&myConfFile)->default_value("conf.json"),
     "Path of the file where to read configuration in JSON format.")
    ;
    // clang-format on
    uiiit::support::MmOptions myCli(argc, argv, myDesc);

    if (myCli.token().empty()) {
      throw std::runtime_error("Empty token");
    }

    ResponderServer myServer(myCli.root(), myCli.token(), myConfFile);
    myServer.start();
    pause();

    return EXIT_SUCCESS;
  } catch (const std::exception& aErr) {
    LOG(ERROR) << "Exception caught: " << aErr.what();
  } catch (...) {
    LOG(ERROR) << "Unknown exception caught";
  }

  return EXIT_FAILURE;
}
