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
#include <jansson.h>
#include <string>
#include <string.h>
#include <ulfius.h>
#include "u_example.h"
#include "rest-api.h"
using namespace std;

int RestSend(const char* to, const char* server_url, const char* append_url, json_t * json_body) 
{
	struct _u_response response;
	int res;
	struct _u_request req_list;
	ulfius_init_request(&req_list);

	ulfius_set_request_properties(&req_list, U_OPT_HTTP_VERB, "POST", U_OPT_HTTP_URL, server_url, U_OPT_HTTP_URL_APPEND, append_url, U_OPT_TIMEOUT, 20, U_OPT_JSON_BODY, json_body, U_OPT_NONE); 


	ulfius_init_response(&response);
	res = ulfius_send_http_request(&req_list, &response);
	if (res == U_OK) 
	{
		printf("\n>>>> %s Send [ Success (%s/%s) ]\n",to, server_url, append_url);
		return 0;
	} 
	else 
	{
		printf("\n>>>> %s Send [ Failure (%d, %s/%s) ]\n", to, res, server_url, append_url);
		return -1;
	}
	ulfius_clean_response(&response);
	json_decref(json_body);
	ulfius_clean_request(&req_list);

	return -1;
}

int RestSend(const char* to, const char* server_url, const char* append_url, json_t * json_body, const char* command) 
{
	struct _u_response response;
	int res;
	struct _u_request req_list;
	ulfius_init_request(&req_list);
	
	if(strcmp(command,"")!=0)
		json_object_set_new(json_body, "command", json_string(command));

	ulfius_set_request_properties(&req_list, U_OPT_HTTP_VERB, "POST", U_OPT_HTTP_URL, server_url, U_OPT_HTTP_URL_APPEND, append_url, U_OPT_TIMEOUT, 20, U_OPT_JSON_BODY, json_body, U_OPT_NONE); 


	ulfius_init_response(&response);
	res = ulfius_send_http_request(&req_list, &response);
	if (res == U_OK) 
	{
		printf("\n>>>> %s Send [ Success (%s/%s) ]\n",to, server_url, append_url);
		return 0;
	} 
	else 
	{
		printf("\n>>>> %s Send [ Failure (%d, %s/%s) ]\n", to, res, server_url, append_url);
		return -1;
	}
	ulfius_clean_response(&response);
	json_decref(json_body);
	ulfius_clean_request(&req_list);

	return -1;
}



int RestSend(const char* to, const char* server_url, const char* append_url, const char* command) 
{

	json_t * json_body = json_object();
	struct _u_response response;
	int res;
	
	json_object_set_new(json_body, "command", json_string(command));
	
	struct _u_request req_list;
	ulfius_init_request(&req_list);

	ulfius_set_request_properties(&req_list, U_OPT_HTTP_VERB, "POST", U_OPT_HTTP_URL, server_url, U_OPT_HTTP_URL_APPEND, append_url,
		                U_OPT_TIMEOUT, 20, U_OPT_JSON_BODY, json_body, U_OPT_NONE); 


	ulfius_init_response(&response);
	res = ulfius_send_http_request(&req_list, &response);
	if (res == U_OK) 
	{
		printf("\n>>>> %s Send [ Success (%s) ]\n",to, server_url);
		return 0;
	} 
	else 
	{
		printf("\n>>>> %s Send [ Failure (%d, %s) ]\n", to, res, server_url);
		return -1;
	}
	ulfius_clean_response(&response);
	json_decref(json_body);
	ulfius_clean_request(&req_list);

	return 0;
}



int RestSend(const char* to, const char* server_url, const char* data) 
{
	struct _u_response response;
	int res;
	struct _u_request req_list;
	ulfius_init_request(&req_list);
	
	ulfius_set_request_properties(&req_list, U_OPT_HTTP_VERB, "GET", U_OPT_HTTP_URL, server_url, U_OPT_HTTP_URL_APPEND, "/qkd-controller/DataReceiver", U_OPT_TIMEOUT, 20, U_OPT_URL_PARAMETER, "sdn_data", data, U_OPT_NONE); 


	ulfius_init_response(&response);
	res = ulfius_send_http_request(&req_list, &response);
	if (res == U_OK) 
	{
		printf("\n>>>> %s Send GET [ Success (%s) ]\n",to, server_url);
		return 0;
	} 
	else 
	{
		printf("\n>>>> %s Send GET [ Failure (%d, %s) ]\n", to, res, server_url);
		return -1;
	}
	ulfius_clean_response(&response);
	ulfius_clean_request(&req_list);
	return -1;
}


int RestSend(const char* to, const char* ip, int port, const char* urlappend, char* data) 
{
	struct _u_response response;
	int res;
	struct _u_request req_list;
	ulfius_init_request(&req_list);

	char *server_url = (char*)malloc(128);
	strcpy(server_url,"http://");
	strcat(server_url,ip);
	strcat(server_url,":");
	string s = to_string(port);
	char *p = const_cast<char*>(s.c_str());
	strcat(server_url,p);

	ulfius_set_request_properties(&req_list, U_OPT_HTTP_VERB, "POST", U_OPT_HTTP_URL, server_url, U_OPT_HTTP_URL_APPEND, urlappend, U_OPT_TIMEOUT, 20,  U_OPT_STRING_BODY, data, U_OPT_NONE); 

	ulfius_init_response(&response);
	res = ulfius_send_http_request(&req_list, &response);
	if (res == U_OK) 
	{
		return 0;
	} 
	else 
	{
		printf("\n>>>> %s Send GET [ Failure (%d, %s) ]\n", to, res, server_url);
		return -1;
	}
	ulfius_clean_response(&response);
	ulfius_clean_request(&req_list);
	return -1;
}

