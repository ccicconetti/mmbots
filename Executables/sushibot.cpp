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

#include <list>
#include <sstream>
#include <string>

namespace po = boost::program_options;

class SushiServer : public uiiit::rest::Server
{
  NONCOPYABLE_NONMOVABLE(SushiServer);

 public:
  explicit SushiServer(const std::string& aUri, const std::string& aToken)
      : uiiit::rest::Server(aUri)
      , theToken(aToken) {
    (*this)(web::http::methods::POST,
            "(.*)",
            [this](web::http::http_request aReq) { handleSushi(aReq); });
  }

 private:
  void handleSushi(web::http::http_request aReq) {
    std::string myBody;
    aReq.extract_string()
        .then([&myBody](pplx::task<utility::string_t> aPrevTask) {
          myBody = aPrevTask.get();
        })
        .wait();
    LOG(INFO) << aReq.remote_address() << ' ' << myBody;

    // clang-format off
    static const std::string myHelp(
"This command allows you to split a discount on a shared cost, with optional delivery fee:\n"
"Examples:\n"
"```/sushi Alice 10 Bob 5 discount 0.2```\n"
"applies a discount of 20\% so that Alice will have to pay 8 and Bob 4\n"
"```/sushi Alice 10 Bob 5 discount 0.2 delivery 2```\n"
"same as before but the delivery cost is split evenly between Alice and Bob, who pay 9 and 5, respectively.\n"
"Note that `discount` and `delivery` are keywords. Order of pairs does not matter, so the last command is equivalent to:\n"
"```/sushi delivery 2 Bob 5 discount 0.2 Alice 10```\n"
"You may also let the bot do the sum for you, for instance the command above is equivalent to:\n"
"```/sushi delivery 2 Bob 1 1 3 discount 0.2 Alice 1.5 8.5```"
);
    // clang-format on
    const auto myPairs =
        uiiit::support::split<std::list<std::string>>(myBody, "&");
    auto                         myAuthorized    = false;
    auto                         myValid         = true;
    auto                         myHelpRequested = false;
    auto                         myDiscount      = 0.0f;
    auto                         myDelivery      = 0.0f;
    std::string                  myText;
    std::map<std::string, float> myPayments;
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

        if (myText == "help") {
          myHelpRequested = true;
          continue;
        }
        std::string myLastPayer;
        for (const auto& myElem : uiiit::support::split<std::list<std::string>>(
                 myPair.back(), "+")) {
          try {
            const auto myNumber = std::stof(myElem);

            // there cannot be a number in the first position
            if (myLastPayer.empty()) {
              myValid = false;
              break;
            }

            // it is a number
            myPayments[myLastPayer] += myNumber;
          } catch (...) {
            // not a number
            myPayments.insert({myElem, 0.0f});
            myLastPayer = myElem;
          }
        }
      }
    }

    // search for the discount and delivery keywords
    for (auto it = myPayments.begin(); it != myPayments.end();) {
      assert(not it->first.empty());
      const auto myLower = boost::algorithm::to_lower_copy(it->first);
      if (myLower == "discount") {
        myDiscount = it->second;
        it         = myPayments.erase(it);
      } else if (myLower == "delivery") {
        myDelivery = it->second;
        it         = myPayments.erase(it);
      } else {
        ++it;
      }
    }

    if (myDiscount < 0.0f or myDiscount > 100.0f) {
      myValid = false;
    }

    // assume the user meant percentage
    if (myDiscount >= 1.0f) {
      myDiscount /= 100.0f;
    }

    web::json::value myValue;
    if (myAuthorized) {
      if (myHelpRequested) {
        myValue["text"] = web::json::value(myHelp);
      } else if (myValid) {
        auto myTot = 0.0f;
        for (const auto& myPair : myPayments) {
          myTot += myPair.second;
        }
        auto                         myTotAssigned = 0.0f;
        std::map<std::string, float> myPaymentsDiscounted;
        for (const auto& myPair : myPayments) {
          const auto myPayment =
              myPair.second * (1 - myDiscount) + myDelivery / myPayments.size();
          myPaymentsDiscounted.insert({myPair.first, myPayment});
          myTotAssigned += myPayment;
          VLOG(1) << myPair.first << ' ' << myPair.second << ' ' << myDiscount
                  << ' ' << (myDelivery / myPayments.size()) << ' ' << myPayment
                  << ' ' << myTotAssigned;
        }

        uiiit::support::MmTable myTable(2);
        myTable(0, 0, "Who");
        myTable(0, 1, "How much");

        std::string myResp;
        size_t      myRow = 1;
        for (const auto& myPair : myPaymentsDiscounted) {
          std::stringstream myStream;
          myStream << std::fixed << std::setprecision(2) << myPair.second;
          myTable(myRow, 0, myPair.first);
          myTable(myRow, 1, myStream.str());
          myRow++;
        }
        const auto        myBill = (1 - myDiscount) * myTot + myDelivery;
        std::stringstream myStream;
        myStream << std::fixed << std::setprecision(2) << myBill;
        myTable(myRow, 0, "** Total **");
        myTable(myRow, 1, "** " + myStream.str() + " **");
        myResp += myTable.toString() + "_Bon appetit!_";

        myValue["response_type"] = web::json::value("in_channel");
        myValue["text"]          = web::json::value(myResp);
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
  const std::string theToken;
};

int main(int argc, char* argv[]) {
  uiiit::support::GlogRaii myGlogRaii(argv[0]);

  try {
    po::options_description   myDesc("Allowed options");
    uiiit::support::MmOptions myCli(argc, argv, myDesc);

    if (myCli.token().empty()) {
      throw std::runtime_error("Empty token");
    }

    SushiServer myServer(myCli.root(), myCli.token());
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
