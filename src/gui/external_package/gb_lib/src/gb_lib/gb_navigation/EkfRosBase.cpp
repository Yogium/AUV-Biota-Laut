#include "gb_lib/gb_navigation/EkfRosBase.h"

EkfRosBase::EkfRosBase(const std::string name):
    name_(name)
{   pub_nav_cov_ = n_.advertise<auv_msgs::NavCov>("/gb_navigation/nav_cov", 1);
    pub_odom_ = n_.advertise<nav_msgs::Odometry>("/gb_navigation/odometry", 1);
    pub_nav_sts_ = n_.advertise< auv_msgs::NavSts >("/gb_navigation/nav_sts", 1);
}

void EkfRosBase::publish(const ros::Time& stamp)
{
    world_frame_id_ = "world_ned";
    vehicle_frame_id_ = "GaneshBlue/nav_solution";
    Eigen::Vector3d orientation ;
    Eigen::Vector3d angular_velocity;
    Eigen::Vector3d linear_acceleration ;
    Eigen::Vector3d linear_velocity ;
    Eigen::Vector3d position ;
    Eigen::Vector3d latlonh;
    int8_t gps_status;

    ekf_slam_auv_->getData(orientation,
                            angular_velocity,
                            linear_acceleration,
                            linear_velocity,
                            position,
                            latlonh,
                            gps_status);
                            
    // TODO: Konfigurasi sementara untuk benerin posisi North yang kebalik
    bool inverseNorth;
    if(n_.getParam("navigator/inverse_north", inverseNorth)) {
        position(0) = -position(0);
    }
    // TODO

    // Publish Odometry message
    nav_msgs::Odometry odom;
    odom.header.frame_id = "world_ned" ;
    odom.header.stamp = stamp;
    odom.pose.pose.position.x = position(0);
    odom.pose.pose.position.y = position(1);
    odom.pose.pose.position.z = position(2);
    odom.pose.pose.orientation = tf::createQuaternionMsgFromRollPitchYaw(
										orientation(0),
										orientation(1),
										orientation(2) );
    odom.twist.twist.linear.x = linear_velocity(0);
    odom.twist.twist.linear.y = linear_velocity(1);
    odom.twist.twist.linear.z = linear_velocity(2);
    odom.twist.twist.angular.x = angular_velocity(0);
    odom.twist.twist.angular.y = angular_velocity(1);
    odom.twist.twist.angular.z = angular_velocity(2);

    pub_odom_.publish(odom);

    // Publish Nav Covariance
    auv_msgs::NavCov nav_cov;
    Eigen::MatrixXd P(15,15);
    P = ekf_slam_auv_->getCovarianceMatrix() ;
    nav_cov.position_variance.x      = P(0,0);
    nav_cov.position_variance.y      = P(1,1);
    nav_cov.position_variance.z      = P(2,2);
    nav_cov.orientation_variance.x   = P(3,3);
    nav_cov.orientation_variance.y   = P(4,4);
    nav_cov.orientation_variance.z   = P(5,5);
    nav_cov.body_velocity_variance.x = P(6,6);
    nav_cov.body_velocity_variance.y = P(7,7);
    nav_cov.body_velocity_variance.z = P(8,8);
    nav_cov.ba_variance.x            = P(9,9);
    nav_cov.ba_variance.y            = P(10,10);
    nav_cov.ba_variance.z            = P(11,11);
    nav_cov.bg_variance.x            = P(12,12);
    nav_cov.bg_variance.y            = P(13,13);
    nav_cov.bg_variance.z            = P(14,14);    
    pub_nav_cov_.publish(nav_cov);

    // Publish Nav Status
    auv_msgs::NavSts nav_sts;
    nav_sts.header.frame_id = "GaneshBlue/nav_solution";
    nav_sts.header.stamp = stamp;

    Eigen::Vector3d body_velocity ;
    
    body_velocity = linear_velocity ;

    nav_sts.body_velocity.x = body_velocity(0);
    nav_sts.body_velocity.y = body_velocity(1);
    nav_sts.body_velocity.z = body_velocity(2);

    if (gps_status >= 0) {
        nav_sts.global_position.latitude = latlonh(0);
        nav_sts.global_position.longitude = latlonh(1);
    }
    else
    {
        double lat, lon, height;
        ned_->ned2Geodetic(position(0),
                           position(1),
                           position(2),
                           lat, lon, height);
        nav_sts.global_position.latitude = lat;
        nav_sts.global_position.longitude = lon;
    }

    nav_sts.orientation.roll = orientation(0);
    nav_sts.orientation.pitch = orientation(1);
    nav_sts.orientation.yaw = orientation(2);

    nav_sts.orientation_rate.roll = angular_velocity(0);
    nav_sts.orientation_rate.pitch = angular_velocity(1);
    nav_sts.orientation_rate.yaw = angular_velocity(2);

    nav_sts.origin.latitude = init_latitude_;
    nav_sts.origin.longitude = init_longitude_;

    nav_sts.position.north = position(0);
    nav_sts.position.east = position(1);
    nav_sts.position.depth = position(2);

    // Publish vehicle TF
    tf::Transform tf_vehicle;
    tf_vehicle.setOrigin(tf::Vector3(odom.pose.pose.position.x,
                                    odom.pose.pose.position.y,
                                    odom.pose.pose.position.z));
    tf_vehicle.setRotation(tf::Quaternion(odom.pose.pose.orientation.x,
                                        odom.pose.pose.orientation.y,
                                        odom.pose.pose.orientation.z,
                                        odom.pose.pose.orientation.w));
    br_.sendTransform(tf::StampedTransform(tf_vehicle, stamp, world_frame_id_, vehicle_frame_id_));


    pub_nav_sts_.publish(nav_sts);
}
    


