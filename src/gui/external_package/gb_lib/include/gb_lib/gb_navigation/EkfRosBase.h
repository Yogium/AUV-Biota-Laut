/*
 * Copyright (c) 2017 Iqua Robotics SL - All Rights Reserved
 *
 * This file is subject to the terms and conditions defined in file
 * 'LICENSE.txt', which is part of this source code package.
 */

#ifndef GB_LIB_INCLUDE_GB_LIB_GB_NAVIGATION_EKFROSBASE_H_
#define GB_LIB_INCLUDE_GB_LIB_GB_NAVIGATION_EKFROSBASE_H_

#include <ros/ros.h>
#include <nav_msgs/Odometry.h>
#include <auv_msgs/NavSts.h>
#include <auv_msgs/NavCov.h>

#include <string>
#include <vector>
#include <tf/transform_broadcaster.h>
#include <tf/transform_listener.h>
#include <tf_conversions/tf_eigen.h>


#include "./EkfSlamAuv.h"
#include "./Ned.h"

class EkfRosBase
{
 public:
  EkfRosBase(const std::string name);

  void publish(const ros::Time& stamp);

 protected:
  // EKF Slam AUV ptr
  EkfSlamAuv *ekf_slam_auv_;

  // Name
  std::string name_;

  // Node handle
  ros::NodeHandle n_;

  // Publisher
  ros::Publisher pub_odom_;
  ros::Publisher pub_nav_cov_;
  ros::Publisher pub_nav_sts_;

  // NED ptr
  Ned *ned_;
  double init_latitude_;
  double init_longitude_;

  tf::TransformBroadcaster br_;
  tf::TransformListener listener_;
  double altitude_;
  ros::Timer timer_create;

  std::string vehicle_frame_id_;
  std::string world_frame_id_;


};

#endif  // COLA2_LIB_INCLUDE_COLA2_LIB_COLA2_NAVIGATION_EKFROSBASE_H_