/***********************************************      
QKD NS simulation
MAQAN
CSG CDAC(T)
Sep 2022
v1.0
************************************************/
#ifndef SIMULATOR_H
#define SIMULATOR_H
#include <jansson.h>
#include <string>
#include <cstring>

#define DEFAULT_NETWORK_BASE	"10.1.1.0"
#define DEFAULT_NETWORK_MASK	"255.255.255.0"
#define TOPO_ID_MAQAN		1
#define TOPO_ID_CUSTOM		4

#define NODES_MAQAN			5
#define NODES_CUSTOM		5

#define PARAM_LINK_ID				1
#define PARAM_LINK_NAME				2
#define PARAM_LINK_SOURCE			3
#define PARAM_LINK_DESTINATION		4
#define PARAM_LINK_NEIGHBOUR_NODE 	5
#define PARAM_LINK_CHANNEL_TYPE		6
#define PARAM_LINK_CLASSICAL_ID		7
#define PARAM_LINK_CLASSICAL_NAME	8
#define PARAM_LINK_CLASSICAL_STATUS	9

#define PARAM_NODE_ID		1
#define PARAM_NODE_NAME		2
#define PARAM_NODE_IP		3
#define PARAM_NODE_PORT		4

#define SDN_AGENT_UPDATE_INTERVAL 60
using namespace std;

class Simulator
{
	int id;
	int duration;
	int interval;
	int agentupdateinterval;
	bool status;
	bool topostatus;
	bool linkstatus;
	char *linksource;
	char *linkdestination;
	
	char *controllerip;
	int controllerport;
	
	char *netsquidip;
	int netsquidport;
	
	char *networkbase;
	char *networkmask;
	int topoid;
	char *toponame;
	int toponodes;
	
	json_t *nodes;
	json_t *links; 
	json_t *cclinks; 

	int log_level;
	string qne_home;
	
public:
	Simulator();
	
	bool Update(int interval);
	
	bool SetDuration(int duarion);
	int GetDuration();
	
	bool SetInterval(int duarion);
	int GetInterval();
	
	bool SetStatus(bool status);
	bool GetStatus();
	
	bool SetTopoStatus(bool topostatus);
	bool GetTopoStatus();
	
	bool SetLinkStatus(bool linkstatus);
	bool GetLinkStatus();
	
	bool SetLinkSource(const char * linksource);
	const char * GetLinkSource();
	
	bool SetLinkDestination(const char * linkdestination);
	const char * GetLinkDestination();
	
	bool SetControllerIP(char *ip);
	char* GetControllerIP();
	
	bool SetControllerPort(int port);
	int GetControllerPort();
	
	bool SetNetSquidIP(char *ip);
	char* GetNetSquidIP();
	
	bool SetNetSquidPort(int port);
	int GetNetSquidPort();
	
	bool SetNetworkBase(char *base);
	char* GetNetworkBase();
	
	bool SetNetworkMask(char *mask);
	char* GetNetworkMask();
	
	bool SetTopoID(int topoid);
	int GetTopoID();
	
	bool SetTopoName(char *mask);
	char* GetTopoName();

	bool SetTopoNodes(int nodes);
	int GetTopoNodes();
	
	int GetNodesInTopology(int id);
	int GetNodesCount();

	bool SetAgentUpdationInterval(int updateinterval);
	int GetAgentUpdationInterval();
	
	json_t * GetJsonDataObject(); 
	json_t * GetJsonDataObject(json_t *);	
	
	bool SetNodes(json_t *);
	json_t* GetNodes();
	char * GetNodeName(char *nodeid);
	char * GetNodeParams(int indexnode, int idparam);
	
	bool SetLinks(json_t *);
	json_t* GetLinks();

	bool SetCCLinks(json_t *);
	json_t* GetCCLinks();

	char * GetLinkParams(int indexlink, int idparam);

	int GetQuantumChannels(const char *nodeid);
	char* GetChannelParams(const char *nodeid, int quantumchannelid, int idparam);
	char* GetCCChannelParams(const char *nodeid, int idparam);

	bool SetLogLevel(int level);
	int GetLogLevel();
	
	bool SetQNEHome(string qne_home);
	string GetQNEHome();
};
static Simulator QSimulator;
#endif
