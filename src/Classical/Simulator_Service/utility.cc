/***********************************************      
QKD simulation
MAQAN
CSG CDAC(T)
June 2022
v1.0
************************************************/
#include <cstring>
#include <iostream>
#include <bits/stdc++.h>
#include <cstdlib>
#include "simulator.h"
#include "utility.h"

using namespace std;

bool getSimulatorStatus()
{
	return (QSimulator.GetStatus());
}

bool setSimulatorStatus(bool status)
{
	QSimulator.SetStatus(status);
	return true;

}

bool getTopologyStatus()
{
	return (QSimulator.GetTopoStatus());
}

bool setTopologyStatus(bool status)
{
	QSimulator.SetTopoStatus(status);
	return true;

}

bool getTopologyStatus(int topoid)
{
	int simtopoid = QSimulator.GetTopoID();
	if(simtopoid == topoid)
		return (QSimulator.GetTopoStatus());
	else
		return false;

}
bool setTopologyStatus(int topoid, bool status)
{
	QSimulator.SetTopoID(topoid);
	QSimulator.SetTopoStatus(status);
	return true;
}

bool setControllerIP(char *ip)
{
	QSimulator.SetControllerIP(ip);
	return true;

}

char* getControllerIP()
{
	return (QSimulator.GetControllerIP());

}

bool setControllerPort(int port)
{
	QSimulator.SetControllerPort(port);
	return true;
}


int getControllerPort()
{
	return (QSimulator.GetControllerPort());

}


bool setNetSquidIP(char *ip)
{
	QSimulator.SetNetSquidIP(ip);
	return true;

}

char* getNetSquidIP()
{
	return (QSimulator.GetNetSquidIP());

}

bool setNetSquidPort(int port)
{
	QSimulator.SetNetSquidPort(port);
	return true;
}


int getNetSquidPort()
{
	return (QSimulator.GetNetSquidPort());

}


bool setNetworkBase(char *base)
{
	QSimulator.SetNetworkBase(base);
	return true;
}

char* getNetworkBase()
{
	return (QSimulator.GetNetworkBase());

}

bool setNetworkMask(char *mask)
{
	QSimulator.SetNetworkMask(mask);
	return true;

}

char* getNetworkMask()
{
	return (QSimulator.GetNetworkMask());

}


bool setTopologyID(int id)
{
	QSimulator.SetTopoID(id);
	return true;
}

int getTopologyID()
{
  return (QSimulator.GetTopoID());
}


bool setTopologyNodes(int nodes)
{
	QSimulator.SetTopoNodes(nodes);
	return true;
}

int getTopologyNodes()
{
	return (QSimulator.GetTopoNodes());
}


int getNodesInTopology(int id)
{
	return(QSimulator.GetNodesInTopology(id));
}

int getNodesCount()
{
	return(QSimulator.GetNodesCount());
}


bool setAgentUpdationInterval(int updationinterval)
{
	QSimulator.SetAgentUpdationInterval(updationinterval);
	return true;
}

int getAgentUpdationInterval()
{
	return(QSimulator.GetAgentUpdationInterval());
}


bool setNodesDetails(json_t* nodes)
{
	QSimulator.SetNodes(nodes);
	return true;

}

json_t* getNodesDetails()
{
	return (QSimulator.GetNodes());
}


char * getNodeName(char *nodeid)
{
	return (QSimulator.GetNodeName(nodeid));
}


char * getNodeParams(int indexnode, int idparam)
{
	return (QSimulator.GetNodeParams(indexnode, idparam));
}

bool setLinksDetails(json_t* links)
{
	QSimulator.SetLinks(links);
	return true;

}

json_t* getLinksDetails()
{
	return (QSimulator.GetLinks());
}


bool setCCLinksDetails(json_t* cclinks)
{
	QSimulator.SetCCLinks(cclinks);
	return true;

}

json_t* getCCLinksDetails()
{
	return (QSimulator.GetCCLinks());
}


char * getLinkParams(int indexlink, int idparam)
{
	return (QSimulator.GetLinkParams(indexlink, idparam));
}

int getQuantumChannels(const char *nodeid)
{
	return (QSimulator.GetQuantumChannels(nodeid));
}

char* getChannelParams(const char *nodeid, int quantumchannelid, int idparam)
{
	return (QSimulator.GetChannelParams(nodeid, quantumchannelid, idparam));
}

char* getCCChannelParams(const char *nodeid, int idparam)
{
	return (QSimulator.GetCCChannelParams(nodeid, idparam));
}

char *getCurrentDateTime()
{
	time_t curr_time;
	tm * curr_tm;
	char datetime_string[64];
	char *dt=(char*)malloc(64);
	time(&curr_time);
	curr_tm = localtime(&curr_time);
	strftime(datetime_string, 64, "%d-%m-%Y %H:%M:%S", curr_tm);
	strcpy(dt,datetime_string);
	//cout<<" Date time "<<dt<<endl;
	return dt;
}

int getLogLevel()
{
	return(QSimulator.GetLogLevel());
}

bool setLogLevel(int level)
{
	QSimulator.SetLogLevel(level);
	return true;
}

string getQNEHome()
{
	return(QSimulator.GetQNEHome());
}

bool setQNEHome()
{
	const char* var_name = "QNE_HOME";
    const char* var_value = std::getenv(var_name);
	string qne_home="";
    if (var_value != nullptr) 
	{
		qne_home = var_value;
		QSimulator.SetQNEHome(qne_home);
		return true;
    } 
	else 
	{
		return false;
    }
	return false;
}



/* return 1 if IP string is valid, else return 0 */
int isValidIP(string s)
{
	int n = s.size();
	if (n < 7)
		return false;
	vector<string> v;
	stringstream ss(s);
	while (ss.good()) {
		string substr;
		getline(ss, substr, '.');
		v.push_back(substr);
	}
	if (v.size() != 4)
		return false;
	for (int i = 0; i < v.size(); i++) {
		string temp = v[i];

		if (temp.size() > 1) {
			if (temp[0] == '0')
				return false;
		}
		for (int j = 0; j < temp.size(); j++) {
			if (isalpha(temp[j]))
				return false;
		}
		if (stoi(temp) > 255)
			return false;
	}
	return true;
}

