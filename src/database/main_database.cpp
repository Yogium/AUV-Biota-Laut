#include "database.h"
#include <iostream>
#include <string>
#include <fstream>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <nlohmann/json.hpp>
#include <chrono> // Added for high-resolution timing

using json = nlohmann::json;

int main() {
    sqlite3 *db;

    if (dbInit(db) != 0) {
        std::cerr << "[ERROR] Failed to initialize database. Exiting..." << std::endl;
        return -1;
    }

    // Check for reset table and export flags
    const std::string configPath = "setup.json";
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
    std::string export_flag = config.value("export_JSON", "true");
    std::string clean_flag = config.value("clean_db", "false");
    std::string exportPath = config.value("export_path", "biota_laut.json");
    configFile.close();

    if(clean_flag == "true"){
        cleanDb(db);
    }

    // --- NEW: Initialize the timing log file ---
    std::ofstream time_log("db_insert_times.csv", std::ios::app);
    if (!time_log.is_open()) {
        std::cerr << "[WARNING] Could not open db_insert_times.csv for logging." << std::endl;
    } else {
        // Write CSV header if the file is empty
        time_log.seekp(0, std::ios::end);
        if (time_log.tellp() == 0) {
            time_log << "timestamp_sys,biota_id,label,insert_time_us\n";
        }
    }
    // -------------------------------------------

    // Initialize TCP server
    int server_fd = socketInit("127.0.0.1", 8080);
    if (server_fd < 0) {
        std::cerr << "[ERROR] Failed to initialize socket server. Exiting..." << std::endl;
        return -1;
    }
    std::cout << "[SYSTEM] Server listening on 127.0.0.1:8080. Waiting for connection..." << std::endl;

    // Accept incoming connection from Python
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int client_socket = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);

    if (client_socket < 0) {
        std::cerr << "[ERROR] Failed to accept connection" << std::endl;
        return -1;
    }
    std::cout << "[SYSTEM] Client connected" << std::endl;

    std::string stream_buffer = "";
    char temp_buf[4096];

    while (true) {
        int bytes_read = read(client_socket, temp_buf, sizeof(temp_buf) - 1);
        
        if (bytes_read <= 0) {
            std::cout << "[SYSTEM] Client disconnected. Closing server" << std::endl;
            break;
        }
        
        temp_buf[bytes_read] = '\0';
        stream_buffer += temp_buf;

        size_t pos;
        while ((pos = stream_buffer.find('\n')) != std::string::npos) {
            std::string json_line = stream_buffer.substr(0, pos);
            stream_buffer.erase(0, pos + 1);

            try {
                json payload = json::parse(json_line);
                
                if (payload.contains("metadata") && payload["metadata"].is_array()) {
                    for (const auto& item : payload["metadata"]) {
                        std::string id = item["ID"].get<std::string>();
                        std::string time = item["time"].get<std::string>();
                        double lat = item["lat"].get<double>();
                        double lon = item["lon"].get<double>();
                        float depth = item["depth"].get<float>();
                        std::string label = item["label"].get<std::string>();
                        float conf = item["confidence"].get<float>();
                        std::string flag = item["flag"].get<std::string>();
                        std::string filename = item["filename"].get<std::string>();

                        DataBiota biota(id, time, lat, lon, depth, label, conf, flag, filename);
                        
                        // --- NEW: Timing block starts here ---
                        auto start_time = std::chrono::high_resolution_clock::now();
                        
                        addData(db, biota);
                        
                        auto end_time = std::chrono::high_resolution_clock::now();
                        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count();
                        // -------------------------------------
                        
                        // Print to screen
                        std::cout << "[DB] Inserted: " << label 
                                  << " (" << conf * 100 << "%) at depth " << depth << "m. "
                                  << "Insert time: " << duration << " us" << std::endl;

                        // Write to CSV log file
                        if (time_log.is_open()) {
                            time_log << time << "," 
                                     << id << "," 
                                     << label << "," 
                                     << duration << "\n";
                        }
                    }
                }
                
            } catch (const json::exception& e) {
                std::cerr << "[ERROR] JSON Parsing failed: " << e.what() << std::endl;
            }
        }
    }
    
    if(export_flag == "true"){
        exportJSON(db, exportPath);
    }
 
    if (time_log.is_open()) {
        time_log.close();
    }
    
    close(client_socket);
    close(server_fd);
    sqlite3_close(db);

    return 0;
}