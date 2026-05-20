#include "database.h"
#include <iostream>
#include <string>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main() {
    sqlite3 *db;
    //std::string pwd = "test_pwd";

    if (dbInit(db) != 0) {
        std::cerr << "[ERROR] Failed to initialize database. Exiting..." << std::endl;
        return -1;
    }

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

        // Process data line by line to ensure we capture complete JSON objects
        size_t pos;
        while ((pos = stream_buffer.find('\n')) != std::string::npos) {
            std::string json_line = stream_buffer.substr(0, pos);
            stream_buffer.erase(0, pos + 1);

            try {
                // Parse the JSON payload
                json payload = json::parse(json_line);
                
                // Extract detection metadata
                if (payload.contains("metadata") && payload["metadata"].is_array()) {
                    for (const auto& item : payload["metadata"]) {
                        // Extract fields 
                        int id = item["ID"].get<int>();
                        std::string time = item["time"].get<std::string>();
                        double lat = item["lat"].get<double>();
                        double lon = item["lon"].get<double>();
                        float depth = item["depth"].get<float>();
                        std::string label = item["label"].get<std::string>();
                        float conf = item["confidence"].get<float>();
                        std::string flag = item["flag"].get<std::string>();
                        std::string filename = item["filename"].get<std::string>();

                        // Construct object and insert to SQLite
                        DataBiota biota(id, time, lat, lon, depth, label, conf, flag, filename);
                        addData(db, biota);
                        
                        std::cout << "[DB] Inserted: " << label << " (" << conf * 100 << "%) at depth " << depth << "m" << std::endl;
                    }
                }
                
            } catch (const json::exception& e) {
                std::cerr << "[ERROR] JSON Parsing failed: " << e.what() << std::endl;
            }
        }
    }

    close(client_socket);
    close(server_fd);
    sqlite3_close(db);

    return 0;
}