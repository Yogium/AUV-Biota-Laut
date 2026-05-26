#ifndef GB_LIB_INCLUDE_GB_LIB_GB_NAVIGATION_EKFSLAMAUV_H_
#define GB_LIB_INCLUDE_GB_LIB_GB_NAVIGATION_EKFSLAMAUV_H_

#include <iostream>
#include <map>
#include <utility>
#include <string>
#include <vector>

#include "ros/ros.h"
#include "./EkfBase.h"
#include "./nav_utils.h"
#include "./Ned.h"

class EkfSlamAuv: public EkfBase
{
public:
    /**
    * \brief Constructor.
    *
    * \param state_vector_size Size in rows of the state vector
    * \param q_var Sistem c
    * \param now (??? belom tau ini gunanya apa)
    */
    EkfSlamAuv  (const unsigned int state_vector_size, 
                 const Eigen::VectorXd q_var, 
                 const double now);
    int8_t gps_status_;
    Eigen::Vector3d auv_latlonh_;
    Eigen::Vector3d auv_orientation_;           //!< Orientation vector
    Eigen::Matrix3d auv_Cpt_;                   //!< Rotation matrix from platfrom to tangent    
    Eigen::Vector3d auv_angular_velocity_;      //!< Angular velocity vector
    Eigen::Vector3d auv_linear_acceleration_;   //!< Body acceleration vector
    Eigen::Vector3d auv_body_velocity_;         //!< Body velocity vector
    Eigen::Vector3d auv_ned_velocity_;          //!< NED velocity vector
    Eigen::Vector3d auv_position_;              //!< Position vector (NED)
    Eigen::Vector3d auv_ba_;
    Eigen::Vector3d auv_bg_;
    Eigen::VectorXd error_state_;               //!< Kalman filter correction
    double last_prediction_ ;                   //!< Time of last predicition
    // double latitude_ ;                          //!< Latitude initialization 
    /**
    * \brief Perhitungan state transition matrix.
    * Persamaan diambil dari paper AUV Navigation
    * \param t Timestamp
    * \return State transition matrix 
    */
    Eigen::MatrixXd computeA(const double t) const ;
    
    Eigen::MatrixXd computeG() const ;

    Eigen::MatrixXd computeF() const ;

    /**
    * \brief Menghitung matriks rotasi dari platform ke tangent
    * \return Vector position, orientation, and body velocity
    */
    Eigen::MatrixXd computeCpt(void) const ;

    Eigen::MatrixXd computeSkewSymmetryMatrix(const Eigen::VectorXd temp) const ; 
    
    bool init_imu_;

    // IMU input
    void setImuInput(const std::string sensor_id,
                     const double time_stamp,
                     const Eigen::Vector3d orientation,
                     const Eigen::Vector3d angular_velocity,
                     const Eigen::Vector3d linear_acceleration);
                     
    Eigen::Vector3d insCalculation (const double now,
                                    const Eigen::Vector3d linear_acceleration,
                                    const Eigen::Vector3d orientation,
                                    const Eigen::Vector3d angular_velocity);

    void orientationUpdate(const std::string sensor_id,
                           const double time_stamp,
                           const Eigen::VectorXd orientation,
                           const Eigen::MatrixXd orientation_cov);
    
    // Depth sensor 
    void depthUpdate(const std::string sensor_id,
                     const double time_stamp,
                     const double depth,
                     const double depth_cov);

    void createDepthMeasure(const double depth,
                            const double depth_cov,
                            Eigen::VectorXd& z,
                            Eigen::MatrixXd& R,
                            Eigen::MatrixXd& H,
                            Eigen::MatrixXd& V);    

    // DVL 
    void velocityUpdate(const std::string sensor_id,
                                const double time_stamp,
                                const Eigen::VectorXd velocity,
                                const Eigen::MatrixXd velocity_cov,
                                const Eigen::MatrixXd gyro_cov);

    void createVelocityMeasure(const Eigen::VectorXd velocity,
                               const Eigen::MatrixXd velocity_cov,
                               const Eigen::MatrixXd gyro_cov,
                               Eigen::VectorXd& z,
                               Eigen::MatrixXd& R,
                               Eigen::MatrixXd& H,
                               Eigen::MatrixXd& v);                                

    void getData(Eigen::Vector3d& orientation,
                 Eigen::Vector3d& angular_velocity,
                 Eigen::Vector3d& linear_acceleration,
                 Eigen::Vector3d& linear_velocity,
                 Eigen::Vector3d& position,
                 Eigen::Vector3d& latlonh,
                 int8_t& gps_status);

    // GPS 
    void gpsUpdate (const std::string sensor_id,
                    const double time_stamp,
                    const int8_t status,
                    const double latitude,
                    const double longitude,
                    const double north,
                    const double east,
                    const double depth,
                    const Eigen::MatrixXd gps_cov);

    void createGpsMeasure(const Eigen::VectorXd gps_position,
                          const Eigen::MatrixXd gps_cov,
                          Eigen::VectorXd& z,
                          Eigen::MatrixXd& R,
                          Eigen::MatrixXd& H,
                          Eigen::MatrixXd& V);




    void kalmancorrection();
};

#endif