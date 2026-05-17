#include "database.h"
#include <iostream>
#include <cstdlib>
#include <string>
#include <cstring>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

//data struct

    // public:
    // int id;
    // std::string timestamp;
    // double lat;
    // double lon;
    // float depth;
    // std::string label;
    // float confidence;
    // std::string filename;

    //check if int is still the best way to represent ID

int generateID(std::string label, float conf, int frame, int object){
    int id = 0;
    //check confidence to flag whether warning or not (current threshold 50%)
    if(conf<50.0f)id+=1000000000;
    //check for label part of ID
    if(label == "Fish") id +=0;
    else if(label =="Coral")id+=100000000;
    else if(label == "Seagrass")id+=200000000;
    else if(label == "Human")id+=300000000;
    else id+=400000000;
    //insert frame and object
    id += frame*1000+object;
    return id;
}

void dataGen(double lat, double lon, float depth){
   //take lat, lon, and depth from socket
   //generate everything else
   int id;
   std::string label;
   float confidence;
   std::string filename;

    std::string labelArr[5] = {"Fish", "Coral", "Seagrass", "Human", "Other"};

   //generating confidence
    confidence = 40.0f+(rand()/(float)RAND_MAX)*50.0f;
    //generate label
    label = labelArr[rand()%5];
    //generate 
}


//main function for testing
int main(){
    std::string labelArr[5] = {"Fish", "Coral", "Seagrass", "Human", "Other"};
    srand(time(0));
    sqlite3 *db;
    char* errMsg;
    int rc;
    std::string pwd = "test_pwd";
    std::string wrongPwd = "wrong_pwd";
    int port = 9420;

    dbInit(db, pwd);
    
    int serverSock = socketInit(port);
    listen(serverSock, 5);
    std::cout << "Server listening on port " << port << std::endl;

    int clientSock = accept(serverSock, NULL, NULL);
    std::cout << "Client connected\n";


    char buffer[1024];
    int frame = 1, obj = 1, count = 1;
    while(true){
        int id, flag;
        double lat, lon;
        float depth;
        std::string label = labelArr[rand()%5];
        float conf;
        std::string filename;
        int bytes_receive = recv(clientSock, buffer, sizeof(buffer)-1, 0);

        if(bytes_receive == 0){
            std::cout << "client disconnected\n";
            break;
        }
        else if(bytes_receive < 0){
            std::cerr << "recv error\n";
            break;
        }
        memcpy(&lat, buffer, sizeof(double));
        memcpy(&lon, buffer+8, sizeof(double));
        memcpy(&depth, buffer+16, sizeof(float));

        //generate confidence
        conf = 40.0f+(rand()/(float)RAND_MAX)*50.0f;

        //generate filename
        filename = std::to_string(count) + ".jpg";
        count++;

        //generate frame and obj
        id = generateID(label, conf, frame, obj);
        if(rand()%10 < 3){
            frame++;
            obj = 1;
        }
        else{
            obj++;
        }
        if(conf<0.5){
            flag = 1;
        }
        else flag=0;
        DataBiota data(id, lat, lon, depth, label, conf, flag, filename);
        addData(db, data);
    }


    // // Create sample DataBiota objects
    // DataBiota biota1(1001234001, 6.2088, 106.8450, 5.5f, "Fish", 0.95f, "fish_001.jpg.");
    // DataBiota biota2(1001234002, 6.2089, 106.8451, 6.0f, "Coral", 0.87f, "coral_001.jpg");
    // DataBiota biota3(1001234003, 6.2090, 106.8452, 7.2f, "Seagrass", 0.92f, "seagrass_001.jpg");

    // // Insert data into database
    // addData(db, biota1);
    // addData(db, biota2);
    // addData(db, biota3);

    std::cout << "Data inserted\n";

    exportJSON(db);

    sqlite3_close(db);
    return 0;
}