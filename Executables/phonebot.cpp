#include "Rest/server.h"
#include "Support/glograii.h"
#include "Support/macros.h"
#include "Support/mmtable.h"
#include "Support/split.h"

#include "mmoptions.h"

#include <glog/logging.h>

#include <nlohmann/json.hpp>

#include <boost/algorithm/string.hpp>
#include <boost/program_options.hpp>

#include <algorithm>
#include <fstream>
#include <list>
#include <sstream>
#include <string>

namespace po = boost::program_options;

class PhoneServer : public uiiit::rest::Server
{
  NONCOPYABLE_NONMOVABLE(PhoneServer);

 public:
  explicit PhoneServer(const std::string& aUri,
                       const std::string& aToken,
                       const std::string& aInputFile)
      : uiiit::rest::Server(aUri)
      , theToken(aToken)
      , theNumbers() {
    // load input file, throw if errors
    std::ifstream myInput(aInputFile);
    if (not myInput) {
      throw std::runtime_error("Could not open file " + aInputFile);
    }
    std::string myLine;
    size_t      myLineCnt = 0;
    while (not myInput.eof()) {
      myLineCnt++;
      std::getline(myInput, myLine);
      const auto myRecords =
          uiiit::support::split<std::vector<std::string>>(myLine, "\t");

      // skip invalid lines
      if (myRecords.size() != 3) {
        VLOG(1) << "Invalid input at line " << myLineCnt;
        continue;
      }
      theNumbers[myRecords.at(0)] = myRecords.at(2);
    }

    if (theNumbers.empty()) {
      throw std::runtime_error("No records found in file " + aInputFile);
    }

    LOG(INFO) << "Found " << theNumbers.size() << " numbers";
    for (const auto& elem : theNumbers) {
      VLOG(1) << elem.first << ' ' << elem.second;
    }

    // register REST handlers
    (*this)(web::http::methods::POST,
            "(.*)",
            [this](web::http::http_request aReq) { handleNumber(aReq); });
  }

 private:
  void handleNumber(web::http::http_request aReq) {
    std::string myBody;
    aReq.extract_string()
        .then([&myBody](pplx::task<utility::string_t> aPrevTask) {
          myBody = aPrevTask.get();
        })
        .wait();
    LOG(INFO) << aReq.remote_address() << ' ' << myBody;

    // clang-format off
    static const std::string myHelp(
"This command allows you to search a phone directory, for instance `/phone Bob` returns the phone number of all persons whose name contains Bob in the directory.\n");
    // clang-format on
    const auto myPairs =
        uiiit::support::split<std::list<std::string>>(myBody, "&");
    auto        myAuthorized    = false;
    auto        myValid         = true;
    auto        myHelpRequested = false;
    std::string myText;
    std::string myName;
    for (const auto& myElem : myPairs) {
      const auto myPair =
          uiiit::support::split<std::list<std::string>>(myElem, "=");
      if (myPair.size() != 2) {
        continue;
      }
      if (myPair.front() == "token" and myPair.back() == theToken) {
        myAuthorized = true;
      } else if (myPair.front() == "text") {
        myText = myPair.back();

        if (myText.empty() or myText == "help") {
          myHelpRequested = true;
          continue;
        }
        myName =
            uiiit::support::split<std::list<std::string>>(myPair.back(), "+")
                .front();
        std::transform(myName.begin(), myName.end(), myName.begin(), ::tolower);
      }
    }

    web::json::value myValue;
    if (myAuthorized) {
      if (myHelpRequested) {
        myValue["text"] = web::json::value(myHelp);

      } else if (myValid) {
        uiiit::support::MmTable myTable(2);

        // add table header
        myTable(0, 0, "Person");
        myTable(0, 1, "Number");

        // add all numbers found
        size_t myRow = 1;
        for (const auto& elem : theNumbers) {
          auto myLowerKey = elem.first;
          std::transform(myLowerKey.begin(),
                         myLowerKey.end(),
                         myLowerKey.begin(),
                         ::tolower);
          if (myLowerKey.find(myName) != std::string::npos) {
            myTable(myRow, 0, elem.first);
            myTable(myRow++, 1, elem.second);
          }
        }

        myValue["response_type"] = web::json::value("in_channel");
        myValue["text"]          = web::json::value(myTable.toString());
      } else {
        myValue["text"] = web::json::value("invalid request: " + myText +
                                           "\ntry `/sushi help`");
      }
      aReq.reply(web::http::status_codes::OK, myValue);

    } else {
      LOG(WARNING) << "Unauthorized access from " << aReq.remote_address();
      aReq.reply(web::http::status_codes::Unauthorized, myValue);
    }
  }

 private:
  const std::string                            theToken;
  std::unordered_map<std::string, std::string> theNumbers;
};

int main(int argc, char* argv[]) {
  uiiit::support::GlogRaii myGlogRaii(argv[0]);

  try {
    std::string             myInputFile;
    po::options_description myDesc("Allowed options");
    // clang-format off
    myDesc.add_options()
    ("input-file",
     boost::program_options::value<std::string>(&myInputFile)
       ->default_value(""),
     "Input file, 3 columns tab-separated.")
    ;
    // clang-format on

    uiiit::support::MmOptions myCli(argc, argv, myDesc);

    if (myCli.token().empty()) {
      throw std::runtime_error("Empty token");
    }

    PhoneServer myServer(myCli.root(), myCli.token(), myInputFile);
    myServer.start();
    pause();

    return EXIT_SUCCESS;
  } catch (const uiiit::support::CliExit&) {
    return EXIT_SUCCESS; // clean exit
  } catch (const std::exception& aErr) {
    LOG(ERROR) << "Exception caught: " << aErr.what();
  } catch (...) {
    LOG(ERROR) << "Unknown exception caught";
  }

  return EXIT_FAILURE;
}
