#!/usr/bin/env python
'''
Created on Feb 04, 2016

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
# ROS package name: planning_domain
#
# \author
# Author: Christian Ehrmann
# \author
# Supervised by: Richard Bormann
#
# \date Date of creation: 02.2016
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
import sys
import cv2
import numpy as np
from sensor_msgs.msg import Image
#from sensor_msgs.msg._Image import Image

import actionlib

from cob_srvs.srv._SetString import SetString
from cob_srvs.srv._SetString import SetStringResponse


class PlanDomainClass(object):
    def __init__(self, path_to_inputfile):
        rospy.loginfo("Initialize PlanDomainClass ...")
        self.path_to_inputfile = path_to_inputfile
        rospy.loginfo(path_to_inputfile)
        self.domain_srv = rospy.Service('planning_domain_server', SetString, self.handle_domain_cb)
        self.domain_info = ""
        
        rospy.logwarn("Waiting for planning_solver_domain_server to come available ...")
        rospy.wait_for_service('planning_solver_domain_server')
        rospy.logwarn("Server online!")
        try:
            self.domain_solver_client = rospy.ServiceProxy('planning_solver_domain_server', SetString)
        except rospy.ServiceException, e:
            print "Service call failed: %s"%e
        
        rospy.loginfo("PlanDomainServer is running, waiting for new problems to plan ...")
        rospy.loginfo("... finished")
        
    def handle_domain_cb(self, domain_info):
        print "domain_info"
        print domain_info
        self.domain_info = self.generate_debug_domain()
        print self.domain_info
        
        answer = self.domain_solver_client(self.domain_info)
        
        print answer
        response = SetStringResponse()
        response.success = True
        response.message = "ErrorAnswer"
        
        return response
    
    def generate_debug_domain(self):
        print "read input file"
        listOfInput = []
        try:
            fileObject = open(self.path_to_inputfile+"domain.pddl", "r")
            with fileObject as listOfText:
                listOfInput = listOfText.readlines()
            fileObject.close()
        except IOError:
            rospy.loginfo("open file failed or readLine error")
        StringOfObjects = str(" ").join(map(str, listOfInput))
        domain_text = StringOfObjects
        return domain_text

if __name__ == '__main__':
    rospy.init_node('planning_domain_node', anonymous=False)
    pDC = PlanDomainClass(sys.argv[1])
    rospy.spin()
