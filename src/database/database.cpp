#include <iostream>
#include <string>
#include <sqlite3.h>
#include <chrono>
#include <iomanip>
#include <sstream>

//class for biota_laut table
class DataBiota{
    private:
    //setting a timestamp
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

// callback function for sqlite database
static int callback(void *NotUsed,  int argc, char **argv, char **azColName){
    for(int i=0;i<argc; i++){
        std::cout << azColName[i] << " = " << (argv[i] ? argv[i] : "NULL") << std::endl;
        return (-1);
    }
    return 0;
}

// function to initialize and open database
int dbInit(sqlite3 *&db, const std::string &passwd){
    //open database file
    int rc = sqlite3_open("biota_encrypted.db", &db);
    if(rc){
        std::cerr << "error opening database: " << sqlite3_errmsg16(db) << std::endl;
        return (-1);
    }
    std::cout << "Database successfully opened!\n";

    //set encryption key
    std::string pragma = "PRAGMA key = '" + passwd + "';";
    char *errMsg = nullptr;
    rc = sqlite3_exec(db, pragma.c_str(), nullptr, nullptr, &errMsg);
    if(rc != SQLITE_OK){
        std::cerr << "Error setting encryption key: " << errMsg << std::endl;
        sqlite3_free(errMsg);
        sqlite3_close(db);
        return (-1);
    }
    std::cout << "Database encrypted!\n";

    //ensure table exists
    const char *createTableSQL = 
        "CREATE TABLE IF NOT EXISTS biota_laut("
        "id INTEGER PRIMARY KEY, "
        "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "latitude DOUBLE NOT NULL, "
        "longitude DOUBLE NOT NULL, "
        "depth FLOAT NOT NULL, "
        "label TEXT NOT NULL, "
        "confidence FLOAT NOT NULL, "
        "filename TEXT NOT NULL); ";

    rc = sqlite3_exec(db, createTableSQL, nullptr, nullptr, &errMsg);
    if(rc != SQLITE_OK){
        std::cerr << "Error creating table: " << errMsg << std::endl;
        sqlite3_free(errMsg);
        sqlite3_close(db);
        return (-1);
    }
    return 0;
}


// function to add data to database
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

//main function for testing
int main(){
    sqlite3 *db;
    char* errMsg;
    int rc;
    std::string pwd = "test_pwd";
    std::string wrongPwd = "wrong_pwd";

    dbInit(db, pwd);

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