#!/usr/bin/env python

import rospy
import socket
import json
from sensor_msgs.msg import NavSatFix
from gb_msgs.msg import Valeport_Altimeter

class TCPDirectStreamer:
    def __init__(self):
        # Initialize the ROS node
        rospy.init_node('tcp_direct_streamer_node', anonymous=True)

        # --- TCP Socket Configuration ---
        self.tcp_ip = '192.168.2.105'
        self.tcp_port = 9191  # CHANGE THIS to match your receiving server's port
        self.sock = None
        
        # Initialize data variables
        self.latitude = 0.0
        self.longitude = 0.0
        self.depth = 0.0

        # Attempt initial TCP connection
        self.connect_tcp()

        # Subscribe directly to the raw sensor topics (Independent of the GUI)
        rospy.Subscriber('/gb_navigation/spatial/Gps', NavSatFix, self.gps_callback)
        rospy.Subscriber('/gb_navigation/altimeter', Valeport_Altimeter, self.altimeter_callback)

        # Set up a timer to send data at a fixed rate (e.g., 2 Hz or every 0.5 seconds)
        self.timer = rospy.Timer(rospy.Duration(0.5), self.send_tcp_data)

        rospy.loginfo("TCP Direct Streamer Node Started.")

    def connect_tcp(self):
        """Establishes the TCP connection to the specified IP and Port."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0) # 2 second timeout for connection attempts
            self.sock.connect((self.tcp_ip, self.tcp_port))
            rospy.loginfo("Successfully connected to TCP server at %s:%s", self.tcp_ip, self.tcp_port)
        except Exception as e:
            rospy.logwarn("Failed to connect to TCP server %s:%s. Retrying... Error: %s", self.tcp_ip, self.tcp_port, str(e))
            self.sock = None

    def gps_callback(self, data):
        """Updates latitude and longitude from the raw GPS topic."""
        self.latitude = data.latitude
        self.longitude = data.longitude

    def altimeter_callback(self, data):
        """Updates depth from the raw Altimeter topic."""
        self.depth = data.depth

    def send_tcp_data(self, event):
        """Packages the data as JSON and sends it over the socket."""
        # Reconnect if the socket dropped or hasn't connected yet
        if self.sock is None:
            self.connect_tcp()
            if self.sock is None:
                return

        # Prepare the payload
        payload = {
            "latitude": round(self.latitude, 8),
            "longitude": round(self.longitude, 8),
            "depth": round(self.depth, 2)
        }
        
        # Convert dictionary to string and add a newline as a delimiter
        message = json.dumps(payload) + "\n"

        try:
            # Send the encoded data
            self.sock.sendall(message.encode('utf-8'))
        except socket.error as e:
            rospy.logerr("Connection lost. Failed to send data: %s", str(e))
            self.sock.close()
            self.sock = None  # Reset socket to trigger reconnection on the next timer tick

    def cleanup(self):
        """Closes the socket upon node shutdown."""
        if self.sock:
            self.sock.close()
            rospy.loginfo("TCP socket closed.")

if __name__ == '__main__':
    try:
        streamer = TCPDirectStreamer()
        # Register the cleanup function to run when CTRL+C is pressed
        rospy.on_shutdown(streamer.cleanup)
        # Keep the node running
        rospy.spin()
    except rospy.ROSInterruptException:
        pass