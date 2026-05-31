#include "database.h"
#include <iostream>
#include <cstdlib>
#include <ctime>
#include <string>
#include <cstring>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

std::string generateID(const std::string& label, float conf, int frame, int object){
    int id = 0;
    if(conf < 50.0f) id += 1000000000;
    if(label == "Fish") id += 0;
    else if(label == "Coral") id += 100000000;
    else if(label == "Seagrass") id += 200000000;
    else if(label == "Human") id += 300000000;
    else id += 400000000;
    id += frame * 1000 + object;
    return std::to_string(id);
}

std::string getTimestamp(){
    auto now = std::chrono::system_clock::now();
    std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::ostringstream oss;
    oss << std::put_time(std::localtime(&t), "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

int main(){
    std::string labelArr[5] = {"Fish", "Coral", "Seagrass", "Human", "Other"};
    srand(time(0));
    sqlite3 *db;
    int port = 9420;
    std::string ip = "127.0.0.1";

    dbInit(db);
    cleanDb(db);

    int serverSock = socketInit(ip, port);
    std::cout << "Server listening on port " << port << std::endl;

    int clientSock = accept(serverSock, NULL, NULL);
    std::cout << "Client connected\n";

    char buffer[1024];
    int frame = 1, obj = 1, count = 1;
    while(true){
        std::string id;
        double lat, lon;
        float depth;
        std::string label = labelArr[rand() % 5];
        float conf;
        std::string filename;
        std::string flag;

        int bytes_received = recv(clientSock, buffer, sizeof(buffer) - 1, 0);

        if(bytes_received == 0){
            std::cout << "Client disconnected\n";
            break;
        }
        else if(bytes_received < 0){
            std::cerr << "recv error\n";
            break;
        }

        memcpy(&lat, buffer, sizeof(double));
        memcpy(&lon, buffer + 8, sizeof(double));
        memcpy(&depth, buffer + 16, sizeof(float));

        conf = 40.0f + (rand() / (float)RAND_MAX) * 50.0f;
        filename = std::to_string(count++) + ".jpg";

        id = generateID(label, conf, frame, obj);
        if(rand() % 10 < 3){
            frame++;
            obj = 1;
        }
        else{
            obj++;
        }

        flag = (conf < 50.0f) ? "TIDAK YAKIN" : "YAKIN";
        std::string timestamp = getTimestamp();
        DataBiota data(id, timestamp, lat, lon, depth, label, conf, flag, filename);
        addData(db, data);
    }

    std::cout << "Data inserted\n";
    exportJSON(db);
    sqlite3_close(db);
    return 0;
}
