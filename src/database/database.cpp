#include <iostream>
#include <string>
#include <sqlite3.h>
#include <chrono>
#include <iomanip>
#include <sstream>

//class for biota_laut table
class DataBiota{
    private:
        std::string timestamp;
        std::string get_iso8601_timestamp(){
            auto now = std::chrono::system_clock::now();
            std::time_t t = std::chrono::system_clock::to_time_t(now);
            std::stringstream ss;
            ss << std::put_time(std::gmtime(&t), "%FT%TZ");
            return ss.str();
        }
    public:
        int id;
        double lat;
        double lon;
        float depth;
        std::string label;
        float confidence;
        std::string filename;

   //default construct
    DataBiota() : id(0), lat(0.0), lon(0.0), depth(0.0f), confidence(0.0f) {};
    
    //construct with input
    DataBiota(int _id, double _lat, double _lon, float _depth, std::string _lbl, float _conf, std::string _fname ): id(_id), lat(_lat), lon(_lon), depth(_depth), label(_lbl), confidence(_conf), filename(_fname){
        timestamp = get_iso8601_timestamp();
    }
};

static int callback(void *NotUsed,  int argc, char **argv, char **azColName){
    for(int i=0;i<argc; i++){
        std::cout << azColName[i] << " = " << (argv[i] ? argv[i] : "NULL") << std::endl;
        return (-1);
    }
    return 0;
}

int dbInit(int rc, sqlite3 *db, char*errMsg){
    //open database file
    rc = sqlite3_open("biota.db", &db);
    if(rc){
        std::cerr << "error opening database: " << sqlite3_errmsg16(db) << std::endl;
        return (-1);
    }
    else{
        std::cout << "Database successfully opened!\n";
    }
    return 0;
}


int main(){
    sqlite3 *db;
    char* errMsg;
    int rc;
    std::string sql;

    dbInit(rc, db, errMsg);

    return 0;
}