/*###################################################################### 
# 
# File Name: QKDNode.cc
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 25-11-2022
# 
# Purpose : Simulation
# 
# Description : QKD Node Simulation for NS3 and REST service to TestApp
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
#include "ns3/log.h"
#include "ns3/udp-socket.h"
#include "ns3/simulator.h"
#include "ns3/csma-net-device.h"
#include "ns3/ethernet-header.h"
#include "ns3/arp-header.h"
#include "ns3/ipv4-header.h"
#include "ns3/udp-header.h"
#include "ns3/tcp-header.h"
#include "ns3/uinteger.h"
#include "ns3/boolean.h"
#include "ns3/ipv4-raw-socket-impl.h"
#include "ns3/socket-factory.h"
#include "ns3/ipv4-raw-socket-impl.h"
#include "ns3/ipv4-l3-protocol.h"
#include "ns3/icmpv4.h"
#include <ns3/callback.h>
#include <ns3/config.h>
#include <ns3/pointer.h>
#include <ns3/uinteger.h>
#include <ns3/packet.h>
#include <ns3/socket.h>
#include <ns3/tcp-socket.h>
#include <ns3/tcp-socket-factory.h>
#include <ns3/inet-socket-address.h>
#include <ns3/unused.h>
#include <string.h>
#include <cstring>
#include <unistd.h>
#include <bits/stdc++.h>
#include <iostream>
#include "QKDNode.h"
#include "../Simulator_Service/utility.h"
#include "../SDN_Agent/SDNAgent.h"

using namespace std;
using namespace ns3;

namespace ns3
{
  
QKDNode::QKDNode()
{
	this->messageId=0;
}
QKDNode::~QKDNode()
{
	
}

int QKDNode::postDeviceInit(const char *nodeid, const char *ip)
{
	json_t *json_body = json_object();
	json_t *json_link[3];
	json_t *json_arrays = json_array();
	json_t *json_clink[1];
	json_t *json_carrays = json_array();

	json_object_set_new(json_body, "MESSAGE_ID", json_string(to_string(1).c_str()));
	json_object_set_new(json_body, "NODE_ID", json_string(nodeid));
	json_object_set_new(json_body, "NODE_NAME", json_string(GetNodeName().c_str()));
	json_object_set_new(json_body, "STATUS_TYPE", json_string("DEVICE_INIT"));
	json_object_set_new(json_body, "NODE_IP", json_string(ip)); 
	json_object_set_new(json_body, "TIMESTAMP", json_string(getCurrentDateTime())); 
 	json_object_set_new(json_body, "KM_IP", json_string(ip)); 
	json_object_set_new(json_body, "KM_PORT", json_integer(SDN_AGENT_PORT)); 
	json_object_set_new(json_body, "DOMAIN", json_string("maqan.qkd.net"));
	int qc_channels = getQuantumChannels(nodeid);
	if(qc_channels > 0)
	{
		for (int i = 0; i < qc_channels; i++)
		{
			json_link[i] = json_object();
			json_object_set_new(json_link[i], "QC_ID", json_string(getChannelParams(nodeid,(i+1), PARAM_LINK_ID)));
			json_object_set_new(json_link[i], "QC_STATUS", json_string("UP"));
			json_object_set_new(json_link[i], "QC_TYPE", json_string(getChannelParams(nodeid, (i+1), PARAM_LINK_CHANNEL_TYPE))); 
			json_object_set_new(json_link[i], "NEIGHBOUR_NODE_ID", json_string(getChannelParams(nodeid,(i+1),PARAM_LINK_NEIGHBOUR_NODE)));
			json_object_set_new(json_link[i], "NEIGHBOUR_NODE_NAME", json_string(getNodeName(getChannelParams(nodeid,(i+1),PARAM_LINK_NEIGHBOUR_NODE))));
			json_array_append_new(json_arrays, json_link[i]);	
		} 
		json_object_set_new(json_body, "QUANTUM_CHANNEL", json_arrays);
}
//Not passing classical channel information as not receiving from application	

	int cc_channels = 1;	
	for (int i =0; i < cc_channels; i++)
	{
		json_clink[i] = json_object();
		json_object_set_new(json_clink[i], "CC_ID", json_string(getCCChannelParams(nodeid, PARAM_LINK_CLASSICAL_ID)));
		json_object_set_new(json_clink[i], "CC_NAME", json_string(getCCChannelParams(nodeid, PARAM_LINK_CLASSICAL_NAME)));
		json_object_set_new(json_clink[i], "CC_STATUS", json_string(getCCChannelParams(nodeid, PARAM_LINK_CLASSICAL_STATUS)));        
            	json_object_set_new(json_clink[i], "XD_LINK", json_string("false"));
            	json_object_set_new(json_clink[i], "XD_NEIGHBOUR_NODE_ID", json_string("NA"));
		json_array_append_new(json_carrays, json_clink[i]);
	}
	json_object_set_new(json_body, "CLASSICAL_CHANNEL", json_carrays); 


	string qne_home = getQNEHome();
	ofstream statusfile;
	string statusfilename=qne_home+QKD_NODE_FILE_BASE+(this->nodeid)+"/"+QKD_STATUS_FILE;
	statusfile.open (statusfilename);
	statusfile << json_dumps(json_body,0)<<"\n";
	statusfile.close();

	ofstream commadfile;
	string commadfilename=QKD_NODE_FILE_BASE+(this->nodeid)+"/"+QKD_COMMAND_FILE;
	commadfile.open (commadfilename);
	commadfile.close();
	return 0;
}


const char *QKDNode::getNodeIPAddress()
{
	int UIntIP = GetNode()->GetObject<Ipv4>()->GetAddress(1,0).GetLocal().Get();
	string strip = to_string(UIntIP >> 24) + "." + to_string((UIntIP >> 16) & 0xff) + "." + to_string((UIntIP >> 8) & 0xff) + "." + to_string(UIntIP & 0xff) ;
	return (strip.c_str());
}


void QKDNode::StartApplication()
{
	const char *nodeip = getNodeIPAddress();   
    cout<<"QKD Node ["<<GetNodeId()<<" | "<<nodeip<<"] - STARTED "<<endl;
	postDeviceInit(GetNodeId().c_str(), nodeip);
	++messageId;
	//cout<<"Device_Init\t: "<<nodeid<<" | "<<messageId<<endl;
    PeriodicStatusUpdate(); 	
}

  
void QKDNode::PeriodicStatusUpdate()
{
	return;	  
}



int QKDNode::UpdateNodeStatus (string messagetype, string nodeid, string status)
{
	return 0;
}


bool QKDNode::SetNodeId(string nodeid)
{

	this->nodeid = nodeid;
	return true;
}

string QKDNode::GetNodeId()
{
	return(this->nodeid);
} 

bool QKDNode::SetNodeName(string nodename)
{
	this->nodename = nodename;
	return true;
}

string QKDNode::GetNodeName()
{
	return (this->nodename);
}

int QKDNode::GetLogLevel()
{
	return(this->log_level);

}

bool QKDNode::SetLogLevel(int level)
{
	this->log_level = level;
	return true;
}


}
