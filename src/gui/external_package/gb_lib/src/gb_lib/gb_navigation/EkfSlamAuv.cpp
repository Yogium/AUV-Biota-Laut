#include "gb_lib/gb_navigation/EkfSlamAuv.h"

double LastTime;
double northgps = 0.0,eastgps = 0.0;

EkfSlamAuv::EkfSlamAuv(const unsigned int state_vector_size, const Eigen::VectorXd q_var, const double now):
  EkfBase(state_vector_size, q_var, now),
  init_imu_(false),
  auv_orientation_(0.0, 0.0, 0.0)
{
  last_prediction_          = 0;
  gps_status_               = -1;
  auv_latlonh_              << 41.7773700755, 3.03875848166, 0.0;
  auv_position_             = Eigen::Vector3d::Zero();
  auv_orientation_          = Eigen::Vector3d::Zero(); 
  auv_body_velocity_        = Eigen::Vector3d::Zero();
  auv_ba_                   = Eigen::Vector3d::Zero();
  auv_bg_                   = Eigen::Vector3d::Zero();
  auv_ned_velocity_         = Eigen::Vector3d::Zero(); 
  auv_linear_acceleration_  = Eigen::Vector3d::Zero();
  auv_angular_velocity_     = Eigen::Vector3d::Zero();
  auv_Cpt_                  = Eigen::Matrix3d::Identity();
  error_state_              = Eigen::VectorXd::Zero(15);
  // latitude_                 = -6.8914747*M_PI/180;
  // w_ie_t_                   << 0, 0, 0; // not used
  // g_t_                      << 0, 0, 0; // not used

}

void EkfSlamAuv::setImuInput(const std::string sensor_id,
                             const double time_stamp,
                             const Eigen::Vector3d orientation,
                             const Eigen::Vector3d angular_velocity,
                             const Eigen::Vector3d linear_acceleration)
{

  auv_linear_acceleration_ = linear_acceleration - auv_ba_;
  // auv_linear_acceleration_(0) =  linear_acceleration(0) - error_state_(9);
  // auv_linear_acceleration_(1) =  linear_acceleration(1) - error_state_(10);
  // auv_linear_acceleration_(2) =  linear_acceleration(2) - error_state_(11);

  auv_angular_velocity_ = angular_velocity - auv_bg_ ;

  // auv_ba_ = Eigen::VectorXd::Zero(3);
  // auv_bg_ = Eigen::VectorXd::Zero(3);
  // auv_angular_velocity_(0) =  angular_velocity(0) - error_state_(12);  // closed loop kalman
  // auv_angular_velocity_(1) =  angular_velocity(1) - error_state_(13); 
  // auv_angular_velocity_(2) =  angular_velocity(2) - error_state_(14); 

  // std::cout << "auv_ba = " << auv_ba_ << "\n";
  // std::cout << "auv_bg = " << auv_bg_ << "\n";

  // std::cout << "perbaiki 1 : " << linear_acceleration(0) <<" - " << error_state_(3) << "\n" ;
  // std::cout << "perbaiki 2: " << linear_acceleration(1) <<" - " << error_state_(4) << "\n" ;
  // std::cout << "perbaiki 3: " << linear_acceleration(2) <<" - " << error_state_(5) << "\n" ; 


  insCalculation(time_stamp,
                 auv_linear_acceleration_,
                 orientation,
                 auv_angular_velocity_);

  if (makePrediction(time_stamp))
  {
    // updatePrediction();
    // showStateVector();
  }
}

Eigen::Vector3d EkfSlamAuv::insCalculation( const double now,
                                            const Eigen::Vector3d linear_acceleration,
                                            const Eigen::Vector3d orientation,
                                            const Eigen::Vector3d angular_velocity
                                            )
{

  double t = 0.05;
  // now - LastTime;
  // LastTime = now;

  // std::cout << "t:\n" << t << "\n";
  Eigen::Matrix3d Cpt_new, Cpt_old;
  
  Cpt_old = auv_Cpt_;
  
  Eigen::Matrix3d w ;
  w = Eigen::MatrixXd::Identity(3,3) ;
  w = w + computeSkewSymmetryMatrix(angular_velocity)*t ;  

  Cpt_new = Cpt_old * w;
  auv_Cpt_ = Cpt_new ;

  if (init_imu_ == false) {
    init_imu_ = true;
    auv_orientation_ = orientation;
  }

  Eigen::Matrix3d T;
  T(0,0) = 1; T(0,1) = sin(auv_orientation_(0))*tan(auv_orientation_(1));  T(0,2) = cos(auv_orientation_(0))*tan(auv_orientation_(1));
  T(1,0) = 0; T(1,1) = cos(auv_orientation_(0));                           T(1,2) = -sin(auv_orientation_(0));
  T(2,0) = 0; T(2,1) = sin(auv_orientation_(0))/cos(auv_orientation_(1));  T(2,2) = cos(auv_orientation_(0))/cos(auv_orientation_(1));

  // auv_orientation_(0) = atan2(Cpt_new(2,1),Cpt_new(2,2)) ; 
  // auv_orientation_(1) = -atan(Cpt_new(2,0)/sqrt(1-(Cpt_new(2,0)*Cpt_new(2,0)))) ;
  // auv_orientation_(2) = atan2(Cpt_new(1,0),Cpt_new(0,0)) ;

  // auv_orientation_ += angular_velocity*t;
  auv_orientation_ += T*angular_velocity*t;
  // auv_orientation_ = orientation;

  // std::cout << "auv_orientation\n = " << auv_orientation_ << "\n\n";

  auv_body_velocity_ += (linear_acceleration) * t ;
  // auv_body_velocity_(0) = 0.15;
  // auv_body_velocity_(1) = 0.0;
  // auv_body_velocity_(2) = 0.0;
  auv_ned_velocity_ = computeCpt() * auv_body_velocity_  ;

  // std::cout << "kecepatan z : " << auv_ned_velocity_(2) << "\n" ;
  // std::cout << "perbaiki 5: " << v(1) <<" - " << error_state_(1) << "\n" ;
  // std::cout << "perbaiki 6: " << v(2) <<" - " << error_state_(2) << "\n\n" ; 

  auv_position_ += auv_ned_velocity_ * t ;

  // if (auv_position_(2) <= 0) {
  //   auv_position_(2) = 0;
  // }
  
  // error_state_.tail(6) = Eigen::VectorXd::Zero(6);

  std::cout << " Ins Calcul Position = " << auv_position_.transpose() << " Kecepatan = " << auv_body_velocity_.transpose() << std::endl;
  std::cout << " Sudut = " << auv_orientation_.transpose() << " Bias = " << auv_ba_.transpose() << auv_bg_.transpose() <<std::endl;
  last_prediction_ = now ;
}

void EkfSlamAuv::kalmancorrection()
{
  Eigen::Matrix3d w ;
  Eigen::VectorXd position_error(3);
  Eigen::VectorXd small_angle_error(3);
  Eigen::VectorXd body_velocity_error(3);
  Eigen::VectorXd ba_error(3);
  Eigen::VectorXd bg_error(3);

  position_error << error_state_(0), error_state_(1), error_state_(2); 
  small_angle_error << error_state_(3), error_state_(4), error_state_(5);
  body_velocity_error << error_state_(6), error_state_(7), error_state_(8);
  ba_error << error_state_(9), error_state_(10), error_state_(11);
  bg_error << error_state_(12), error_state_(13), error_state_(14);

  w = Eigen::MatrixXd::Identity(3,3) + computeSkewSymmetryMatrix(small_angle_error);
  auv_Cpt_ = w * auv_Cpt_;

  auv_position_ = auv_position_ + position_error;
  
  // if (auv_position_(2) <= 0) {
  //   auv_position_(2) = 0;
  // }

  // auv_orientation_(0) = atan2(auv_Cpt_(2,1),auv_Cpt_(2,2)) ; 
  // auv_orientation_(1) = -atan(auv_Cpt_(2,0)/sqrt(1-(auv_Cpt_(2,0)*auv_Cpt_(2,0)))) ;
  // auv_orientation_(2) = atan2(auv_Cpt_(1,0),auv_Cpt_(0,0)) ;

  // auv_orientation_(0) = atan2(ctp(1,2),ctp(2,2)) ; 
  // auv_orientation_(1) = -atan(ctp(0,2)/sqrt(1-(ctp(0,2)*ctp(0,2)))) ;
  // auv_orientation_(2) = atan2(ctp(0,1),ctp(0,0)) ;
  auv_orientation_ = auv_orientation_ + small_angle_error;

  auv_body_velocity_ = auv_body_velocity_ + body_velocity_error;

  auv_ned_velocity_ = auv_Cpt_ * auv_body_velocity_ ; 
  // auv_ned_velocity_ = computeCpt() * auv_body_velocity_ ; 
  

  auv_ba_ += ba_error;
  auv_bg_ += bg_error;

  std::cout << " Kalman Correct Position = " << auv_position_.transpose() << " Kecepatan = " << auv_body_velocity_.transpose() << std::endl;
  std::cout << " Sudut = " << auv_orientation_.transpose() << " Bias = " << auv_ba_.transpose() << auv_bg_.transpose() <<std::endl;

  error_state_ = Eigen::VectorXd::Zero(15);
}

void EkfSlamAuv::getData(Eigen::Vector3d& orientation,
                         Eigen::Vector3d& angular_velocity,
                         Eigen::Vector3d& linear_acceleration,
                         Eigen::Vector3d& linear_velocity,
                         Eigen::Vector3d& position,
                         Eigen::Vector3d& latlonh,
                         int8_t& gps_status)
{
  orientation = auv_orientation_;
  angular_velocity = auv_angular_velocity_;
  linear_acceleration = auv_linear_acceleration_;
  linear_velocity = auv_body_velocity_ ;
  position = auv_position_ ;
  // position(0) = northgps;
  // position(1) = eastgps;
  // position(2) = auv_position_(2);
  latlonh = auv_latlonh_;
  gps_status = gps_status_;
}

void EkfSlamAuv::gpsUpdate (const std::string sensor_id,
                            const double time_stamp,
                            const int8_t status,
                            const double latitude,
                            const double longitude,
                            const double north,
                            const double east,
                            const double depth,
                            const Eigen::MatrixXd gps_cov)
{
  if (init_imu_)
  {
    Eigen::VectorXd z;
    Eigen::MatrixXd R, H, V;
    Eigen::Vector3d gps_position;
    gps_position << north, east, depth;
    northgps = north;
    eastgps = east;
    gps_status_ = status;
    // auv_position_(0) = north;
    // auv_position_(1) = east;
    createGpsMeasure(gps_position, gps_cov,
                    z, R, H, V);

    // Predict and apply update
    // if (makePrediction(time_stamp))
    // {
      if (applyUpdate(z, R, H, V, 10.0))
      {
        Eigen::VectorXd buffer_ ;
        buffer_ = resetStateVector() ;
        error_state_(0) = buffer_(0) ; error_state_(1) = buffer_(1) ; 
        // error_state_(2) = buffer_(2) ;
        // error_state_(3) = buffer_(3) ; error_state_(4) = buffer_(4) ; error_state_(5) = buffer_(5) ;
        // error_state_(6) = buffer_(6) ; error_state_(7) = buffer_(7) ; error_state_(8) = buffer_(8) ;
        // error_state_(9) += buffer_(9) ; error_state_(10) += buffer_(10) ; error_state_(11) += buffer_(11) ;
        // error_state_(12) += buffer_(12) ; error_state_(13) += buffer_(13) ; error_state_(14) += buffer_(14) ;
        // error_state_ =  buffer_;
        kalmancorrection();
        // std::cout << "correction vector : " << error_state_ << "\n" ;
        std::cout << "GPS measurement aidment" << std::endl;
        auv_position_(0) = auv_position_(0) + error_state_(0);
        auv_position_(1) = auv_position_(1) + error_state_(1);
        // error_state_.head(9) = Eigen::VectorXd::Zero(9);
        // auv_position_ << north, east, depth;
        auv_latlonh_ << latitude, longitude, 0.0;
          // std::cout << " n (state) = " << auv_position_(0) << std::endl;
          // std::cout << " e (state) = " << auv_position_(1) << std::endl;
          // std::cout << " d (state) = " << auv_position_(2) << std::endl;
      }
    // }
  std::cout << " n (gps)= " << gps_position(0) << " n (state) = " << auv_position_(0) << std::endl;
  std::cout << " e (gps)= " << gps_position(1) << " e (state) = " << auv_position_(1) << std::endl;
  std::cout << " d (gps)= " << gps_position(2) << " d (state) = " << auv_position_(2) << std::endl;
  }
}

void EkfSlamAuv::createGpsMeasure(const Eigen::VectorXd gps_position,
                                  const Eigen::MatrixXd gps_cov,
                                  Eigen::VectorXd& z,
                                  Eigen::MatrixXd& R,
                                  Eigen::MatrixXd& H,
                                  Eigen::MatrixXd& V)
{
  z.resize(3);

  R.resize(3,3) ;
  R(0,0) = gps_cov(0,0);
  R(1,1) = gps_cov(1,1);
  R(2,2) = 1e-4;

  H = Eigen::MatrixXd::Zero(3,15);
  H(0,0) = 1.0;
  H(1,1) = 1.0;
  H(2,2) = 0.0;

  V.resize(3,3);
  V = Eigen::MatrixXd::Identity(3,3);

  z(0) = gps_position(0) - auv_position_(0);
  z(1) = gps_position(1) - auv_position_(1);
  z(2) = 0.0;
}


void EkfSlamAuv::depthUpdate(const std::string sensor_id,
                             const double time_stamp,
                             const double depth,
                             const double depth_cov)
{
  if (init_imu_)
  {
    // Create depth measure matrices
    Eigen::VectorXd z;
    Eigen::MatrixXd R, H, V;
    createDepthMeasure(depth, depth_cov,
                       z, R, H, V);

    // Predict and apply update
    if (makePrediction(time_stamp))
    {
      if (applyUpdate(z, R, H, V, 10.0))
      {
        Eigen::VectorXd buffer_ ;
        buffer_ = resetStateVector() ;
        // error_state_(0) = buffer_(0) ; error_state_(1) = buffer_(1) ; 
        error_state_(2) = buffer_(2) ;
        // error_state_(3) = buffer_(3) ; error_state_(4) = buffer_(4) ; error_state_(5) = buffer_(5) ;
        // error_state_(6) = buffer_(6) ; error_state_(7) = buffer_(7) ; error_state_(8) = buffer_(8) ;
        // error_state_(9) += buffer_(9) ; error_state_(10) += buffer_(10) ; error_state_(11) += buffer_(11) ;
        // error_state_(12) += buffer_(12) ; error_state_(13) += buffer_(13) ; error_state_(14) += buffer_(14) ;
        // error_state_ = buffer_;
        // std::cout << "error state (after depth sensor) = \n" << buffer_ << std::endl;
        kalmancorrection();
        auv_position_(2) = auv_position_(2) + error_state_(2);
        auv_position_(2) = depth;
        error_state_.head(9) = Eigen::VectorXd::Zero(9);
        std::cout << "Depth sensor measurement aidment" << std::endl;
      }
      else
      {
        // If the update fails update at leat the prediction
        // updatePrediction();
      }
    }
  }  
}


void EkfSlamAuv::createDepthMeasure(const double depth,
                                    const double depth_cov,
                                    Eigen::VectorXd& z,
                                    Eigen::MatrixXd& R,
                                    Eigen::MatrixXd& H,
                                    Eigen::MatrixXd& V)
{
  z.resize(1);

  R.resize(1,1);
  // R = Eigen::MatrixXd::Zero(1,1);
  // R(0,0) = 1e-8;
  // R(1,1) = 1e-8;
  R << depth_cov;
  
  H = Eigen::MatrixXd::Zero(1, 15);
  // H(0,0) = 0.0;
  // H(1,1) = 0.0;
  H(0,2) = 1.0;

  V.resize(1,1);
  V = Eigen::MatrixXd::Identity(1,1);
  
  // Eigen::MatrixXd depth_scale(1,3);
  // depth_scale << 0, 0, 1;

  // H.block<1,3>(0,0) = depth_scale;

  // Eigen::Vector3d l_ps;

  // l_ps << 1.32, 0, 0.12;

  // Eigen::Matrix3d lps_skew;

  // lps_skew = auv_Cpt_*computeSkewSymmetryMatrix(l_ps);

  // H.block<1,3>(0,0) = -depth_scale*lps_skew;
  // H(0,0) = 0.0;
  // H(1,1) = 0.0;
  // H(2,2) = 1.0;

  // z << depth - (auv_position_(2) + auv_Cpt_.row(2)*l_ps);
  // z(0) = 0.0;
  // z(1) = 0.0;
  z << depth - auv_position_(2);
}

void EkfSlamAuv::orientationUpdate(const std::string sensor_id,
                             const double time_stamp,
                             const Eigen::VectorXd orientation,
                             const Eigen::MatrixXd orientation_cov)
{
  if (init_imu_ )
  {
    // Create orientation measure matrices
    Eigen::VectorXd z;
    Eigen::MatrixXd R, H, V;
    
    z.resize(3);

    R.resize(3,3);
    R = orientation_cov;
    
    H = Eigen::MatrixXd::Zero(3,15);
    V.resize(3,3);
    V = Eigen::MatrixXd::Identity(3,3);

    Eigen::Matrix3d sigma;
    sigma(0,0) = cos(auv_orientation_(1))*cos(auv_orientation_(2));
    sigma(1,0) = cos(auv_orientation_(1))*sin(auv_orientation_(2));
    sigma(2,0) = -sin(auv_orientation_(1));

    sigma(0,1) = -sin(auv_orientation_(2));
    sigma(1,1) = cos(auv_orientation_(2));
    sigma(2,1) = 0;

    sigma(0,2) = 0;
    sigma(1,2) = 0;
    sigma(2,2) = 1;

    H.block<3,3>(0,3) = sigma.inverse();
    H.block<3,3>(0,3) = Eigen::MatrixXd::Identity(3,3);

    z = orientation - auv_orientation_;

    for (int i = 0; i<3; i++){
      if (z(i)>M_PI) {
        z(i) -= 2*M_PI;
      } else if (z(i)<M_PI) {
        z(i) += 2*M_PI;
      }
    }

    // Apply update
    if (applyUpdate(z, R, H, V, -5.0))
    {
      Eigen::VectorXd buffer_ ;
      buffer_ = resetStateVector() ;
      // error_state_(0) = buffer_(0) ; error_state_(1) = buffer_(1) ; error_state_(2) = buffer_(2) ;
      error_state_(3) = buffer_(3) ; error_state_(4) = buffer_(4) ; error_state_(5) = buffer_(5) ;
      // error_state_(6) = buffer_(6) ; error_state_(7) = buffer_(7) ; error_state_(8) = buffer_(8) ;
      // error_state_(9) += buffer_(9) ; error_state_(10) += buffer_(10) ; error_state_(11) += buffer_(11) ;
      // error_state_(12) += buffer_(12) ; error_state_(13) += buffer_(13) ; error_state_(14) += buffer_(14) ;
      // error_state_ =  buffer_;
      // std::cout << "error state (after orientation measurement) = \n" << error_state_ << std::endl;
      kalmancorrection();
      std::cout << "Orientation sensor measurement aidment" << std::endl;
    }
    else
    {
      // If the update fails update at leat the prediction
      // updatePrediction();
    }
  }
}

void EkfSlamAuv::velocityUpdate(const std::string sensor_id,
                                const double time_stamp,
                                const Eigen::VectorXd velocity,
                                const Eigen::MatrixXd velocity_cov,
                                const Eigen::MatrixXd gyro_cov)
{
  if (init_imu_ )
  {
    // if (_transformations.find(sensor_id) != _transformations.end())
    // {
    //     // Transform position to vehicle frame
    //     velocity_tmp = transformations::linearVelocity(velocity,
    //                                              auv_angular_velocity_,
    //                                              _transformations[ sensor_id ].first,
    //                                              _transformations[ sensor_id ].second);
    // }
    // else
    // {
    //std::cout << "EkfSlamAuv warning: DVL data stored without appropriate TF\n";
    // }

    // Create velocity measure matrices
    Eigen::VectorXd z;
    Eigen::MatrixXd R, H, V;
    createVelocityMeasure(velocity, velocity_cov, gyro_cov,
                          z, R, H, V);

    // Predict and apply update
    if (makePrediction(time_stamp))
    // {
      if (applyUpdate(z, R, H, V, -10.0))
      {
        Eigen::VectorXd buffer_ ;
        buffer_ = resetStateVector() ;
        // error_state_(0) = buffer_(0) ; error_state_(1) = buffer_(1) ; error_state_(2) = buffer_(2) ;
        // error_state_(3) = buffer_(3) ; error_state_(4) = buffer_(4) ; error_state_(5) = buffer_(5) ;
        error_state_(6) = buffer_(6) ; error_state_(7) = buffer_(7) ; error_state_(8) = buffer_(8) ;
        // error_state_(9) += buffer_(9) ; error_state_(10) += buffer_(10) ; error_state_(11) += buffer_(11) ;
        // error_state_(12) += buffer_(12) ; error_state_(13) += buffer_(13) ; error_state_(14) += buffer_(14) ;
        // error_state_ =  buffer_;
        kalmancorrection();
        std::cout << "DVL measurement aidment" << std::endl;
      }
      else
      {
        // If the update fails update at leat the prediction
        // updatePrediction();
      }
    // }
  std::cout << " n (gps)= " << velocity(0) << " n (state) = " << auv_body_velocity_(0) << std::endl;
  std::cout << " e (gps)= " << velocity(1) << " e (state) = " << auv_body_velocity_(1) << std::endl;
  std::cout << " d (gps)= " << velocity(2) << " d (state) = " << auv_body_velocity_(2) << std::endl;
  }
}

void EkfSlamAuv::createVelocityMeasure(const Eigen::VectorXd dvl_velocity,
                                       const Eigen::MatrixXd dvl_velocity_cov,
                                       const Eigen::MatrixXd gyro_cov,
                                       Eigen::VectorXd& z,
                                       Eigen::MatrixXd& R,
                                       Eigen::MatrixXd& H,
                                       Eigen::MatrixXd& V)

{

  // z.resize(4);

  // R.resize(4, 4);
  
  // H = Eigen::MatrixXd::Zero(4, 15);

  // V.resize(4, 4);
  // V = Eigen::MatrixXd::Identity(4,4);

  // Eigen::MatrixXd b(4, 3);
  // b.row(0) << 0, 0, cos(22*M_PI/180) ;
  // b.row(1) << cos(22*M_PI/180), sin(22*M_PI/180), cos(22*M_PI/180) ;
  // b.row(2) << 0, 0, cos(22*M_PI/180) ;
  // b.row(3) << -cos(22*M_PI/180), -sin(22*M_PI/180), cos(22*M_PI/180) ;

  // Eigen::MatrixXd l_dvl(3,4);
  // l_dvl.col(0) << 1.153, 0, 0.129 ;
  // l_dvl.col(1) << 1.153, 0, 0.129 ;
  // l_dvl.col(2) << 1.153, 0, 0.129 ;
  // l_dvl.col(3) << 1.153, 0, 0.129 ;
  
  // Eigen::MatrixXd b_ld_skew(4,3);
  // size_t i;
  // for (i=0; i<4; i++) { 
  //   b_ld_skew.block<1,3>(i,0) = b.row(i)*computeSkewSymmetryMatrix(l_dvl.col(i)) ;  
  // }
  
  // H.block<4,3>(0,6) = b ;

  // H.block<4,3>(0,12) = b_ld_skew;
  
  // // H(0,0) = -C(0,0); H(0,1) = -C(0,1); H(0,2) = -C(0,2);
  // // H(1,0) = -C(1,0); H(1,1) = -C(1,1); H(1,2) = -C(1,2);
  // // H(2,0) = -C(2,0); H(2,1) = -C(2,1); H(2,2) = -C(2,2);

  // // H(0,6) = -C(0,1)*zdot + (C(0,2)*ydot) ; H(0,7) = C(0,0)*zdot + (-C(0,2)*xdot) ; H(0,8) = -C(0,0)*ydot + (C(0,1)*xdot) ;
  // // H(1,6) = -C(1,1)*zdot + (C(1,2)*ydot) ; H(1,7) = C(1,0)*zdot + (-C(1,2)*xdot) ; H(1,8) = -C(1,0)*ydot + (C(1,1)*xdot) ;
  // // H(2,6) = -C(2,1)*zdot + (C(2,2)*ydot) ; H(2,7) = C(2,0)*zdot + (-C(2,2)*xdot) ; H(2,8) = -C(2,0)*ydot + (C(2,1)*xdot) ; 

  // Eigen::Matrix3d skew_l_dvl ;

  // for ( i=0; i<4; i++){
  //   skew_l_dvl = computeSkewSymmetryMatrix(l_dvl.col(i)) ;      
  //   z(i) = dvl_velocity(i) -   b.row(i)*(auv_body_velocity_ + computeSkewSymmetryMatrix(auv_angular_velocity_) * l_dvl.col(i))   ;    
  //   R(i,i) = b.row(i) * skew_l_dvl * gyro_cov * skew_l_dvl.transpose() * b.row(i).transpose() + dvl_velocity_cov(i,i) ; 
  // }
  
  z.resize(3);

  R.resize(3, 3);
  R = dvl_velocity_cov;
  
  H = Eigen::MatrixXd::Zero(3, 15);

  V.resize(3, 3);
  V = Eigen::MatrixXd::Identity(3,3);
  
  // H.block<3,3>(0,3) = auv_Cpt_.inverse() * computeSkewSymmetryMatrix(auv_ned_velocity_);
  H(0,6) = 1.0;
  H(1,7) = 1.0;
  H(2,8) = 1.0;

  z = dvl_velocity - auv_body_velocity_;

  // std::cout << "DVL 1 : " << (0) <<" - " << auv_ned_velocity_(0) << " : " << z(0) << "\n" ;
  // std::cout << "DVL 2 : " << velocity_temp(1) <<" - " << auv_ned_velocity_(1) << " : " << z(1) << "\n" ;
  // std::cout << "DVL 3 : " << velocity_temp(2) <<" - " << auv_ned_velocity_(2) << " : " << z(2) << "\n" ;
  // std::cout << "\n" ;
}

Eigen::MatrixXd EkfSlamAuv::computeF() const
{
  // State transition matrix
  
  Eigen::Vector3d position;
  Eigen::Vector3d orientation;
  Eigen::Vector3d body_velocity;
  Eigen::Vector3d angular_velocity;

  position = auv_position_;
  body_velocity = auv_body_velocity_;
  orientation = auv_orientation_;
  angular_velocity = auv_angular_velocity_;

  unsigned int f_size = 15;
  Eigen::MatrixXd F(f_size, f_size);
  F = Eigen::MatrixXd::Zero(f_size, f_size);

  /* 
  * Persamaan F12
  */
  Eigen::Vector3d ned_velocity;
  ned_velocity = auv_Cpt_ *body_velocity;
  ned_velocity = computeCpt() *body_velocity;

  F.block<3,3>(0,3) = -computeSkewSymmetryMatrix(ned_velocity);

  /* 
   * Persamaan F13
  */
  F.block<3,3>(0,6) = auv_Cpt_;
  F.block<3,3>(0,6) = computeCpt();

  /* 
   * Persamaan F22
  */
  F.block<3,3>(3,3) = Eigen::MatrixXd::Zero(3,3);

  /* 
   * Persamaan F25
  */
  F.block<3,3>(3,12) = -auv_Cpt_;
  F.block<3,3>(3,12) = -computeCpt();

  /* 
   * Persamaan F32
  */

  F.block<3,3>(6,3) = Eigen::MatrixXd::Zero(3,3);

  /* 
   * Persamaan F33
  */
  Eigen::Matrix3d skew_angular_velocity;
  skew_angular_velocity = computeSkewSymmetryMatrix(auv_angular_velocity_);
  F.block<3,3>(6,6) = - skew_angular_velocity;

  /* 
   * Persamaan F34
  */
  F.block<3,3>(6,9) = -Eigen::MatrixXd::Identity(3,3);

  /* 
   * Persamaan F35
  */
  F.block<3,3>(6,12) = -computeSkewSymmetryMatrix(auv_body_velocity_);

  return F;
}

Eigen::MatrixXd EkfSlamAuv::computeA(const double t) const
{
  // State transition matrix
  
  Eigen::Vector3d position;
  Eigen::Vector3d orientation;
  Eigen::Vector3d body_velocity;
  Eigen::Vector3d angular_velocity;

  position = auv_position_;
  body_velocity = auv_body_velocity_;
  orientation = auv_orientation_;
  angular_velocity = auv_angular_velocity_;

  unsigned int a_size = 15;
  Eigen::MatrixXd A(a_size, a_size);
  A = Eigen::MatrixXd::Identity(a_size, a_size);

  /* 
  * Persamaan F12
  */

  // auv_Cpt_ = computeCpt();

  Eigen::Vector3d ned_velocity;
  ned_velocity = auv_Cpt_ *body_velocity;
  ned_velocity = computeCpt() *body_velocity;
  
  A.block<3,3>(0,3) = -computeSkewSymmetryMatrix(ned_velocity)*t;

  /* 
   * Persamaan F13
  */
  A.block<3,3>(0,6) = auv_Cpt_*t;
  A.block<3,3>(0,6) = computeCpt()*t;

  // /* 
  //  * Persamaan F22
  // */
  // // double w_ie = 0.00007292115; // Earth's angular rate in rad/s
  // // Eigen::Vector3d w_ie_t;
  // // Eigen::Vector3d scaling;
  // // scaling << cos(latitude_), 0, -sin(latitude_);
  // // w_ie_t = w_ie * scaling;
  // // Eigen::Matrix3d skeww_ie_t_ = computeSkewSymmetryMatrix(w_ie_t_);
  // // A.block<3,3>(3,3) = skeww_ie_t_*t;

  /* 
   * Persamaan F25
  */
  A.block<3,3>(3,12) = -auv_Cpt_*t;
  A.block<3,3>(3,12) = -computeCpt()*t;

  /* 
   * Persamaan F32
  */
  // double e =  0.0818191908425;
  // double R0 = 6378137;
  // double g0 = 9.7803253359*(1 + 0.001931853*pow(sin(latitude_), 2))/sqrt(1-pow(e,2)*pow(sin(latitude_), 2));
  // double Re = R0 / sqrt(1-pow(e,2)*pow(sin(latitude_), 2));
  // double r_eS = Re * sqrt(pow(cos(latitude_), 2) + pow(1-pow(e,2),2) * pow(sin(latitude_), 2));

  // Eigen::Vector3d down_unit_vector(0,0,1);
  // Eigen::Vector3d gravity_vector;
  // gravity_vector = g0 * down_unit_vector;

  // Eigen::Matrix3d buffer1, buffer2;
  // Eigen::Matrix3d Ctp;
  // Ctp = auv_Cpt_.inverse();
  // buffer1 = computeSkewSymmetryMatrix(gravity_vector) + w_ie_t_*(auv_Cpt_*body_velocity).transpose();
  // buffer2 = (w_ie_t_.dot(auv_Cpt_*body_velocity))*Eigen::MatrixXd::Identity(3,3);
  A.block<3,3>(6,3) = Eigen::MatrixXd::Zero(3,3);

  /* 
   * Persamaan F33
  */
  Eigen::Matrix3d skew_angular_velocity;
  skew_angular_velocity = computeSkewSymmetryMatrix(auv_angular_velocity_);
  A.block<3,3>(6,6) = Eigen::MatrixXd::Identity(3,3) - skew_angular_velocity*t;

  /* 
   * Persamaan F34
  */
  A.block<3,3>(6,9) = -Eigen::MatrixXd::Identity(3,3)*t;

  /* 
   * Persamaan F35
  */
  A.block<3,3>(6,12) = -computeSkewSymmetryMatrix(auv_body_velocity_)*t;


  // /* Persamaan F23
  //  * Dari buku Principles of GNSS halaman 381
  //  * Perhitungan g0, Re, dan r_eS ada di Principles bab 2
  // */
  // double e =  0.0818191908425;
  // double R0 = 6378137;
  // double g0 = 9.7803253359*(1 + 0.001931853*pow(sin(latitude_), 2))/sqrt(1-pow(e,2)*pow(sin(latitude_), 2));
  // double Re = R0 / sqrt(1-pow(e,2)*pow(sin(latitude_), 2));
  // double r_eS = Re * sqrt(pow(cos(latitude_), 2) + pow(1-pow(e,2),2) * pow(sin(latitude_), 2));
  // A.block<3,3>(3,6) = t*(2*g0/r_eS)*r*r.transpose()/r.squaredNorm();



  // unsigned int a_size = 9 ;
  // Eigen::MatrixXd A(a_size, a_size);
  // A = Eigen::MatrixXd::Identity(a_size, a_size);
  // A(0, 3) = cos(pitch)*cos(yaw)*t;
  // A(0, 4) = -cos(roll)*sin(yaw)*t + sin(roll)*sin(pitch)*cos(yaw)*t;
  // A(0, 5) = sin(roll)*sin(yaw)*t + cos(roll)*sin(pitch)*cos(yaw)*t;

  // A(1, 3) = cos(pitch)*sin(yaw)*t;
  // A(1, 4) = cos(roll)*cos(yaw)*t + sin(roll)*sin(pitch)*sin(yaw)*t;
  // A(1, 5) = -sin(roll)*cos(yaw)*t + cos(roll)*sin(pitch)*sin(yaw)*t;

  // A(2, 3) = -sin(pitch)*t;
  // A(2, 4) = sin(roll)*cos(pitch)*t;
  // A(2, 5) = cos(roll)*cos(pitch)*t;

  // // A(0,6) = 0;
  // A(0,7) = (udot*(-sin(pitch)*t) + vdot*(sin(roll)*cos(pitch)*t) + wdot*(cos(roll)*cos(pitch)*t));
  // A(0,8) = -(udot*(cos(pitch)*sin(yaw)*t) + vdot*(cos(roll)*cos(yaw)*t + sin(roll)*sin(pitch)*sin(yaw)*t) + wdot*(-sin(roll)*cos(yaw)*t + cos(roll)*sin(pitch)*sin(yaw)*t));

  // // A(1,6) = 0;
  // A(1,6) = -(udot*(-sin(pitch)*t) + vdot*(sin(roll)*cos(pitch)*t) + wdot*(cos(roll)*cos(pitch)*t));
  // A(1,8) = (udot*(cos(pitch)*cos(yaw)*t) + vdot*(-cos(roll)*sin(yaw)*t + sin(roll)*sin(pitch)*cos(yaw)*t) + wdot*(sin(roll)*sin(yaw)*t + cos(roll)*sin(pitch)*cos(yaw)*t));

  // // A(2,6) = 0;
  // A(2,6) = (udot*(cos(pitch)*sin(yaw)*t) + vdot*(cos(roll)*cos(yaw)*t + sin(roll)*sin(pitch)*sin(yaw)*t) + wdot*(-sin(roll)*cos(yaw)*t + cos(roll)*sin(pitch)*sin(yaw)*t)); 
  // A(2,7) = -(udot*(cos(pitch)*cos(yaw)*t) + vdot*(-cos(roll)*sin(yaw)*t + sin(roll)*sin(pitch)*cos(yaw)*t) + wdot*(sin(roll)*sin(yaw)*t + cos(roll)*sin(pitch)*cos(yaw)*t)); 

    
  return A;
}

Eigen::MatrixXd EkfSlamAuv::computeG() const
{
  Eigen::MatrixXd G(15, 12);
  G = Eigen::MatrixXd::Zero(15, 12);

  /* 
   * Persamaan G22
  */
  G.block<3,3>(3,3) = -auv_Cpt_;
  G.block<3,3>(3,3) = -computeCpt();

  /* 
   * Persamaan G31
  */
  G.block<3,3>(6,0) = -Eigen::MatrixXd::Identity(3,3);
 
  /* 
   * Persamaan G32
  */
  G.block<3,3>(6,3) = -computeSkewSymmetryMatrix(auv_body_velocity_);
    
  /* 
   * Persamaan G43
  */
  G.block<3,3>(9,6) = Eigen::MatrixXd::Identity(3,3);

  /* 
  * Persamaan G54
  */
  G.block<3,3>(12,9) = Eigen::MatrixXd::Identity(3,3);

  return G;
}

Eigen::MatrixXd EkfSlamAuv::computeCpt(void) const
{
  Eigen::MatrixXd Cpt(3, 3);
  double roll = auv_orientation_(0);
  double pitch = auv_orientation_(1);
  double yaw = auv_orientation_(2);

  Cpt(0,0) = cos(pitch)*cos(yaw);  Cpt(0,1) = sin(roll)*sin(pitch)*cos(yaw) - cos(roll)*sin(yaw);    Cpt(0,2) = cos(roll)*sin(pitch)*cos(yaw) + sin(roll)*sin(yaw);
  Cpt(1,0) = cos(pitch)*sin(yaw);  Cpt(1,1) = cos(roll)*cos(yaw) + sin(roll)*sin(pitch)*sin(yaw);    Cpt(1,2) = -sin(roll)*cos(yaw) + cos(roll)*sin(pitch)*sin(yaw);
  Cpt(2,0) = -sin(pitch);          Cpt(2,1) = sin(roll)*cos(pitch);                                  Cpt(2,2) = cos(roll)*cos(pitch); 
  return Cpt;
}

Eigen::MatrixXd EkfSlamAuv::computeSkewSymmetryMatrix(const Eigen::VectorXd x) const
{
  Eigen::MatrixXd skew_symmetry(3,3);
  skew_symmetry= Eigen::MatrixXd::Zero(3,3);
  skew_symmetry(0,1) = -x(2);   skew_symmetry(1,0) = x(2);
  skew_symmetry(0,2) = x(1);    skew_symmetry(2,0) = -x(1);
  skew_symmetry(1,2) = -x(0);   skew_symmetry(2,1) = x(0);
  return skew_symmetry;
}