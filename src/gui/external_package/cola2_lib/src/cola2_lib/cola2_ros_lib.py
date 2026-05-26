#!/usr/bin/env python
# Copyright (c) 2019 Iqua Robotics SL - All Rights Reserved
#
# This file is subject to the terms and conditions defined in file
# 'LICENSE.txt', which is part of this source code package.

from __future__ import print_function
import rospy
import tf
from numpy import rad2deg

from auv_msgs.msg import BodyVelocityReq, GoalDescriptor
from std_srvs.srv import Empty, EmptyResponse, EmptyRequest

from diagnostic_msgs.msg import DiagnosticStatus
from diagnostic_msgs.msg import KeyValue
from diagnostic_msgs.msg import DiagnosticArray


# Simple service for enabling/disabling a node. See a use case in
# enrics_robot_code (stack)/cirs_cpp (package)/cliff_following_bh.py
class Enabler:
    def __init__(self):
        self.enabled = False

    def enable(self, req):
        self.enabled = True
        return EmptyResponse()

    def disable(self, req):
        self.enabled = False
        return EmptyResponse()

    def setEnabled(self, e):
        self.enabled = e

    def isEnabled(self):
        return self.enabled


# Empty config object, comes handy sometimes
class Config(object): pass

def get_ros_params(obj, params):
    """
    Ease param loading from server by assigning them as attributes to the specified object.
    Param names are treated as absoulte if started by /.
    Otherwise they are assumed to be private and namespace and node name are automatically added.

    :param obj: object where to set attributes (self.*)
    :param params: dictionary of {'attribute': ['param_name', default_value]}
    :return: all params found in the param server
    """
    name = rospy.get_name()
    valid = True
    for key in params:
        # Param is in param server
        param_name, param_default = params[key]
        # If not absolute, load with ns and node name
        if param_name[0] != '/':
            param_name = name + '/' + param_name
        if rospy.has_param(param_name):
            # Get from param server
            param_value = rospy.get_param(param_name)
            setattr(obj, key, param_value)
        else:
            # Display message default value loaded
            rospy.logwarn(param_name + ": set to default value = " + str(param_default))
            setattr(obj, key, param_default)
            valid = False
    return valid

# getRosParams:
#   obj: object for which to set its attributes
#   params: dictionary of {'key': 'value'} pairs defining the attribute
#      name that'll be set and the name of the ROS param that'll be
#      assigned to it
#   [node_name]: optional ROS node name of the node for which the params
#      are retrieved
def getRosParams(obj, params, node_name=None):
    valid_config = True
    for key in params:
        if rospy.has_param(params[key]):
            param_value = rospy.get_param(params[key])
            setattr(obj, key, param_value)
        else:
            valid_config = False
            if node_name == None:
                rospy.logfatal(params[key] + " parameter not found")
            else:
                rospy.logfatal(node_name + ": " + params[key] + " parameter not found")
    return valid_config


# getRosParamsWithDefaults:
#   obj: object for which to set its attributes
#   params: dictionary of
#      {'attr_name': {'name': 'actual_name', default: default_value}
#      pairs defining the attribute name that'll be set, the name of the
#      ROS param that'll be assigned to it and its default value if
#      the ROS param is not found on the param server
#   [node_name]: optional ROS node name of the node for which the params
#      are retrieved
def getRosParamsWithDefaults(obj, params, node_name=None):
    valid_config = True
    for key in params:
        if rospy.has_param(params[key]['name']):
            param_value = rospy.get_param(params[key]['name'])
            setattr(obj, key, param_value)
        else:
            valid_config = False
            setattr(obj, key, params[key]['default'])
            if node_name == None:
                rospy.logfatal(params[key]['name'] + " param not found")
            else:
                rospy.logfatal(node_name + ": " + params[key]['name'] + " param not found")
    return valid_config


def requestBodyVelocity(vx, vy, vz, vyaw, pub):
    # Function for steering the robot at the low level

    #print ("(vx,vy,vz,vyaw) = ", vx,vy,vz,vyaw)

    # Build BodyVelocityReq message according to params
    message = BodyVelocityReq()

    message.header.stamp = rospy.Time.now()

    message.goal.priority = GoalDescriptor.PRIORITY_NORMAL_HIGH
    message.goal.requester = rospy.get_name()

    message.twist.linear.x = vx
    message.twist.linear.y = vy
    message.twist.linear.z = vz
    message.twist.angular.z = vyaw

    message.disable_axis.x = False
    message.disable_axis.y = False
    message.disable_axis.z = False
    message.disable_axis.roll = True
    message.disable_axis.pitch = True
    message.disable_axis.yaw = False

    # Publish built message
    rospy.loginfo(rospy.get_name()+": publishing BodyVelocityReq message")
    pub.publish(message)


class TransformHandler(object):
    """The TransformHandler class queries and saves transforms with origin at the vehicle frame."""

    def __init__(self):
        """Constructor that queries the namespace to know vehicle frame."""
        self.transforms = dict()  # transforms from the robot to the sensors
        self.tf_listener = tf.TransformListener()  # transform listener
        self.frame_vehicle = "GaneshBlue/base_link"  # vehicle frame

    def get_transform(self, frame):
        """Get a static transform from the map or query the listener and save."""
        # Return identity when frame is vehicle frame
        if frame == self.frame_vehicle:
            return True, [0., 0., 0.], [0., 0., 0.]
        # Look for the transform
        if frame in self.transforms:
            # Found in map
            xyz, rpy = self.transforms[frame]
            return True, xyz, rpy
        else:
            # Need to query it
            ok, xyz, rpy = self.get_dynamic_transform(frame)
            if ok:
                self.transforms[frame] = (xyz, rpy)
                rospy.loginfo("Transform Handler added: {:s}".format(frame))
                rospy.loginfo("trans: {:.3f} {:.3f} {:.3f}".format(*xyz))
                rpy_deg = [rad2deg(v) for v in rpy]
                rospy.loginfo("rpy_deg: {:.3f} {:.3f} {:.3f}".format(*rpy_deg))
                return True, xyz, rpy
        return False, [0., 0., 0.], [0., 0., 0.]

    def get_dynamic_transform(self, frame):
        """Get a transform by querying the listener."""
        # Return identity when frame is vehicle frame
        if frame == self.frame_vehicle:
            return True, [0., 0., 0.], [0., 0., 0.]
        # Look for the transform
        try:
            self.tf_listener.waitForTransform(self.frame_vehicle, frame, rospy.Time(0),rospy.Duration(0.5))
            (xyz, quat) = self.tf_listener.lookupTransform(self.frame_vehicle, frame, rospy.Time(0))
            rpy = tf.transformations.euler_from_quaternion(quat)
            return True, xyz, rpy
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            rospy.logfatal("Unable to get dynamic transform: {:s}".format(frame))
            return False, [0., 0., 0.], [0., 0., 0.]

class DiagnosticHelper(object):
    """
    Helper class to work with ROS diagnostics. Manages the publishing of the diagnostics,
    the addition/supression of diagnostic entries and checks its publishing frequency.
    """

    def __init__(self, name, hw_id, topic='diagnostics', desired_freq=1000, max_freq_error=10):

        # Diagnostic publisher, will get resolved to [vehicle_name]/diagnostics
        self.pub_diagnostic = rospy.Publisher(rospy.get_namespace() + topic,
                                              DiagnosticArray,
                                              queue_size=2)

        # Sets the name and hardware id of the DiagnosticStatus message
        self.diagnostic = DiagnosticStatus()
        # Keep only last name (remove namespace)
        self.diagnostic.name = name.split('/')[-1]
        self.diagnostic.hardware_id = hw_id

        # Initialization of vars to check the frequency
        self.counter = -1
        self.desired_freq = desired_freq
        self.max_freq_error = max_freq_error

    def set_level(self, level, message="none"):
        """ Sets the level and the message of the Diagnostics message """
        self.diagnostic.level = level
        if message == "none":
            if level == DiagnosticStatus.OK:
                self.diagnostic.message = "Ok"
            elif level == DiagnosticStatus.WARN:
                self.diagnostic.message = "Warning"
            else:
                self.diagnostic.message = "Error"
        else:
            self.diagnostic.message = message

        # Publish diagnostic message
        self.publish()

    def add(self, key, value):
        """ Add a diagnostics entry """
        found = False
        i = 0
        while i < len(self.diagnostic.values) and not found:
            if self.diagnostic.values[i].key == key:
                self.diagnostic.values[i].value = value
                found = True
            else:
                i = i + 1

        if not found:
            self.diagnostic.values.append(KeyValue(key, value))

    def remove(self, key, value):
        """ Remove a diagnostics entry """
        found = False
        i = 0
        while i < len(self.diagnostic.values) and not found:
            if self.diagnostic.values[i].key == key:
                found = True
            else:
                i = i + 1

        if found:
            self.diagnostic.values.remove(self.diagnostic.values[i])

    def publish(self):
        """ Publish the diagnostic message """
        diagnostic_array = DiagnosticArray()
        diagnostic_array.header.stamp = rospy.Time.now()
        diagnostic_array.status.append(self.diagnostic)
        self.pub_diagnostic.publish(diagnostic_array)

    def check_frequency(self):
        """ This method is designed to be called from an external node in each iteration.
            If the iteration frequency does not agree with the frequency set at the
            initialization a warning diagnostic message is published. """

        if self.counter == -1:
            self.init_period = rospy.Time.now()

        self.counter = self.counter + 1

        if self.counter == self.desired_freq:
            now = rospy.Time.now()
            period = (now - self.init_period).to_sec()

            self.add("frequency: ", str(self.desired_freq / period))
            if abs(period - 1.0) < (self.max_freq_error / 100.0):
                self.set_level(DiagnosticStatus.OK)
            else:
                self.set_level(DiagnosticStatus.WARN, "Invalid frequency!")
            self.publish()
            self.counter = 0
            self.init_period = now



