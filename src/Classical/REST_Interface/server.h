/*###################################################################### 
# 
# File Name: server.h
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 10-2022
# 
# Purpose : Simulation
# 
# Description : 
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : Simulation server
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 
#ifndef RESTSERVER_H
#define RESTSERVER_H
#include <ulfius.h>
#include <jansson.h>
#include <iostream>
#include <string.h>

using namespace std;

#define URL_SIMULATOR_STATUS		"/sim/status"
#define URL_PROBE_TOPOLOGY		"/sim/probe/topology"
#define URL_PROBE_STACK_CAPABILITY	"/sim/probe/stackcapability"
#define URL_SIMULATE_TOPOLOGY		"/sim/simulatetopology"
#define URL_STOP_TOPOLOGY		"/sim/stoptopology"
#define URL_STATUS_TOPOLOGY		"/sim/statustopology"
#define URL_NODE_LINK_DETAILS		"/sim/nodelinkdetails"

void *RESTServerThread(void *vargp);
int RESTServer(void);

int callback_ServerTest (const struct _u_request * request, struct _u_response * response, void * user_data) ;
int callback_SimulatorStatus (const struct _u_request * request, struct _u_response * response, void * user_data);
int callback_SimulatorProbeTopology (const struct _u_request * request, struct _u_response * response, void * user_data) ;
int callback_SimulatorProbeStackCapability (const struct _u_request * request, struct _u_response * response, void * user_data) ;
int callback_SimulateTopology (const struct _u_request * request, struct _u_response * response, void * user_data) ;
int callback_StopTopology (const struct _u_request * request, struct _u_response * response, void * user_data);
int callback_StatusTopology (const struct _u_request * request, struct _u_response * response, void * user_data);
int callback_nodelinkdetails(const struct _u_request *request, struct _u_response *response, void *user_data); 

#endif
