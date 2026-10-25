/***********************************************      
QKD NS simulation
MAQAN
CSG CDAC(T)
Sep 2022
v1.0
************************************************/
#ifndef UTILITY_H
#define UTILITY_H
#include <jansson.h>
#include <string>
using namespace std;

#define PARAM_NODE_ID		1
#define PARAM_NODE_NAME		2
#define PARAM_NODE_IP		3
#define PARAM_NODE_PORT		4

bool getSimulatorStatus();
bool setSimulatorStatus(bool status);

bool getTopologyStatus();
bool setTopologyStatus(bool status);

bool getTopologyStatus(int topoid);
bool setTopologyStatus(int topoid, bool status);

bool setControllerIP(char *ip);
char* getControllerIP();

bool setControllerPort(int port);
int getControllerPort();

bool setNetSquidIP(char *ip);
char* getNetSquidIP();

bool setNetSquidPort(int port);
int getNetSquidPort();


bool setNetworkBase(char *base);
char* getNetworkBase();
bool setNetworkMask(char *mask);
char* getNetworkMask();

bool setTopologyID(int id);
int getTopologyID();

int getNodesInTopology(int id);
int getNodesCount();

int isValidIP(string s);

bool setAgentUpdationInterval(int updationinterval);
int getAgentUpdationInterval();

bool setNodesDetails(json_t*);
json_t* getNodesDetails();
char * getNodeName(char *nodeid);
char * getNodeParams(int indexnode, int idparam);

bool setLinksDetails(json_t*);
json_t* getLinksDetails();

bool setCCLinksDetails(json_t*);
json_t* getCCLinksDetails();

char * getLinkParams(int indexlink, int idparam);

int getQuantumChannels(const char *nodeid);
char* getChannelParams(const char *nodeid, int quantumchannelid, int idparam);
char* getCCChannelParams(const char *nodeid, int idparam);

char *getCurrentDateTime();

int getLogLevel();
bool setLogLevel(int level);

string getQNEHome();
bool setQNEHome();

#endif
