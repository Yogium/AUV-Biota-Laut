#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstdlib>
#include <ctime>

int main() {
    srand(time(0));

    int num_packets;
    std::cout << "Enter the number of randomly generated packets to send: ";
    if (!(std::cin >> num_packets) || num_packets <= 0) {
        std::cerr << "Invalid number.\n";
        return -1;
    }

    // 1. Create a standard TCP socket
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;

    // 2. Set up the server address (localhost on port 9420)
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);

    // 3. Connect to your server
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        std::cerr << "Connection failed. Is the server running?\n";
        return -1;
    }

    std::cout << "Connected! Generating and sending " << num_packets << " packets...\n";
    std::cout << "---------------------------------------------------\n";

    // 4. Generate and send loop
    for (int i = 0; i < num_packets; i++) {
        // Generate random data around South Tangerang / Jakarta coordinates
        double lat = -6.2088 + ((rand() % 1000) - 500) / 100000.0;
        double lon = 106.8450 + ((rand() % 1000) - 500) / 100000.0;
        float depth = 5.0f + (rand() % 200) / 10.0f; // Random depth 5.0 to 25.0

        // Print directly to the terminal as it works
        std::cout << "[SENDING " << (i + 1) << "/" << num_packets << "] "
                  << "Lat: " << lat 
                  << " | Lon: " << lon 
                  << " | Depth: " << depth << "m\n";

        // Pack exactly 20 bytes into a buffer 
        char buffer[20];
        memcpy(buffer, &lat, sizeof(double));         // Bytes 0-7
        memcpy(buffer + 8, &lon, sizeof(double));     // Bytes 8-15
        memcpy(buffer + 16, &depth, sizeof(float));   // Bytes 16-19

        // Send the buffer over the network
        send(sock, buffer, 20, 0);

        // Sleep for 50 milliseconds to prevent TCP from batching packets together
        usleep(50000); 
    }

    // 5. Close the connection
    std::cout << "---------------------------------------------------\n";
    close(sock);
    std::cout << "All data sent and connection closed.\n";

    return 0;
}