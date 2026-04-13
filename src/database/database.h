#pragma once

#include <string>
#include <sqlite3.h>

class DataBiota{
    private:
    std::string get_iso8601_timestamp();

    public:
    int id;
    std::string timestamp;
    double lat;
    double lon;
    float depth;
    std::string label;
    float confidence;
    std::string filename;

    DataBiota();
    DataBiota(int _id, double _lat, double _lon, float _depth, std::string _lbl, float _conf, std::string _fname);
};

int dbInit(sqlite3*& db, const std::string passwd);
void addData(sqlite3* db, const DataBiota& data);
void exportJSON(sqlite3* db);
void cleanDb(sqlite3* db);