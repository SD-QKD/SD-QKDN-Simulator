/***********************************************      
QKD simulation
MAQAN
CSG CDAC(T)
June 2022
v1.0
************************************************/
#include <cstring>
#include <string>
#include <iostream>
#include "simulator.h"

using namespace std;

Simulator::Simulator()
{

	this->status = false;
	this->linkstatus = false;
	this->topostatus = false;
	this->linksource = new char(32);
	this->linkdestination= new char(32);
	strcpy(this->linksource, "");
	strcpy(this->linkdestination, "");

	this->controllerip = new char(32);
	strcpy(this->controllerip, "");

	this->netsquidip = new char(32);
	strcpy(this->netsquidip, "127.0.0.1");

	this->networkbase = new char(32);
	strcpy(this->networkbase,DEFAULT_NETWORK_BASE);

	this->networkmask = new char(32);
	strcpy(this->networkmask,DEFAULT_NETWORK_MASK);

	this->toponame = new char(32);
	strcpy(this->toponame,"MAQAN");

	this->toponodes = NODES_MAQAN;
	this->agentupdateinterval = SDN_AGENT_UPDATE_INTERVAL;
}

bool Simulator::Update(int interval)
{
	this->interval= interval;
	return true;

}

bool Simulator::SetDuration(int duarion)
{
	this->duration = duration;
	return true;

}


int Simulator::GetDuration()
{
	return (this->duration);

}

bool Simulator::SetInterval(int duarion)
{
	this->interval= interval;
	return true;

}

int Simulator::GetInterval()
{
	return (this->interval);

}

bool Simulator::SetStatus(bool status)
{
	this->status = status;
	return true;

}


bool Simulator::GetStatus()
{
	return (this->status);
}



bool Simulator::SetTopoStatus(bool status)
{
	this->topostatus = status;
	return true;

}

bool Simulator::GetTopoStatus()
{
	return (this->topostatus);
}




bool Simulator::SetLinkStatus(bool linkstatus)
{
	this->linkstatus = linkstatus;
	return true;

}

bool Simulator::GetLinkStatus()
{
	return (this->linkstatus);
}


bool Simulator::SetLinkSource(const char * linksource)
{
	strcpy(this->linksource, linksource);
	return true;
}

const char * Simulator::GetLinkSource()
{
	return (this->linksource);

}

bool Simulator::SetLinkDestination(const char * linkdestination)
{
	strcpy(this->linkdestination, linkdestination);
	return true;

}
const char * Simulator::GetLinkDestination()
{
	return (this->linkdestination);

}


bool Simulator::SetControllerIP(char *ip)
{
	strcpy(this->controllerip, ip);
	return true;
}

char* Simulator::GetControllerIP()
{
	return (this->controllerip);

}

bool Simulator::SetControllerPort(int port)
{

	this->controllerport = port;
	return true;
}

int Simulator::GetControllerPort()
{

	return (this->controllerport);

}


bool Simulator::SetNetSquidIP(char *ip)
{
	strcpy(this->netsquidip, ip);
	return true;
}

char* Simulator::GetNetSquidIP()
{
	return (this->netsquidip);

}

bool Simulator::SetNetSquidPort(int port)
{

	this->netsquidport = port;
	return true;
}

int Simulator::GetNetSquidPort()
{

	return (this->netsquidport);

}


bool Simulator::SetNetworkBase(char *base)
{
	strcpy(this->networkbase, base);
	return true;
}

char* Simulator::GetNetworkBase()
{
	return (this->networkbase);
}

bool Simulator::SetNetworkMask(char *mask)
{
	strcpy(this->networkmask, mask);
	return true;

}

char* Simulator::GetNetworkMask()
{

	return (this->networkmask);
}


bool Simulator::SetTopoID(int topoid)
{
	this->topoid=topoid;
	return true;
}
int Simulator::GetTopoID()
{
	return(this->topoid);
}

bool Simulator::SetTopoName(char *toponame)
{
	strcpy(this->toponame, toponame);
	return true;

}
char* Simulator::GetTopoName()
{

	return (this->toponame);
}

bool Simulator::SetTopoNodes(int nodes)
{
	this->toponodes = nodes;
	return true;
}

int Simulator::GetTopoNodes()
{
	return (this->toponodes);
}


int Simulator::GetNodesInTopology(int id)
{
	switch(id)
	{
		case TOPO_ID_MAQAN:
			return(NODES_MAQAN);
		break;

		case TOPO_ID_CUSTOM:
			return(GetTopoNodes());
		break;

		default:
			return(0);
		break;
	}
	return NODES_MAQAN;

}

int Simulator::GetNodesCount()
{
	int nodenum = json_array_size(this->nodes); 
	if(nodenum <= 0)
		return 0;
	else
		return nodenum;
}



bool Simulator::SetAgentUpdationInterval(int updateinterval)
{
	this->agentupdateinterval = updateinterval;
	return true;
}

int Simulator::GetAgentUpdationInterval()
{
	return(this->agentupdateinterval);

}


json_t * Simulator::GetJsonDataObject()
{
	json_t * json_body = json_object();
	
	GetJsonDataObject(json_body);
	return json_body;

}


json_t * Simulator::GetJsonDataObject(json_t *json_body)
{
	
	json_object_set_new(json_body, "id", json_integer(this->id));
	json_object_set_new(json_body, "duration", json_integer(this->duration));
	json_object_set_new(json_body, "interval", json_integer(this->interval));
	json_object_set_new(json_body, "status", json_integer(this->status));
	
	return json_body;
}


bool Simulator::SetNodes(json_t *nodearray)
{
	this->nodes = nodearray;
	return true;
}
json_t* Simulator::GetNodes()
{	
	return (this->nodes);
}


char * Simulator::GetNodeName(char * nodeid)
{
	int nodenum = json_array_size(this->nodes);
	json_t *node;
	char *nodeid_topo = NULL, *nodename=NULL;
	for(int i=0; i< nodenum; i++)
	{
		node = json_array_get(this->nodes, (size_t)i);
		nodeid_topo = (char *)json_string_value(json_object_get(node, "nodeid"));
		if(strcmp(nodeid, nodeid_topo)==0)
		{
			 nodename = (char *)json_string_value(json_object_get(node, "nodename"));  
	   		return (nodename);
		}
	}
	return (char*)"";
}

char * Simulator::GetNodeParams(int indexnode, int idparam)
{
	int nodenum = json_array_size(this->nodes);
	json_t *node;
	char *nodeparam = NULL;
	
	if(indexnode <= nodenum)
	{
		node = json_array_get(this->nodes, (size_t)indexnode);
		switch(idparam)
		{
			case PARAM_NODE_ID:
				nodeparam = (char *)json_string_value(json_object_get(node, "nodeid"));  
				break;
			case PARAM_NODE_NAME:
				nodeparam = (char *)json_string_value(json_object_get(node, "nodename"));  
				break;
			case PARAM_NODE_IP:
				nodeparam = (char *)json_string_value(json_object_get(node, "nodeip")); 
				break;
			case PARAM_NODE_PORT:
				nodeparam = (char *)json_string_value(json_object_get(node, "nodeport"));  
				break;
			default:
				nodeparam = (char *)json_string_value(json_object_get(node, "nodeid"));  
				break;
		}
	   return (nodeparam);
	}
	else
		return (char*)"";

}




bool Simulator::SetLinks(json_t *linksarray)
{
	this->links = linksarray;
	return true;
}

json_t* Simulator::GetLinks()
{
	return (this->links);
}


bool Simulator::SetCCLinks(json_t *linksarray)
{
	this->cclinks = linksarray;
	return true;
}

json_t* Simulator::GetCCLinks()
{
	return (this->cclinks);
}

char * Simulator::GetLinkParams(int indexlink, int idparam)
{
	int linknum = json_array_size(this->links);
	json_t *link;
	char *linkparam = NULL;
	
	if(indexlink <= linknum)
	{
		link = json_array_get(this->links, (size_t)indexlink);
		switch(idparam)
		{
			case PARAM_LINK_ID:
				linkparam = (char *)json_string_value(json_object_get(link, "linkid"));  
				break;
			case PARAM_LINK_NAME:
				linkparam = (char *)json_string_value(json_object_get(link, "linkname"));  
				break;
			case PARAM_LINK_SOURCE:
				linkparam = (char *)json_string_value(json_object_get(link, "sourcenode"));  
				break;
			case PARAM_LINK_DESTINATION:
				linkparam = (char *)json_string_value(json_object_get(link, "destinationnode"));  
				break;
			case PARAM_LINK_CHANNEL_TYPE:
				linkparam = (char *)json_string_value(json_object_get(link, "channeltype"));  
				break;
			default:
				linkparam = (char *)json_string_value(json_object_get(link, "linkid"));  
				break;
		}
	   return (linkparam);
	}
	else
		return (char*)"";

}



int Simulator::GetQuantumChannels(const char *nodeid)
{
	int qc_connected=0;
	int linknum = json_array_size(this->links);
	json_t *link;
	char *nodeid_src = NULL, *nodeid_dest = NULL;
	//cout<<" Link num "<<linknum<<endl;
	for(int i=0; i<linknum; i++)
	{
		link = json_array_get(this->links, (size_t)i);
		nodeid_src = (char *)json_string_value(json_object_get(link, "sourcenode")); 
		nodeid_dest = (char *)json_string_value(json_object_get(link, "destinationnode")); 
		if((nodeid_src != NULL) && (nodeid_dest != NULL))
		{
			if( (strcmp(nodeid, nodeid_src)== 0 ) || (strcmp(nodeid, nodeid_dest)==0) )
			{
				qc_connected++;
			}
		}
		else
		{
			cout<<"Link Parameters - Not Available (source/destination node)"<<endl;
		}
	}
	return qc_connected;
}

char* Simulator::GetChannelParams(const char *nodeid, int quantumchannelid, int idparam)
{
	int qc_id=0;
	int linknum = json_array_size(this->links);
	json_t *link;
	char *nodeid_src = NULL, *nodeid_dest = NULL;
	char *linkparam = NULL;

	for(int i=0; i<linknum; i++)
	{
		link = json_array_get(this->links, (size_t)i);
		nodeid_src = (char *)json_string_value(json_object_get(link, "sourcenode")); 
		nodeid_dest = (char *)json_string_value(json_object_get(link, "destinationnode")); 
		if( (strcmp(nodeid, nodeid_src)== 0 ) || (strcmp(nodeid, nodeid_dest)==0) )
		{
			qc_id++;
			if(quantumchannelid == qc_id)
			{
				switch(idparam)
				{
					case PARAM_LINK_ID:
						linkparam = (char *)json_string_value(json_object_get(link, "linkid"));
						break;
					case PARAM_LINK_NAME:
						linkparam = (char *)json_string_value(json_object_get(link, "linkname"));
						break;
					case PARAM_LINK_SOURCE:
						linkparam = (char *)json_string_value(json_object_get(link, "sourcenode"));
						break;
					case PARAM_LINK_CHANNEL_TYPE:
						linkparam = (char *)json_string_value(json_object_get(link, "channeltype"));  
						if(linkparam==NULL)
						{
							linkparam = (char *)json_string_value(json_object_get(link, "sourcenode"));
							if(strcmp(linkparam,nodeid) == 0)
								linkparam = (char *)"TX";
							else
								linkparam = (char *)"RX";
						}
						break;
					case PARAM_LINK_DESTINATION:
						linkparam = (char *)json_string_value(json_object_get(link, "destinationnode"));
						break;	
					case PARAM_LINK_NEIGHBOUR_NODE:
						linkparam = (char *)json_string_value(json_object_get(link, "destinationnode"));
						if(strcmp(linkparam,nodeid) == 0)
							linkparam = (char *)json_string_value(json_object_get(link, "sourcenode"));
						break;			
				}
				return linkparam;
			}
		}
	}
	return (char*)("");
}


char* Simulator::GetCCChannelParams(const char *nodeid, int idparam)
{
	int linknum = json_array_size(this->cclinks);
	json_t *link;
	char *nodeid_src = NULL, *dest = NULL;
	char *linkparam = NULL;

	for(int i=0; i<linknum; i++)
	{
		link = json_array_get(this->cclinks, (size_t)i);
		nodeid_src = (char *)json_string_value(json_object_get(link, "source")); 
		dest = (char *)json_string_value(json_object_get(link, "destination")); 
		if(strcmp(nodeid, nodeid_src)== 0 ) 
		{
				switch(idparam)
				{
					case PARAM_LINK_CLASSICAL_ID:
						linkparam = (char *)json_string_value(json_object_get(link, "linkid")); 
						if(linkparam==NULL)
							linkparam = (char *)"eth0";
						break;
					case PARAM_LINK_CLASSICAL_NAME:
						linkparam = (char *)json_string_value(json_object_get(link, "linkname"));  
						if(linkparam==NULL)
							linkparam = (char *)"LAN-1";
						break;
					case PARAM_LINK_CLASSICAL_STATUS:
						linkparam = (char *)json_string_value(json_object_get(link, "linkstatus"));  
						if(linkparam==NULL)
							linkparam = (char *)"UP";
						break;					
				}
				return linkparam;
		}
	}
	return (char*)("");
}



bool Simulator::SetLogLevel(int level)
{
	this->log_level = level;
	return true;
}


int Simulator::GetLogLevel()
{
	return (this->log_level);

}


bool Simulator::SetQNEHome(string qne_home)
{
	this->qne_home = qne_home;
	return true;
}


string Simulator::GetQNEHome()
{
	return (this->qne_home);
}
