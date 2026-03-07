#include <iostream>
#include <opencv2/opencv.hpp>
#include <chrono>
#include <iomanip>
#include <sstream>

int main() {
    int cam_index = 0; // 1 for USB camera, 0 for integrated camera
    cv::VideoCapture cap(cam_index);
    if (!cap.isOpened()) {
        std::cerr << "[ERROR] Kamera tidak bisa dibuka" << std::endl;
        return -1;
    }
    std::cout << "[SYSTEM] Kamera aktif. Memulai pengambilan data" << std::endl;

    const int INTERVAL_MS = 1000; // 1000ms / 1 FPS = 1000
    
    // Record starting time
    auto last_time = std::chrono::steady_clock::now();

    cv::Mat frame;

    // Initial frame number
    int frame_count = 1;

    // Loop
    while (true) {
        cap >> frame; // Pull latest frame from hardware
        if (frame.empty()) {
            std::cerr << "[WARNING] Frame kosong terdeteksi" << std::endl;
            continue;
        }

        // Check time and calculate how many ms have passed
        auto cur_time = std::chrono::steady_clock::now();
        auto elapsed_time = std::chrono::duration_cast<std::chrono::milliseconds>(cur_time - last_time).count();
        
        if (elapsed_time >= INTERVAL_MS) {
            // Format file name
            std::ostringstream filename;
            filename << "data_" << std::setfill('0') << std::setw(4) << frame_count << ".jpg";
            // Save file
            cv::imwrite(filename.str(), frame);
            std::cout << "[SYSTEM] " << filename.str() << " at " << elapsed_time << "ms interval" << std::endl;
            // Reset timer
            last_time = cur_time;
            frame_count++;
        }
    }

    cap.release();
    return 0;
}