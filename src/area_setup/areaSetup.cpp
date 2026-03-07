#include <iostream>
#include <fstream>
#include <algorithm>

int main() {
    // Latitude and longitude variables
    double lat1, lon1, lat2, lon2;

    std::cout << "Enter Corner 1 Latitude: ";
    std::cin >> lat1;
    std::cout << "Enter Corner 1 Longitude: ";
    std::cin >> lon1;

    std::cout << "Enter Corner 2 Latitude: ";
    std::cin >> lat2;
    std::cout << "Enter Corner 2 Longitude: ";
    std::cin >> lon2;

    // Determine boundary
    double min_lat = std::min(lat1, lat2);
    double max_lat = std::max(lat1, lat2);
    double min_lon = std::min(lon1, lon2);
    double max_lon = std::max(lon1, lon2);

    // Store boundary in file
    std::ofstream outfile("m_bounds.txt");

    if (outfile.is_open()) {
        // Write data to file
        outfile << min_lat << "\n" << max_lat << "\n" << min_lon << "\n" << max_lon << "\n";
        outfile.close();
        std::cout << "\n[SUCCESS] Zona pemantauan tersimpan" << std::endl;
    } else {
        std::cerr << "\n[ERROR] Zona pemantauan tidak dapat dibuat" << std::endl;
    }
    return 0;
}