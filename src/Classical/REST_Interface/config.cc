#include<iostream>
#include<fstream>
#include <sstream>
#include <cctype>
#include <boost/algorithm/string.hpp>
#include <string>
#include "config.h"

using namespace std;

Config::Config()
{
	this->guiip="127.0.0.1";
	this->guiport="5070";
	this->simulatorip="127.0.0.1";
	this->simulatorport="5071";
	this->quantumchannelip="127.0.0.1";
	this->quantumchannelport="5072";
	this->sdncontrollerip="127.0.0.1";
	this->sdncontrollerport="5073";

	setQNEHome();
	string qne_home = getQNEHome();
	LoadConfiguration(qne_home+SERVER_CONFIG_FILE);
}

string Config::GetServerIP(string server)
{
	if(server==GUI_SERVER)
	{
		return this->guiip;
	}
	if(server==QCC_SERVER)
	{
		return this->simulatorip;
	}
	if(server==SDN_SERVER)
	{
		return this->sdncontrollerip;
	}
	if(server==QQC_SERVER)
	{
		return this->quantumchannelip;
	}
	return "";
}


string Config::GetServerPort(string server)
{
	if(server==GUI_SERVER)
	{
		return this->guiport;
	}
	if(server==QCC_SERVER)
	{
		return this->simulatorport;
	}
	if(server==SDN_SERVER)
	{
		return this->sdncontrollerport;
	}
	if(server==QQC_SERVER)
	{
		return this->quantumchannelport;
	}
	return "";

}

int Config::GetServerPortNumber(string server)
{
	if(server==GUI_SERVER)
	{
		return stoi(this->guiport);
	}
	if(server==QCC_SERVER)
	{
		return stoi(this->simulatorport);
	}
	if(server==SDN_SERVER)
	{
		return stoi(this->sdncontrollerport);
	}
	if(server==QQC_SERVER)
	{
		return stoi(this->quantumchannelport);
	}
	return 0;
}
	

bool Config::SetServerAddress(string server, string ip, string port)
{
	if(server==GUI_SERVER)
	{
		this->guiip = ip;
		this->guiport = port;
	}

	if(server==QCC_SERVER)
	{
		this->simulatorip = ip;
		this->simulatorport = port;
	}
	
	
	if(server==SDN_SERVER)
	{
		this->sdncontrollerip = ip;
		this->sdncontrollerport = port;
	}
	
	
	if(server==QQC_SERVER)
	{
		this->quantumchannelip = ip;
		this->quantumchannelport = port;
	}
	
	return true;
}

string Config::GetServerURL(string server)
{
	string url="http://";
	if(server==GUI_SERVER)
	{
		url+=this->guiip;
		url+=":";
		url+=this->guiport;
		return (url);
	}

	if(server==QCC_SERVER)
	{
		url+=this->simulatorip;
		url+=":";
		url+=this->simulatorport;
		return (url);
	}
	
	
	if(server==SDN_SERVER)
	{
		url+=this->sdncontrollerip;
		url+=":";
		url+=this->sdncontrollerport;
		return (url);
	}
	
	
	if(server==QQC_SERVER)
	{
		url+=this->quantumchannelip;
		url+=":";
		url+=this->quantumchannelport;
		return (url);
	}
	return "";
}


bool Config::LoadConfiguration(string conffilename)
{
	string servername,ipaddress,port;
	string line;
	ifstream readConfFile(conffilename);
	while(getline(readConfFile,line))   
	{
		stringstream iss(line);
		getline(iss, servername, '=');
		getline(iss, ipaddress, ':');
		getline(iss, port, '\n');

		boost::trim_right(servername);
		boost::trim_left(servername);

		boost::trim_right(ipaddress);
		boost::trim_left(ipaddress);

		boost::trim_right(port);
		boost::trim_left(port);
	 
		this->SetServerAddress(servername, ipaddress, port);
	}
	readConfFile.close();
	return true;
}

