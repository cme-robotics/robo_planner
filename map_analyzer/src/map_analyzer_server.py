#!/usr/bin/env python
'''
Created on Jan 28, 2016

@author: cme
'''
#****************************************************************
# \file
#
# \note
# Copyright (c) 2016 \n
# Fraunhofer Institute for Manufacturing Engineering
# and Automation (IPA) \n\n
#
#*****************************************************************
#
# \note
# Project name: Care-O-bot
# \note
# ROS stack name: ipa_pars
# \note
# ROS package name: map_analyzer
#
# \author
# Author: Christian Ehrmann
# \author
# Supervised by: Richard Bormann
#
# \date Date of creation: 01.2016
#
# \brief
#
#
#*****************************************************************
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer. \n
# - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution. \n
# - Neither the name of the Fraunhofer Institute for Manufacturing
# Engineering and Automation (IPA) nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission. \n
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License LGPL as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License LGPL for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License LGPL along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
#****************************************************************/
import rospy
import cv2
import cv
from sensor_msgs.msg import *
from sensor_msgs.msg._Image import Image


from cv_bridge import CvBridge, CvBridgeError
import actionlib
# Important notice: class and/or filename must not be same package name!
from map_analyzer.srv import MapAnalyzer
from map_analyzer.srv._MapAnalyzer import MapAnalyzerResponse, MapAnalyzerRequest
import ipa_room_segmentation
from ipa_room_segmentation.msg._MapSegmentationAction import *
from geometry_msgs.msg import Pose



class MapAnalyzerServer(object):
    def __init__(self):
        rospy.loginfo("Initialize MapAnalyzer ...")
        rospy.loginfo("... starting room_segmentation_client")
        self._roomsegclient = actionlib.SimpleActionClient('room_segmentation/room_segmentation_server', MapSegmentationAction)
        rospy.logwarn("Waiting for Segmentation Server to come available ...")
        self._roomsegclient.wait_for_server()
        rospy.logwarn("Server is online!")
        rospy.loginfo("... starting map_analyzer_service_server")
        self.map_srvs = rospy.Service('map_analyzer_service_server', MapAnalyzer, self.handle_map_cb)
        rospy.logwarn("Waiting for map_publisher_service_server to come available ...")
        rospy.wait_for_service('map_publisher_server')
        rospy.logwarn("Server online!")
        try:
            self.serviceMapPublisherClient = rospy.ServiceProxy('map_publisher_server', MapAnalyzer)
        except rospy.ServiceException, e:
            print "Service call failed: %s"%e
            
        rospy.loginfo("generating object instances")
        self.bridge = CvBridge()
        rospy.loginfo("... finished")
        
        
    def handle_map_cb(self, input_map):
        print "print recieved map header:"
        print input_map.map.header
        # first image input_map display in publisher
        answer = self.serviceMapPublisherClient(input_map)
        print "answer of pass through publisher call"
        print answer
        
        segmented_map_response = self.useRoomSegmentation(input_map)
        print "we received a segmented map:"
        print "its resolution is:"
        print segmented_map_response.map_resolution
        
        col_map = self.convertSegmentedMap(segmented_map_response)
        answer = self.serviceMapPublisherClient(col_map)
        print answer
        
        response = MapAnalyzerResponse()
        response.answer.data = "saftige Map Antwort!"
        return response
    
    def convertSegmentedMap(self, seg_map_as_index_map):
        #col_map = self.bridge.imgmsg_to_cv2(seg_map, desired_encoding="passthrough")
        output_msg = MapAnalyzerRequest()
        output_msg.map = seg_map_as_index_map
        # convertion in room_segmentation_server Mat!
        color_map = seg_map_as_index_map.segmented_map.clone()
        bridge = CvBridge()
        # TODO: here!
        
        print "information about my output!"
        print output_msg.map.header
        print output_msg.map.height
        print output_msg.map.width
        print output_msg.map.encoding
        print output_msg.map.is_bigendian
        print output_msg.map.step
        return output_msg
    
    def useRoomSegmentation(self, in_map):
        goal = ipa_room_segmentation.msg.MapSegmentationGoal()
        goal.input_map.header.seq = 1
        goal.input_map.header.stamp = rospy.Time.now()
        goal.input_map.header.frame_id = "mymapframe"
        goal.input_map = in_map.map
        # TODO: change this lines to use every map!
        goal.map_resolution = 0.05
        pose = Pose()
        pose.position.x = 0
        pose.orientation.y = 0
        pose.orientation.z = 0
        pose.orientation.x = 0
        pose.orientation.y = 0
        pose.orientation.z = 0
        pose.orientation.w = 0
        goal.map_origin = pose
        goal.return_format_in_pixel = True
        goal.return_format_in_meter = False
        goal.room_segmentation_algorithm = 2
        
        print "header and size of pic before room_segmentation"
        print goal.input_map.header
        print "width %d height %d = " % (goal.input_map.width , goal.input_map.height)
        
        rospy.loginfo("Wait for goal!")
        self._roomsegclient.send_goal(goal)
        rospy.loginfo("Waiting for result of MapSegmentationServer")
        self._roomsegclient.wait_for_result()
        solution = self._roomsegclient.get_result()
        rospy.loginfo("Received a result:")
        
        return solution
        
        
if __name__ == '__main__':
    rospy.init_node('map_analyzer_server_node', anonymous=False)
    mAS = MapAnalyzerServer()
    rospy.spin()
        