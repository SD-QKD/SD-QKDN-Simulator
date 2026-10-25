/*###################################################################### 
# 
# File Name: qcc-simulate.h
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
# Description : SDN Agent Simulation for NS3 and REST service
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : Header file for SDN agent module
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 

#ifndef QCCSIMULATE_H
#define QCCSIMULATE_H
#define FILENAME_PREFIX_PCAP	"/conf/nodes/pcap/agent-" //Default location of pcap file
void *QCCSimulationServerThread(void *vargp);
bool stopSimulation();
bool statusSimulation();
#endif
