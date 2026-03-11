#include <iostream>
#include <string>
#include <sqlite3.h>
#include <chrono>
#include <iomanip>
#include <sstream>

//class for biota_laut table
class DataBiota{
    private:
        std::string get_iso8601_timestamp(){
            auto now = std::chrono::system_clock::now();
            std::time_t t = std::chrono::system_clock::to_time_t(now);
            std::stringstream ss;
            ss << std::put_time(std::gmtime(&t), "%FT%TZ");
            return ss.str();
        }
    public:
        int id;
        std::string timestamp;
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

int dbInit(int rc, sqlite3 *&db, char*errMsg){
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

void addData(sqlite3* db, const DataBiota& data){
    const char* sql = "INSERT INTO biota_laut (id, time, latitude, longitude, depth, label, confidence, filename) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
    
    //preparing sqlite statement
    sqlite3_stmt* stmt;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if(rc != SQLITE_OK){
        std::cerr << "SQL Error: " << sqlite3_errmsg(db) << std::endl;
        return;
    }

    //binding values
    sqlite3_bind_int(stmt, 1, data.id);
    sqlite3_bind_text(stmt, 2, data.timestamp.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_double(stmt, 3, data.lat);
    sqlite3_bind_double(stmt, 4, data.lon);
    sqlite3_bind_double(stmt, 5, data.depth);
    sqlite3_bind_text(stmt, 6, data.label.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_double(stmt, 7, data.confidence);
    sqlite3_bind_text(stmt, 8, data.filename.c_str(), -1, SQLITE_STATIC);

    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}

int main(){
    sqlite3 *db;
    char* errMsg;
    int rc;

    dbInit(rc, db, errMsg);

    // Create sample DataBiota objects
    DataBiota biota1(1001234001, 6.2088, 106.8450, 5.5f, "Fish", 0.95f, "fish_001.jpg");
    DataBiota biota2(1001234002, 6.2089, 106.8451, 6.0f, "Coral", 0.87f, "coral_001.jpg");
    DataBiota biota3(1001234003, 6.2090, 106.8452, 7.2f, "Seagrass", 0.92f, "seagrass_001.jpg");

    // Insert data into database
    addData(db, biota1);
    addData(db, biota2);
    addData(db, biota3);

    std::cout << "Data inserted\n";

    sqlite3_close(db);
    return 0;
}