/*###################################################################### 
# 
# File Name: rest-api.cc
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 10-2022
# 
# Purpose : For REST APIs
# 
# Description : 
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : REST API
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 
#ifndef RESTAPI_H
#define RESTAPI_H
#include <jansson.h>

int RestSend(const char* to, const char* server_url, const char* append_url, json_t * json_body);
int RestSend(const char* to, const char* server_url, const char* append_url, json_t * json_body, const char* command);
int RestSend(const char* to, const char* server_url, const char* append_url, const char* command);
int RestSend(const char* to, const char* server_url, const char* data); 
int RestSend(const char* to, const char* ip, int port, const char* urlappend, char* data);

#endif
