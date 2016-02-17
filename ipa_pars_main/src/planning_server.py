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
# ROS package name: ipa_pars_main
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
import actionlib
import rospy
import sys
import cv2
from cv_bridge import CvBridge, CvBridgeError
from ipa_pars_main.msg._LogicPlanAction import *

from sensor_msgs.msg._Image import Image
import sensor_msgs.msg
from map_analyzer.srv import MapAnalyzer
from cob_srvs.srv._SetString import SetString
from map_analyzer.srv._MapAnalyzer import MapAnalyzerResponse
from ipa_pars_main.srv._PlanData import PlanData, PlanDataRequest


class ParsServer(object):
    _feedback = ipa_pars_main.msg.LogicPlanFeedback()
    _result = ipa_pars_main.msg.LogicPlanResult()
    def __init__(self, path_to_map, path_to_domain):
        rospy.loginfo("Initialize ParsServer ...")
        self._path_to_map = path_to_map
        self._path_to_domain = path_to_domain
        rospy.loginfo("path_to_map: %s" % path_to_map)
        rospy.loginfo("path_to_domain: %s" % path_to_domain)
        rospy.loginfo("Reading map from disk ...")
        self.input_map = cv2.imread(self._path_to_map, cv2.IMREAD_COLOR)
        rospy.loginfo("converting map to sensor_msg ...")
        self.bridge = CvBridge()
        self.output_map = self.bridge.cv2_to_imgmsg(self.input_map, "bgr8")
        rospy.loginfo("... done!")
        rospy.logwarn("Waiting for map_analyzer_service_server to come available ...")
        rospy.wait_for_service('map_analyzer_service_server')
        rospy.logwarn("Server online!")
        rospy.wait_for_service('planning_controller_server')
        rospy.logwarn("Server online!")
        try:
            self.serviceClient = rospy.ServiceProxy('map_analyzer_service_server', MapAnalyzer)
        except rospy.ServiceException, e:
            print "Service call failed: %s"%e
        try:
            self.planning_controller_server = rospy.ServiceProxy('planning_controller_server', PlanData)
        except rospy.ServiceException, e:
            print "Service call faield: %s"%e
        
        self._as = actionlib.SimpleActionServer('pars_server', ipa_pars_main.msg.LogicPlanAction, execute_cb=self.execute_cb, auto_start=False)
        self._as.start()
        
        rospy.loginfo("ParsServer running! Waiting for a new goal.")

    def execute_cb(self, goal):
        rospy.loginfo("Executing a new goal!")
        rospy.loginfo("GOAL: %s , %s, %s " % (str(goal.goal_type), str(goal.what), str(goal.where)))
        rospy.loginfo("in progress ...")
        r = rospy.Rate(1)
        # change herer TODO:
        #===========================
        # robot stuff here
        room_information = self.sendImageToMapAnalyzerServer()
        #room_information = MapAnalyzerResponse()
        #room_information.answer.data = "room-1 room-2\nroom-2 room-1 room-3 room-4 room-5 room-10\nroom-3 room-2\nroom-4 room-2\nroom-5 room-2\nroom-6 room-7 room-10 room-11\nroom-7 room-10 room-11\nroom-8 room-9 room-11\nroom-9 room-8\nroom-10 room-2 room-6 room-7\nroom-11 room-6 room-7 room-8"

        #controller_request = PlanDataRequest()
        #controller_request.goal_data.data = str(goal.goal_type)
        #controller_request.room_data.data = room_information.answer.data
        #controller_request.domain_data.data = self.generate_debug_domain()
        #answer0 = self.planning_controller_server(controller_request)
        #print answer0
        #==========================================================
        #answer1 = self.room_info_client(room_information.answer.data)
        #print answer1
        #planning_goal_text = str(goal.goal_type)+" "+str(goal.what)+" "+goal.where
        #answer2 = self.planning_goal_server(planning_goal_text)
        #print answer2
        #planning_domain_text = "this is my domain information"
        #answer3 = self.planning_domain_server(planning_domain_text)
        #print answer3
        #==============================================
        print "i am sleeping now"
        success = True
        rospy.sleep(5)
        #===========================
        if self._as.is_preempt_requested():
            rospy.loginfo('%s: Preempted' % 'pars_server')
            success = False
        
        
        r.sleep()
        
        if success:
            self._result.success = True
            rospy.loginfo("Succeeded the Logic Plan")
            self._as.set_succeeded(self._result, "good job")
    
        
    def sendImageToMapAnalyzerServer(self):
        # TODO: add header and other meta data to message!
        img_msg_typ = Image()
        img_msg_typ.header.stamp = rospy.Time.now()
        img_msg_typ.header.frame_id = "planning_server_frame"
        #img_msg_typ.height = self.input_map.shape[1]
        img_msg_typ.height = self.input_map.shape[0]
        img_msg_typ.width = self.input_map.shape[1]
        img_msg_typ.data = self.output_map.data
        img_msg_typ.encoding = "rgb8"
        byte_depth = 3
        img_msg_typ.is_bigendian = False
        img_msg_typ.step = img_msg_typ.width * byte_depth
        print "This is the header i want to use"
        print img_msg_typ.header
        answer = self.serviceClient(img_msg_typ)
        print "answer"
        print answer
        return answer
    
    def generate_debug_domain(self):
        print "read input file"
        listOfInput = []
        try:
            fileObject = open(self._path_to_domain+"domain.pddl", "r")
            with fileObject as listOfText:
                listOfInput = listOfText.readlines()
            fileObject.close()
        except IOError:
            rospy.loginfo("open file failed or readLine error")
        StringOfObjects = str(" ").join(map(str, listOfInput))
        domain_text = StringOfObjects
        return domain_text

if __name__ == '__main__':
    rospy.init_node('planning_server', anonymous=False)
    pARS = ParsServer(sys.argv[1], sys.argv[2])
    rospy.spin()
