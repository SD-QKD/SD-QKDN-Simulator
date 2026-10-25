/*###################################################################### 
# 
# File Name: KeyStore.h
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 28-10-2022
# 
# Purpose : QKD Keystore implementation
# 
# Description : QKD Keystore implementation header
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : QKD Key storage and functions
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/
#ifndef KEYSTORE_H
#define KEYSTORE_H
#include <string>
#include <cstring>

#define MAX_KEY_IDS				1024
#define MAX_KEY_STORAGE			20*1024 	//100KB	//5*1024*1024 //52,42,880 = 5MB
#define MIN_KEY_STORAGE			10*1024		//1*1024*1024 //1MB
#define THESHOLD_KEY_STORAGE	20*1024		//2*1024*1024 //2MB
#define MAX_SAE_IDS				5 		//Limited for initial development

#define KEY_STORE_NOT_AVAILABLE	-1
#define KEY_STORE_READY		1
#define KEY_STORE_EMPTY		2
#define KEY_STORE_FULL		3
#define KEY_STORE_THESHOLD	4
#define KEY_STORE_FAILURE	5
#define KEY_STORE_IDLE		6
#define KEY_STORE_UNKNOWN	7

#define KEY_TYPE_QUANTUM	"Quantum"
#define KEY_TYPE_RELAY		"Relay"
#define KEY_TYPE_PQC		"PQC"

using namespace std;
namespace ns3
{
class KeyStore   
{
	string nodeid_source;
	string nodeid_target;
    	string keyid[MAX_KEY_IDS];
    	string key[MAX_KEY_IDS];
	string keystore;
	int keysize[MAX_KEY_IDS];
	bool iskey[MAX_KEY_IDS];
	int keycount;
	int status;
	int sae_id;
	bool active;
    public:
    	KeyStore();
    	KeyStore(string nid_source, string nid_target);
    	KeyStore(int sae_id, string nid_source, string nid_target);
    	~KeyStore();
	int Status();
	string GetKey(int keysize);
	int KeyReserve(int keysize, string kid);
	string GetKey(string keyid);
	int StoreKey(string keystream);
	int GetKeyCount();
	int UpdateKeyCount();
	int GetKeyStoreSize();
	int Notify(string keyid, int size);
	int GetMaxKeyStoreSize();
	int GetMaxKeyCount();
	string GenerateKeyId();
	string GetSourceID();
	string GetTargetID();
	int SetSourceID(string nid_source);
	int SetTargetID(string nid_target);
	void StreamToHexString(const string str, string& hexstr, bool capital);
	void HexStringToStream(const string hexstr, string& str);
	char* Base64Encoder(char input_str[], int len_str);
	char* Base64Decoder(char encoded[], int len_str);
	
	int GetSAEId();
	bool SetSAEId(int saeid);
	bool SetStatus(bool status);
	bool GetStatus();
	
};
}
#endif
