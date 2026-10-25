/*###################################################################### 
# 
# File Name: qne.cc
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 28-10-2022
# 
# Purpose : Quantum Network Emulation
# 
# Description : Emulation core for NS3 and REST service to NetSquid
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : Integrated NS-3 based emulator module for emulation server
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 
#include <iostream>
#include <stdio.h>
#include <string.h>
#include <ulfius.h>
#include <jansson.h>
#include "qne.h"
#include "REST_Interface/server.h"
#include "Simulator_Service/utility.h"
#include "SDN_Agent/SDNAgent.h"
using namespace std;

#ifndef VERSION
#define VERSION "0.0.0"        // string fallback
#endif

#ifndef GIT_COMMIT
#define GIT_COMMIT "unknown"
#endif

#ifndef GIT_REVISION
#define GIT_REVISION 0
#endif

/*
Starting of NS-3 emulation, including REST server, SDN Agent and QKD Nodes
*/

int main(int argc, char *argv[])
{
    cout << endl;
    cout << "+------------------------------------------------------------+" << endl;
    cout << "|         Quantum Network Emulator (QNE)                     |" << endl;
    cout << "+------------------------------------------------------------+" << endl;
    cout << "| Version  : " << VERSION                            << endl;
    cout << "| Revision : " << GIT_REVISION                      << endl;
    cout << "| Commit   : " << GIT_COMMIT                        << endl;
    cout << "| Built    : " << __DATE__ << ",  " << __TIME__     << endl;
    cout << "+------------------------------------------------------------+" << endl;

	if(setQNEHome() == false)
	{
		cout<<"QNE_HOME is not set, Aborting..."<<endl;
		return 0;
	}
	cout<<"QNE_HOME : "<<getQNEHome()<<endl;
	if(argc == 1) { setLogLevel(LOG_LEVEL_DEFAULT); } // default mode is selected if no option provided
	if(argc == 2)
	{
		if((strcmp(argv[1],"-h") == 0) || (strcmp(argv[1],"--help") == 0)) //for different log level support
		{
			cout<<"Log Levels"<<endl;
			cout<<" -q/--quiet\t\t- Quiet(default) "<<endl;
			cout<<" -p/--packets\t\t- Packets logs"<<endl;
			cout<<" -r/--periodical\t- Periodical logs "<<endl;
			cout<<" -d/--debug\t\t- Debug(all logs) "<<endl;
			cout<<" -f/--file\t\t- File based logs "<<endl;
			return 0;
		}
		// Setting different log levels
		if((strcmp(argv[1],"-q") == 0) || (strcmp(argv[1],"--quiet") == 0)) 	{ 	setLogLevel(LOG_LEVEL_DEFAULT); }
		if((strcmp(argv[1],"-p") == 0) || (strcmp(argv[1],"--packets") == 0)) 	{ 	setLogLevel(LOG_LEVEL_PACKETS); }
		if((strcmp(argv[1],"-r") == 0) || (strcmp(argv[1],"--periodical") == 0)){	setLogLevel(LOG_LEVEL_PERIODICAL);	}
		if((strcmp(argv[1],"-d") == 0) || (strcmp(argv[1],"--debug") == 0))		{	setLogLevel(LOG_LEVEL_DEBUG);	}
		if((strcmp(argv[1],"-f") == 0) || (strcmp(argv[1],"--file") == 0)) 		{	setLogLevel(LOG_TO_FILE);	}
	}
	

	pthread_t thread_id_rest; //for REST server thread
	pthread_create(&thread_id_rest, NULL, RESTServerThread, NULL);

	pthread_join(thread_id_rest, NULL); //waiting to REST thread
	return 0;
}

