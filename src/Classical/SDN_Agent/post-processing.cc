/*###################################################################### 
#
# File Name: post-processing.cc
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
#include <iostream>
#include <dlfcn.h>
#include "post-processing.h"

using namespace std;


string PostProcess(PostProMessage MsgPostPro)
{
	void *libqns = LoadPostProcessingLibrary();
	if (libqns == NULL) 
	{	
		printf("No PostProcessing Library(libqnspostpro.so)  - Failure(%s)\n", dlerror());
		printf("Default Post Processing\n");
	}
	string key = QnsPostProcess(libqns, MsgPostPro);
	return key;
}

string QnsPostProcess(void *postprodlhandle, PostProMessage MsgPostPro)
{
	string (*QnsPostProcess)(PostProMessage);
	string key;
	QnsPostProcess = (string (*)(PostProMessage)) dlsym(postprodlhandle, "_ZN14PostProcessing13doPostProcessB5cxx11E7Message");			
	if (QnsPostProcess == NULL) 
	{
		printf("Error: No Symbol (%s)\n", dlerror());
		key = DefaultPostProcess(MsgPostPro);
	}
	else
	{
		key = (*QnsPostProcess)(MsgPostPro);
		printf(" QnsPostPro           -  Found\n\n");
	}
	return key;	
}

string DefaultPostProcess(PostProMessage MsgPostPro)
{
	cout<<" Post Process          -      DEFAULT MODE "<<endl;
	return MsgPostPro.key;  //dummy key
}



unsigned char* DefaultSifting(unsigned char* bytestream)
{
	cout<<" Sifting          -      DEFAULT MODE "<<endl;
	return (unsigned char*)bytestream;
}

float DefaultErrorEstimation(unsigned char* bytestream)
{
	cout<<" Error Estimation -      DEFAULT MODE "<<endl;
	return 0.0;
}

unsigned char* DefaultErrorCorrection(unsigned char* bytestream)
{
	cout<<" Error Correction -      DEFAULT MODE "<<endl;
	return (unsigned char*)bytestream;
}	

unsigned char * DefaultPrivacyAmplification(unsigned char *bytestream)
{
	cout<<" Privacy Amplification - DEFAULT MODE "<<endl;
	return (unsigned char*)bytestream;
}



void * LoadPostProcessingLibrary()
{
	void *postprodlhandle;
	postprodlhandle = dlopen(POSTPROCESSING_LIBRARY, RTLD_LAZY ); 
	return (void *)postprodlhandle;
}

int ExitPostProcessingLibrary(void *postprodlhandle)
{

	dlclose(postprodlhandle);
	return 0;
	
}

unsigned char * CallSwifting(void *postprodlhandle, unsigned char* bytestream)
{
	unsigned char* (*funcptrSwifting)(unsigned char*);
	unsigned char* siftedbytestream;
	funcptrSwifting = (unsigned char* (*)(unsigned char*)) dlsym(postprodlhandle, "_ZN14PostProcessing6doSiftEPh");			
	if (funcptrSwifting == NULL) 
	{
		//printf("Error: No Symbol (%s)\n", dlerror());
		siftedbytestream = DefaultSifting(bytestream);
	}
	else
	{
		siftedbytestream = (*funcptrSwifting)(bytestream);
		//printf(" Sifting          -  Found\n\n");

	}
	return siftedbytestream;	
}


float CallErrorEstimation(void *postprodlhandle, unsigned char* bytestream)
{
	float (*funcptrErrorEstimation)(unsigned char*);
	float estimatederror;
	funcptrErrorEstimation = (float (*)(unsigned char*)) dlsym(postprodlhandle, "_ZN14PostProcessing17doErrorEstimationEPh");			
	if (funcptrErrorEstimation == NULL) 
	{
		//printf("Error: No Symbol (%s)\n", dlerror());
		estimatederror = DefaultErrorEstimation(bytestream);
	}
	else
	{
		estimatederror = (*funcptrErrorEstimation)(bytestream);
		//printf(" Error Estimation   -  Found\n\n");
	}
	return estimatederror;	
}


unsigned char * CallErrorCorrection(void *postprodlhandle, unsigned char* bytestream)
{
	unsigned char* (*funcptrErrorCorrection)(unsigned char*);
	unsigned char* errorcorrectedbytestream;
	funcptrErrorCorrection = (unsigned char* (*)(unsigned char*)) dlsym(postprodlhandle, "_ZN14PostProcessing17doErrorCorrectionEPh");			
	if (funcptrErrorCorrection == NULL) 
	{
		//printf("Error: No Symbol (%s)\n", dlerror());
		errorcorrectedbytestream = DefaultErrorCorrection(bytestream);
	}
	else
	{
		errorcorrectedbytestream = (*funcptrErrorCorrection)(bytestream);
		//printf(" Error Correction   -  Found\n\n");
	}
	return errorcorrectedbytestream;	
}

unsigned char * CallPrivacyAmplification(void *postprodlhandle, unsigned char* bytestream)
{
	unsigned char* (*funcptrPrivacyAmplification)(unsigned char*);
	unsigned char* privacyamplifiedbytestream;

	funcptrPrivacyAmplification = (unsigned char* (*)(unsigned char*)) dlsym(postprodlhandle, "_ZN14PostProcessing22doPrivacyAmplificationEPh");			
	if (funcptrPrivacyAmplification == NULL) 
	{
		//printf("Error: No Symbol (%s)\n", dlerror());
		privacyamplifiedbytestream = DefaultPrivacyAmplification(bytestream);
	}
	else
	{
		privacyamplifiedbytestream = (*funcptrPrivacyAmplification)(bytestream);
		//printf(" Privacy Amplification    -  Found\n\n");
	}
	return privacyamplifiedbytestream;	
}



bool getPostProcessingAlgorithms(int algorithmType)
{
	unsigned char* (*funcptrAlgorithms)(unsigned char*);
	float (*funcptrAlgorithmsErrorEstimation)(unsigned char*);

	void *libqns = LoadPostProcessingLibrary();
	if (libqns == NULL) 
	{
		
		printf("Post Processing Library - Not Available  ( %s )\n", dlerror());
		//printf("Default Post Processing\n");
		return false;
	}

	switch(algorithmType)
	{
		case ALGORITHM_QKD_PROTOCOL:
			ExitPostProcessingLibrary(libqns);
			return false;
			break;
		case ALGORITHM_SIFTING:
			funcptrAlgorithms = (unsigned char* (*)(unsigned char*)) dlsym(libqns, "_ZN14PostProcessing13doPostProcessB5cxx11E7Message");		
			break;
		case ALGORITHM_ERROR_ESTIMATION:
			funcptrAlgorithmsErrorEstimation = (float (*)(unsigned char*)) dlsym(libqns, "_ZN14PostProcessing13doPostProcessB5cxx11E7Message");
			if (funcptrAlgorithmsErrorEstimation != NULL) 
			{
				ExitPostProcessingLibrary(libqns);
				return true;
			}
			else
			{
				ExitPostProcessingLibrary(libqns);
				return false;
			}			
			break;
		case ALGORITHM_ERROR_CORRECTION:
			funcptrAlgorithms = (unsigned char* (*)(unsigned char*)) dlsym(libqns, "_ZN14PostProcessing13doPostProcessB5cxx11E7Message");			
			break;
		case ALGORITHM_PRIVACY_AMPLIFICATION:
			funcptrAlgorithms = (unsigned char* (*)(unsigned char*)) dlsym(libqns, "_ZN14PostProcessing13doPostProcessB5cxx11E7Message");			
			break;
		default:
			ExitPostProcessingLibrary(libqns);
			return false;
			break;
	}
	if (funcptrAlgorithms != NULL) 
	{
		ExitPostProcessingLibrary(libqns);
		return true;
	}
	else
	{
		ExitPostProcessingLibrary(libqns);
		return false;
	}
	ExitPostProcessingLibrary(libqns);	
	return false;
}