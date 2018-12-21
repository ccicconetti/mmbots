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
#include <map>
#include <mutex>
#include <string>

using json   = nlohmann::json;
namespace po = boost::program_options;

class CoffeeTable
{
  NONCOPYABLE_NONMOVABLE(CoffeeTable);

 public:
  explicit CoffeeTable(const std::string& aPersistenceFile)
      : theMutex()
      , thePersistenceFile(aPersistenceFile)
      , theCoffees() {
    std::ifstream myFile(aPersistenceFile);
    if (myFile) {
      json myJson;
      myFile >> myJson;
      for (auto it = myJson.begin(); it != myJson.end(); ++it) {
        theCoffees[it.key()] = it.value().get<float>();
      }
      LOG(INFO) << "Loaded from " << aPersistenceFile << ": " << singleLine();

    } else {
      LOG(WARNING) << "Cannot read from persistence file at "
                   << aPersistenceFile;
    }
  }

  std::pair<bool, int> operator()(const std::string& aCustomer,
                                  const int          aDelta) {
    const std::lock_guard<std::mutex> myLock(theMutex);

    auto ret = theCoffees.insert({aCustomer, 0});
    if ((ret.first->second + aDelta) < 0) {
      return std::make_pair(false, 0);
    }
    ret.first->second += aDelta;
    serializeToDisk();
    return std::make_pair(true, ret.first->second);
  }

  void clear() {
    const std::lock_guard<std::mutex> myLock(theMutex);
    theCoffees.clear();
    serializeToDisk();
  }

  bool empty() const {
    const std::lock_guard<std::mutex> myLock(theMutex);
    return theCoffees.empty();
  }

  std::unordered_map<std::string, int> table() const {
    const std::lock_guard<std::mutex> myLock(theMutex);
    return theCoffees;
  }

 private:
  std::string singleLine() const {
    return toString(
        theCoffees, ",", [](const std::pair<std::string, int>& aPair) {
          return aPair.first + "|" + std::to_string(aPair.second);
        });
  }

  void serializeToDisk() {
    LOG(INFO) << "Current table: " << singleLine();
    std::ofstream myFile(thePersistenceFile);
    json          myJson(theCoffees);
    myFile << myJson;
  }

 private:
  mutable std::mutex                   theMutex;
  const std::string                    thePersistenceFile;
  std::unordered_map<std::string, int> theCoffees;
};

class CoffeeServer : public uiiit::rest::Server
{
  NONCOPYABLE_NONMOVABLE(CoffeeServer);

 public:
  explicit CoffeeServer(const std::string& aUri,
                        const std::string& aToken,
                        const std::string& aPersistenceFile)
      : uiiit::rest::Server(aUri)
      , theCoffeeTable(aPersistenceFile)
      , theToken(aToken) {
    (*this)(web::http::methods::POST,
            "(.*)",
            [this](web::http::http_request aReq) { handleCoffee(aReq); });
  }

 private:
  void handleCoffee(web::http::http_request aReq) {
    std::string myBody;
    aReq.extract_string()
        .then([&myBody](pplx::task<utility::string_t> aPrevTask) {
          myBody = aPrevTask.get();
        })
        .wait();
    LOG(INFO) << aReq.remote_address() << ' ' << myBody;

    // clang-format off
    static const std::string myHelp(
"Commands:\n"
"```/coffee 10```\n"
"You took 10 coffee tabs (can be negative to fix mistakes).\n"
"```/coffee show```\n"
"Show the current coffee table\n"
"```/coffee reset```\n"
"Clear the current coffee table\n"
"```/coffee help```\n"
"Show this help\n");
    // clang-format on
    const auto myPairs =
        uiiit::support::split<std::list<std::string>>(myBody, "&");
    auto        myAuthorized = false;
    std::string myText;
    std::string myUserName;
    for (const auto& myElem : myPairs) {
      const auto myPair =
          uiiit::support::split<std::list<std::string>>(myElem, "=");
      if (myPair.size() != 2) {
        continue;
      }
      if (myPair.front() == "token" and myPair.back() == theToken) {
        myAuthorized = true;
      } else if (myPair.front() == "user_name") {
        myUserName = myPair.back();
      } else if (myPair.front() == "text") {
        myText = myPair.back();
      }
    }

    auto myIsNumber = true;
    int  myNumber;
    try {
      myNumber = std::stoi(myText);
    } catch (...) {
      myIsNumber = false;
    }

    web::json::value myValue;
    if (not myUserName.empty() and myAuthorized) {
      if (myText == "help") {
        myValue["text"] = web::json::value(myHelp);

      } else if (myText == "reset") {
        theCoffeeTable.clear();
        myValue["response_type"] = web::json::value("in_channel");
        myValue["text"] = web::json::value("The coffee table has been cleared");

      } else if (myText == "show") {
        std::stringstream myStream;
        myStream << " | name  | coffees | \n"
                    " | -------- | ----------- |\n";
        auto myTot = 0;
        for (const auto& myPair : theCoffeeTable.table()) {
          myStream << " | " << myPair.first << " | " << myPair.second << " |\n";
          myTot += myPair.second;
        }
        myStream << " | **total** | " << myTot << " |\n";
        myValue["response_type"] = web::json::value("in_channel");
        myValue["text"]          = web::json::value(theCoffeeTable.empty() ?
                                               "There are no pending coffees" :
                                               myStream.str());

      } else if (myIsNumber) {
        const auto ret = theCoffeeTable(myUserName, myNumber);

        if (ret.first) {
          myValue["response_type"] = web::json::value("in_channel");
          myValue["text"] =
              web::json::value("Number of coffees of " + myUserName +
                               " updated to " + std::to_string(ret.second));
        } else {
          myValue["text"] = web::json::value("Update refused");
        }

      } else {
        myValue["text"] = web::json::value("invalid request: " + myText +
                                           "\ntry `/coffee help`");
      }
      aReq.reply(web::http::status_codes::OK, myValue);

    } else {
      LOG(WARNING) << "Unauthorized access from " << aReq.remote_address();
      aReq.reply(web::http::status_codes::Unauthorized, myValue);
    }
  }

 private:
  CoffeeTable       theCoffeeTable;
  const std::string theToken;
};

int main(int argc, char* argv[]) {
  uiiit::support::GlogRaii myGlogRaii(argv[0]);

  try {
    std::string             myPersistenceFile;
    po::options_description myDesc("Allowed options");
    // clang-format off
    myDesc.add_options()
    ("persistence-file",
     po::value<std::string>(&myPersistenceFile)->default_value("persistence.json"),
     "Path of the file where to read from/save to persistence.")
    ;
    // clang-format on
    uiiit::support::MmOptions myCli(argc, argv, myDesc);

    if (myCli.token().empty()) {
      throw std::runtime_error("Empty token");
    }

    CoffeeServer myServer(myCli.root(), myCli.token(), myPersistenceFile);
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
