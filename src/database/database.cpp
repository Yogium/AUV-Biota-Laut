#include "database.h"
#include <iostream>
#include <string>
#include <sqlite3.h>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <nlohmann/json.hpp>
#include <fstream>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>

// Implement constructors
DataBiota::DataBiota() : id(0), lat(0.0), lon(0.0), depth(0.0f), confidence(0.0f) {}

DataBiota::DataBiota(std::string _id, std::string _time, double _lat, double _lon, float _depth, std::string _lbl, float _conf, std::string _flag, std::string _fname)
    : id(_id), timestamp(_time), lat(_lat), lon(_lon), depth(_depth), label(_lbl), confidence(_conf), flag(_flag), filename(_fname) {
}

// Callback function for sqlite database
static int callback(void *NotUsed,  int argc, char **argv, char **azColName){
    for(int i=0;i<argc; i++){
        std::cout << azColName[i] << " = " << (argv[i] ? argv[i] : "NULL") << std::endl;
        return (-1);
    }
    return 0;
}

// Function to initialize and open database
int dbInit(sqlite3 *&db, const std::string configPath){
    //grab database name and password from json setup file
    std::ifstream configFile(configPath);
    if(!configFile.is_open()){
        std::cerr << "[ERROR] Failed to open config file: " << configPath << std::endl;
        return(-1);
    }

    nlohmann::json config;
    try {
        configFile >> config;
    }catch(const nlohmann::json::parse_error& e){
        std::cerr << "[ERROR] Failed to parse JSON config: "<< e.what() << std::endl;
        return(-1);
    }

    std::string dbName = config.value("database_name", "biota.db");
    std::string dbPwd = config.value("database_password", "");

    if(dbPwd.empty()){
        std::cerr << "[WARNING] Database password is empty!\n";
    }
    // Open database file
    int rc = sqlite3_open(dbName.c_str(), &db);
    if(rc){
        std::cerr << "[ERROR] Failed to open database: " << sqlite3_errmsg16(db) << std::endl;
        return (-1);
    }
    std::cout << "[SYSTEM] Database successfully opened!\n";

    // Set encryption key
    std::string pragma = "PRAGMA key = '" + dbPwd + "';";
    char *errMsg = nullptr;
    rc = sqlite3_exec(db, pragma.c_str(), nullptr, nullptr, &errMsg);
    if(rc != SQLITE_OK){
        std::cerr << "[ERROR] Error setting encryption key: " << errMsg << std::endl;
        sqlite3_free(errMsg);
        sqlite3_close(db);
        return (-1);
    }
    std::cout << "[SYSTEM] Database encrypted!\n";

    // Ensure table exists
    const char *createTableSQL = 
        "CREATE TABLE IF NOT EXISTS biota_laut("
        "id TEXT PRIMARY KEY, "
        "time TEXT NOT NULL, "
        "latitude DOUBLE NOT NULL, "
        "longitude DOUBLE NOT NULL, "
        "depth FLOAT NOT NULL, "
        "label TEXT NOT NULL, "
        "confidence FLOAT NOT NULL, "
        "flag TEXT NOT NULL,"
        "filename TEXT NOT NULL); ";

    rc = sqlite3_exec(db, createTableSQL, nullptr, nullptr, &errMsg);
    if(rc != SQLITE_OK){
        std::cerr << "[ERROR] Failed to create table: " << errMsg << std::endl;
        sqlite3_free(errMsg);
        sqlite3_close(db);
        return (-1);
    }
    return 0;
}


// Function to add data to database
void addData(sqlite3* db, const DataBiota& data){
    const char* sql = "INSERT INTO biota_laut (id, time, latitude, longitude, depth, label, confidence, flag, filename) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)";
    
    //preparing sqlite statement
    sqlite3_stmt* stmt;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if(rc != SQLITE_OK){
        std::cerr << "[ERROR] SQL Error: " << sqlite3_errmsg(db) << std::endl;
        return;
    }

    //binding values
    sqlite3_bind_text(stmt, 1, data.id.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 2, data.timestamp.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_double(stmt, 3, data.lat);
    sqlite3_bind_double(stmt, 4, data.lon);
    sqlite3_bind_double(stmt, 5, data.depth);
    sqlite3_bind_text(stmt, 6, data.label.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_double(stmt, 7, data.confidence);
    sqlite3_bind_text(stmt, 8, data.flag.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 9, data.filename.c_str(), -1, SQLITE_STATIC);

    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
}

void exportJSON(sqlite3* db){
    // Declare array to hold records
    nlohmann::json jsonArr = nlohmann::json::array();
    
    // Declare sqlite statements
    const char* sql = "SELECT id, time, latitude, longitude, depth, label, confidence, flag, filename FROM biota_laut";
    sqlite3_stmt* stmt;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if(rc != SQLITE_OK){
        std::cerr << "[ERROR] SQL Error preparing database for extractions: " << sqlite3_errmsg(db) << std::endl;
        return;
    }

    // Fetch each row and built a json object
    while(sqlite3_step(stmt) == SQLITE_ROW){
        nlohmann::json obj;
        obj["id"] = std::string((const char*)sqlite3_column_text(stmt, 0));
        obj["time"] = std::string((const char*)sqlite3_column_text(stmt, 1));
        obj["latitude"] = sqlite3_column_double(stmt, 2);
        obj["longitude"] = sqlite3_column_double(stmt, 3);
        obj["depth"] = sqlite3_column_double(stmt, 4);
        obj["label"] = std::string((const char*)sqlite3_column_text(stmt, 5));
        obj["confidence"] = sqlite3_column_double(stmt, 6);
        obj["flag"] = std::string((const char*)sqlite3_column_text(stmt, 7));
        obj["filename"] = std::string((const char*)sqlite3_column_text(stmt, 8));
        jsonArr.push_back(obj);
    }
    sqlite3_finalize(stmt);

    // Write to a file in same directory
    std::ofstream file("biota_export.json");
    if(!file.is_open()){
        std::cerr << "[ERROR] Failed to open file" << std::endl;
        return;
    }
    file << jsonArr.dump(4); // 4 space indentation
    file.close();
    std::cout << "[SYSTEM] Data successfully exported to biota_export.json" << std::endl;
}

// Function to clean current database of all rows in table
void cleanDb(sqlite3* db){
    const char* sql = "DELETE FROM biota_laut;";
    char* errmsg = nullptr;
    int rc = sqlite3_exec(db, sql, nullptr, nullptr, &errmsg);
    if(rc != SQLITE_OK){
        std::cerr << "[ERROR] Failed to delete all rows from table: " << errmsg << std::endl;
        sqlite3_free(errmsg);
        return;
    }
    std::cout << "[SYSTEM] All rows deleted from table!" << std::endl;
}

int socketInit(std::string ip, int port){
    int serversocket = socket(AF_INET, SOCK_STREAM, 0);
    if (serversocket == -1) return -1;
    // Prevent "address already in use" error
    int opt = 1;
    setsockopt(serversocket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    serverAddr.sin_addr.s_addr = inet_addr(ip.c_str());

    // Bind socket
    if (bind(serversocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        std::cerr << "[ERROR] Socket binding failed" << std::endl;
        return -1;
    };
    // Set the socket to listen to incoming data
    if (listen(serversocket, 3) < 0) {
        std::cerr << "[ERROR] Socket listening failed" << std::endl;
        return -1;
    }
    return serversocket; 
}