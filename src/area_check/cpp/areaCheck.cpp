#include <iostream>
#include <fstream>

int main() {
    // Variables to store latitude and longitude from txt file
    double min_lat, max_lat, min_lon, max_lon;

    // Load file and read
    std::ifstream infile("m_bounds.txt");
    if (!infile.is_open()) {
        std::cerr << "[ERROR] File boundary tidak ditemukan";
        return 1;
    }
    infile >> min_lat >> max_lat >> min_lon >> max_lon;
    infile.close();
    std::cout << "[SUCCESS] Boundary tersimpan ke memori";

    // Simulate AUV reading
    double cur_lat, cur_lon;
    std::cout << "\nEnter Current Latitude: ";
    std::cin >> cur_lat;
    std::cout << "\nEnter Current Longitude: ";
    std::cin >> cur_lon;

    // Check boundary condition
    bool in_lat = (cur_lat >= min_lat && cur_lat <= max_lat);
    bool in_lon = (cur_lon >= min_lon && cur_lon <= max_lon);
    if (in_lat && in_lon) {
        std::cout << "\n[STATUS] Wahana berada dalam zona target";
        std::cout << "[SYSTEM] Menyalakan sistem pemantauan";
    } else {
        std::cout << "\n[STATUS] Wahana berada di luar zona target";
        std::cout << "[SYSTEM] Mematikan sistem pemantauan";
    }

    return 0;
}