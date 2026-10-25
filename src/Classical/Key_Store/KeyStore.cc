/*###################################################################### 
# 
# File Name: KeyStore.cpp
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
# Description : QKD Keystore implementation
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
#include <iostream>
#include <uuid/uuid.h>
#include "KeyStore.h"

using namespace std;
//using namespace ns3;

namespace ns3
{

KeyStore::KeyStore()
{
	keystore="";
	keycount=0;
	status = KEY_STORE_EMPTY;
	nodeid_source="";
	nodeid_target="";
	sae_id=0;
	active = false;
}

KeyStore::KeyStore(string nid_source, string nid_target)
{
	keystore="";
	keycount=0;
	status = KEY_STORE_EMPTY;
	nodeid_source=nid_source;
	nodeid_target=nid_target;
	sae_id=0;
	active = false;
}

KeyStore::KeyStore(int sae_id, string nid_source, string nid_target)
{
	keystore="";
	keycount=0;
	status = KEY_STORE_EMPTY;
	nodeid_source=nid_source;
	nodeid_target=nid_target;
	this->sae_id = sae_id;
	active = false;
}


KeyStore::~KeyStore()
{
	keystore="";
	keycount=0;
	status = KEY_STORE_EMPTY;
	active = false;
}

int KeyStore::StoreKey(string keystream)
{
	if(GetKeyStoreSize() < MAX_KEY_STORAGE)
	{
		this->keystore.append(keystream);
	}
	else
	{
		return KEY_STORE_FULL;
	}
	//cout<<"Key store  size : "<<keystore.size()<<" data: "<<keystore<<endl;	   	
    return KEY_STORE_READY;
}


int KeyStore::GetKeyStoreSize()
{
	return(this->keystore.size());
}


int KeyStore::Status()
{
	int keystoresize = GetKeyStoreSize();
	if(keystoresize >= MAX_KEY_STORAGE)
	{	
		status = KEY_STORE_FULL;
		return KEY_STORE_FULL;
	}
	else if(keystoresize <= 1)
	{
		status = KEY_STORE_EMPTY;
		return KEY_STORE_EMPTY;
	}
	else if (keystoresize < THESHOLD_KEY_STORAGE)
	{
		status = KEY_STORE_THESHOLD;
		return KEY_STORE_THESHOLD;
	}
	else if (keystoresize < MIN_KEY_STORAGE)
	{
		status = KEY_STORE_READY;
		return KEY_STORE_READY;
	}
	else
	{
		status = KEY_STORE_IDLE;
		return KEY_STORE_IDLE;
	}
	status = KEY_STORE_UNKNOWN; 	
	return KEY_STORE_UNKNOWN;
}

string KeyStore::GenerateKeyId()
{
	uuid_t uuid;
	char uuid_str[37];
	uuid_generate_random(uuid);
        uuid_unparse_lower(uuid, uuid_str);
        return uuid_str;
}

	
string KeyStore::GetKey(int keysize)
{
    string kvalue="";
    string kid="";
    
    int keysizebytes=0;
    
    if((keysize < 64) | (keysize > 1024))
    	return "";
    if((keysize%8) != 0 )
    	return "";
    else
    	keysizebytes = keysize/8 ;
    	
    if(GetKeyStoreSize() < keysizebytes )
    	return "";
    	
    string::iterator it;

    for (it = this->keystore.begin(); it <= this->keystore.begin()+(keysizebytes-1); it++)
    {
        kvalue+= *it;
     }
    this->keystore.erase(this->keystore.begin(), this->keystore.begin()+keysizebytes);

    
    kid = GenerateKeyId();
    
    int kcount = GetKeyCount();
    if(kcount < MAX_KEY_IDS)
    {
    	keyid[kcount] = kid;
    	key[kcount] = kvalue;
    	UpdateKeyCount();
    }
    else
    	return "";
    
    return kid; 
}

int KeyStore::KeyReserve(int keysize, string kid)
{
    string kvalue="";
  
    int keysizebytes=0;
    
    if((keysize < 64) | (keysize > 1024))
    	return -1;
    if((keysize%8) != 0 )
    	return -1;
    else
    	keysizebytes = keysize/8 ;
    	
    if(GetKeyStoreSize() < keysizebytes )
    	return -1;
    	
    string::iterator it;

    for (it = this->keystore.begin(); it <= this->keystore.begin()+(keysizebytes-1); it++)
    {
        kvalue+= *it;
     }
    this->keystore.erase(this->keystore.begin(), this->keystore.begin()+keysizebytes);

    if( kid=="")
    	return -1;

    int kcount = GetKeyCount();
    if(kcount < MAX_KEY_IDS)
    {
    	keyid[kcount] = kid;
    	key[kcount] = kvalue;
    	UpdateKeyCount();
    }
    else
    	return -1;
    
    return 0; 
}


string KeyStore::GetKey(string keyid)
{
 
    if(GetKeyCount()==0)
    	return "";
    
    for(int i=0; i < GetKeyCount(); i++)
    {
    	if(keyid == this->keyid[i])
    		return (this->key[i]);
    }
    return ""; 
}

int KeyStore::GetKeyCount()
{
	return (this->keycount);
}

int KeyStore::UpdateKeyCount()
{	
	this->keycount++;
	return (this->keycount);
}

int KeyStore::Notify(string keyid, int size)
{
	return 0;
}

string KeyStore::GetSourceID()
{
	return (this->nodeid_source);
}

string KeyStore::GetTargetID()
{
	return (this->nodeid_target);
}

int KeyStore::SetSourceID(string nid_source)
{
	this->nodeid_source = nid_source;
	return true;

}
int KeyStore::GetMaxKeyStoreSize()
{
	return MAX_KEY_STORAGE;
}

int KeyStore::GetMaxKeyCount()
{
	return MAX_KEY_IDS;
}
int KeyStore::SetTargetID(string nid_target)
{
	this->nodeid_target=nid_target;
	return true;
}

int KeyStore::GetSAEId()
{
	return (this->sae_id);

}

bool KeyStore::SetSAEId(int saeid)
{
	this->sae_id = saeid;
	return true;
}

bool KeyStore::SetStatus(bool status)
{
	this->active = status;
	return (this->active);
}

bool KeyStore::GetStatus()
{
	return (this->active);
}

// Convert string of chars to its representative string of hex numbers
void KeyStore::StreamToHexString(const std::string str, std::string& hexstr, bool capital = true)
{
    hexstr.resize(str.size() * 2);
    const size_t a = capital ? 'A' - 1 : 'a' - 1;

    for (size_t i = 0, c = str[0] & 0xFF; i < hexstr.size(); c = str[i / 2] & 0xFF)
    {
        hexstr[i++] = c > 0x9F ? (c / 16 - 9) | a : c / 16 | '0';
        hexstr[i++] = (c & 0xF) > 9 ? (c % 16 - 9) | a : c % 16 | '0';
    }
}

// Convert string of hex numbers to its equivalent char-stream
void KeyStore::HexStringToStream(const std::string hexstr, std::string& str)
{
    str.resize((hexstr.size() + 1) / 2);

    for (size_t i = 0, j = 0; i < str.size(); i++, j++)
    {
        str[i] = (hexstr[j] & '@' ? hexstr[j] + 9 : hexstr[j]) << 4, j++;
        str[i] |= (hexstr[j] & '@' ? hexstr[j] + 9 : hexstr[j]) & 0xF;
    }
}

char* KeyStore::Base64Encoder(char input_str[], int len_str)
{
	// Character set of base64 encoding scheme
	char char_set[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
	
	// Resultant string
	char *res_str = (char *) malloc((2*1024) * sizeof(char));
	
	int index, no_of_bits = 0, padding = 0, val = 0, count = 0, temp;
	int i, j, k = 0;
	
	for (i = 0; i < len_str; i += 3)
	{
		val = 0, count = 0, no_of_bits = 0;

		for (j = i; j < len_str && j <= i + 2; j++)
		{
			val = val << 8;
			val = val | input_str[j];
			count++;
		}
		no_of_bits = count * 8;
		padding = no_of_bits % 3;
		while (no_of_bits != 0)
		{
			if (no_of_bits >= 6)
			{
				temp = no_of_bits - 6;
				index = (val >> temp) & 63;
				no_of_bits -= 6;		
			}
			else
			{
				temp = 6 - no_of_bits;
				index = (val << temp) & 63;
				no_of_bits = 0;
			}
			res_str[k++] = char_set[index];
		}
	}

	for (i = 1; i <= padding; i++)
	{
		res_str[k++] = '=';
	}

	res_str[k] = '\0';

	return res_str;
}


char* KeyStore::Base64Decoder(char encoded[], int len_str)
{
    char* decoded_string;
 
    decoded_string = (char*)malloc(sizeof(char) * (2*1024));
 
    int i, j, k = 0;
 
    int num = 0;
    int count_bits = 0;

    for (i = 0; i < len_str; i += 4) {
        num = 0, count_bits = 0;
        for (j = 0; j < 4; j++) {
            if (encoded[i + j] != '=') {
                num = num << 6;
                count_bits += 6;
            }
 
            if (encoded[i + j] >= 'A' && encoded[i + j] <= 'Z')
                num = num | (encoded[i + j] - 'A');

            else if (encoded[i + j] >= 'a' && encoded[i + j] <= 'z')
                num = num | (encoded[i + j] - 'a' + 26);
 
            else if (encoded[i + j] >= '0' && encoded[i + j] <= '9')
                num = num | (encoded[i + j] - '0' + 52);
 
            else if (encoded[i + j] == '+')
                num = num | 62;
 
            else if (encoded[i + j] == '/')
                num = num | 63;
            else {
                num = num >> 2;
                count_bits -= 2;
            }
        }
 
        while (count_bits != 0) {
            count_bits -= 8;
            decoded_string[k++] = (num >> count_bits) & 255;
        }
    }
 
    decoded_string[k] = '\0';
 
    return decoded_string;
}
}		
