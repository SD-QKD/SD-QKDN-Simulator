/*###################################################################### 
# 
# File Name: QKDNode.h
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 24-01-2023
# 
# Purpose : QKD Node Simulation
# 
# Description : QKD Node Simulation header 
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : QKD Node module
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 
#ifndef QKDNODE_H
#define QKDNODE_H
#include "ns3/socket.h"
#include "ns3/application.h"
#include <string.h>
#include <jansson.h>

using namespace ns3;
using namespace std;


#define QKD_NODE_FILE_BASE      "/conf/nodes/"
#define QKD_STATUS_FILE		"STATUS.txt"
#define QKD_COMMAND_FILE	"COMMAND.txt"
#define LOG_FILE_NAME		"LOG.txt"

#define QKDNODE_INTERVAL_DEFAULT	60
#define MESSAGE_TYPE_STATUS		  "status"
#define MESSAGE_TYPE_COMMAND		"command"

#define PARAM_LINK_ID		          1
#define PARAM_LINK_NAME		        2
#define PARAM_LINK_SOURCE	        3
#define PARAM_LINK_DESTINATION	  4
#define PARAM_LINK_NEIGHBOUR_NODE 5
#define PARAM_LINK_CHANNEL_TYPE   6
#define PARAM_LINK_CLASSICAL_ID		7
#define PARAM_LINK_CLASSICAL_NAME	8
#define PARAM_LINK_CLASSICAL_STATUS	9

namespace ns3
{
  class QKDNode : public Application 
  {
    public:
      string nodeid;
      string nodename;
      int messageId;
      int log_level;
      QKDNode ();
      virtual ~QKDNode ();
      
      void PeriodicStatusUpdate(void);  
      int UpdateNodeStatus (string messagetype, string nodeid, string status);
      bool SetNodeId(string nodeid);
      string GetNodeId();
      
      bool SetNodeName(string nodeid);
      string GetNodeName();

      int postDeviceInit(const char *nodeid, const char *ip);
      const char *getNodeIPAddress();
      int GetLogLevel();
      bool SetLogLevel(int level);
      
    private:     
      
      virtual void StartApplication ();
      
  };
}

#endif
