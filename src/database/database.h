#pragma once

#include <string>
#include <sqlite3.h>

class DataBiota{
    public:
    int id;
    std::string timestamp;
    double lat;
    double lon;
    float depth;
    std::string label;
    float confidence;
    std::string flag;
    std::string filename;

    DataBiota();
    DataBiota(int _id, std::string _time, double _lat, double _lon, float _depth, std::string _lbl, float _conf, std::string _flag, std::string _fname);
};


static int callback(void *NotUsed,  int argc, char **argv, char **azColName);
int dbInit(sqlite3 *&db, const std::string configPath = "setup.json");
void addData(sqlite3* db, const DataBiota& data);
void exportJSON(sqlite3* db);
void cleanDb(sqlite3* db);
int socketInit(std::string ip, int port);