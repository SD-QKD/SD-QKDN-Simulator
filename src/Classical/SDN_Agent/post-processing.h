/*###################################################################### 
#
# File Name: post-processing.h
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 28-10-2022
# 
# Purpose : Simulation - Post processing
# 
# Description : Post prcoessing of NetSquid Quantum transmission
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : Integration module between NetSquid and NS3 simulation server
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
########################################################################*/
#ifndef POST_PROCESSSING_H
#define POST_PROCESSSING_H
#include <string.h>

#define ALGORITHM_QKD_PROTOCOL          1
#define ALGORITHM_SIFTING               2
#define ALGORITHM_ERROR_ESTIMATION      3
#define ALGORITHM_ERROR_CORRECTION      4
#define ALGORITHM_PRIVACY_AMPLIFICATION 5

#define POSTPROCESSING_LIBRARY	"libqnspostpro.so"
#define NODE_TYPE_ALICE		1
#define NODE_TYPE_BOB		2
#define PROTOCOL_BB84		"BB84"

using namespace std;

class PostProMessage
{
	public:
		int id;
		int node_type;
		string protocol;
		string bits;
		string basis;
		string source;
		string source_ip;
		int source_port;
		string destination;
		string destination_ip;
		int destination_port;
		string matchlist;
		float error_rate;
		string key;
};


string PostProcess(PostProMessage MsgPostPro);
string QnsPostProcess(void *postprodlhandle, PostProMessage MsgPostPro);
string DefaultPostProcess(PostProMessage MsgPostPro);

unsigned char* DefaultSifting(unsigned char* bytestream);
float DefaultErrorEstimation(unsigned char* bytestream);
unsigned char* DefaultErrorCorrection(unsigned char* bytestream);
unsigned char * DefaultPrivacyAmplification(unsigned char *bytestream);

void * LoadPostProcessingLibrary();
int ExitPostProcessingLibrary(void *postprodlhandle);

unsigned char * CallSwifting(void *postprodlhandle, unsigned char* bytestream);
float CallErrorEstimation(void *postprodlhandle, unsigned char* bytestream);
unsigned char * CallErrorCorrection(void *postprodlhandle, unsigned char* bytestream);
unsigned char * CallPrivacyAmplification(void *postprodlhandle, unsigned char* bytestream);

bool getPostProcessingAlgorithms(int algorithmType);

#endif
