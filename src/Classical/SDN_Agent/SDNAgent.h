
/*###################################################################### 
# 
# File Name: SDNAgent.h
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 25-11-2022
# 
# Purpose : Simulation
# 
# Description : SDN Agent Simulation header 
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
#			: Aneesh Kumar KB (aneesh_kb@cdac.in)
#			: Neethu V (neethuv@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : SDN agent module
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 
#ifndef SDNAGENT_H
#define SDNAGENT_H
#include "ns3/socket.h"
#include "ns3/application.h" 
#include "ns3/tcp-socket-base.h"
#include <queue>
#include <string.h>
#include <jansson.h>
#include "../Key_Store/KeyStore.h"
#include<thread>
#include <map>
#include <map>
#include "TSQueue.h"

#define SDN_AGENT_PORT			              7500
#define SDN_AGENT_PORT_STRING		          "7500"
#define SDN_SERVER_URL_APPEND		          "/qkd-controller/AgentPush/status"
#define SDN_SERVER_LOG_URL_APPEND	        "/qkd-controller/AgentPush/log"

#define SDN_KEY_STATUS_URL_APPEND	        "/api/v1/keys/SAE_ID/status"
#define SDN_GET_KEY_URL_APPEND		        "/api/v1/keys/SAE_ID/enc_keys"
#define SDN_GET_KEY_ID_URL_APPEND	        "/api/v1/keys/SAE_ID/dec_keys"
#define SDN_NODEINFO_URL_APPEND		        "/NodeInfo"
#define SDN_NETSQUID_URL_APPEND		        "/SDN/response"
#define BB84_SIFTING_URL_APPEND	          "/bb84/PostProcessing"		
#define SDN_GET_KEY_NOFIFY_URL_APPEND	    "/KeyNotify"
#define REGISTER_APPLICATION_URL_APPEND 	"/register"
#define KEY_PROVISION_URL_APPEND 	        "/keyprovision"
#define KEY_PROVISION_STATUS_URL_APPEND 	"/keyprovisionStatus"

#define SDN_COMMAND_URL_APPEND		          "/SDN/command"
#define SDN_COMMAND_RESPONSE_URL_APPEND	    "/qkd-controller/AgentPush/command"


#define NETSQUID_PROVISION_URL_APPEND		    "/sim/link/provision"
#define NETSQUID_LINK_STOP_URL_APPEND		    "/sim/link/stop"
#define NETSQUID_LINK_STATUS_URL_APPEND		  "/sim/link/status"
#define KEYMANAGER_CONTROLLER_URL_APPEND 	  "/qkd-controller/application/registerApp"
#define KEYPROVISION_CONTROLLER_URL_APPEND 	"/qkd-controller/keyProvision/provision"
#define KEYPROVISION_STATUS_CONTROLLER_URL_APPEND 	"/qkd-controller/keyProvision/status/"


#define CONTROLLER_KEYMANAGER_URL_APPEND	  "/keyManager/reserveKeys"
#define NODE_KEY_STATUS_URL_APPEND		      "/inventory/getallnodekeystatus"
            
#define NODE_CONF_FILE_DIR  		            "/conf/nodes"
#define STATUS_FILE_NAME 		                "STATUS.txt"
#define COMMAND_FILE_NAME 		              "COMMAND.txt"


#define MESSAGE_TYPE_STATUS		              "status"
#define MESSAGE_TYPE_COMMAND		            "command"
#define FILENAME_SHARED_KEY		              "/conf/key.txt"


#define	MESSAGE_REST_RECEIVED	      "{\"STATUS\":\"Received\"}"
#define MESSAGE_REST_SUCCESS        "{\"STATUS\":\"Success\"}"
#define MESSAGE_REST_FAILURE        "{\"STATUS\":\"Failure\"}"
#define MESSAGE_REST_UNKNOWN        "{\"STATUS\":\"Unknown\"}"
#define MESSAGE_REST_INVALID_DATA   "{\"STATUS\":\"Invalid data format\"}" 
#define MESSAGE_REST_NO_NODEID      "{\"STATUS\":\"No Node ID\"}" 
#define MESSAGE_REST_NO_KEYSTORE    "{\"STATUS\":\"No Keystore\"}" 
#define MESSAGE_REST_NO_COMMAND_ID  "{\"STATUS\":\"No Command ID\"}" 

#define CALLBACK_NONE			              0
#define CALLBACK_NODEINFO		            1
#define CALLBACK_NETSQUID		            2
#define CALLBACK_KEYSTORE_STATUS	      3
#define CALLBACK_KEYSTORE_GETKEY	      4
#define CALLBACK_KEYSTORE_GETKEYID	    5
#define CALLBACK_BB84_SIFTING		        6
#define CALLBACK_KEY_NOTIFY		          7
#define CALLBACK_SDN_COMMAND		        8
#define CALLBACK_REGISTER_APPLICATION 	9
#define CALLBACK_KEY_PROVISION		      10
#define CALLBACK_CONTROLLER_KM		      11	
#define CALLBACK_NODE_KEY_STATUS	      12
#define CALLBACK_KEY_PROVISION_STATUS		13


#define MESSAGE_QUEUE_TYPE_NONE         0
#define MESSAGE_QUEUE_TYPE_TX           1
#define MESSAGE_QUEUE_TYPE_ITX          2

#define MAX_STORE_IDS			              5
#define STORE_ID_GET			              0
#define STORE_ID_GET_CREATE		          1

#define LOG_LEVEL_DEFAULT	              0
#define LOG_LEVEL_PACKETS	              1
#define LOG_LEVEL_PERIODICAL	          2
#define LOG_LEVEL_DEBUG		              3	
#define LOG_TO_FILE		                  4

using namespace ns3;
using namespace std;

namespace ns3
{
class Message : public Object, SimpleRefCount<Message>
{
    private:
      string endpoint;
      string iRxmessage;
      string iTxMessage;
      string rxMessage;
      string txMessage;
      int state;
      string updateTime;
      mutable uint32_t m_count;
    public:
      Ptr<Socket> socket;
      Ptr<Socket> isocket;
      string packet;  
      int iTxCState;     
      string toIp;
      int toPort;
      string toUrl;
      bool crypto;
      int cbid;

      Message()
      :socket(nullptr),
      isocket(nullptr),
      packet(""),
      iTxCState(0)     
      {
        endpoint="";
        iRxmessage="";
        iTxMessage="";
        rxMessage="";
        state = 0;
        updateTime = "";
        m_count =1;
      }
      ~ Message()
      {
	      socket = nullptr;
	      isocket = nullptr;
	      packet = "";
	      iTxCState = 0;
      }
      inline void Ref() const
      {
		    m_count++;
      }
      inline void Unref() const
      {
    		  m_count--;
      }
   };



  class SDNAgent : public Application 
  {
    public:
      string nodeid;
      string nodename;
      int msgIdStatusSent;
      int msgIdCommandSent;
      string basis;
      pthread_t thread_id_restq;
      int thread_restq_params;
      thread thread_restq_process;

      int thread_tsq_params;
      thread thread_tsq_process;
      bool processQ;
      map<string, pair<string,string>> saeid_map;

      SDNAgent ();
      virtual ~SDNAgent ();
      
      bool ConnectionRequestCallback (Ptr<Socket> socket, const Address &address);
      void NewConnectionCreatedCallback (Ptr<Socket> socket, const Address &address);
      void NormalCloseCallback(Ptr<Socket> socket);
      void ErrorCloseCallback(Ptr<Socket> socket);
      void DataSentCallback(Ptr<Socket> socket, uint32_t datsent);

    	void rxMessageReceived(Ptr<Socket> socket);
      void iRxMessageReceived(Ptr<Socket> socket);
    	void processQueues(int thread_tsq_params);
      void ScheduleTxDataQueue();
      void ScheduleiTxDataQueue();

	    bool SetSAEIdMap(string request, string response);

	    bool log_socket(Ptr<Socket> socket, string modulename);

      string getJsonData(string packetData);
      int getRestCallbackID(string packetData);
    	bool isJsonData(string strpacket);

      void PeriodicStatusUpdate(void);  
      int UpdateNodeStatus (string messagetype, string nodeid, string status);

      
   		int SendToQ(char *ip, int port, string url, json_t *json_data, bool crypto);
	    int RestSend(Ptr<Message> Msg);
	    int RestSend(Ptr<Socket> socket, string data, Address to, string append_url);
      int RestSendResponse(Ptr<Socket> socketresponse, string data);
	    int RestSend(Ptr<Socket> socket, string data, Address to, string append_url, bool crypto=true);


      char *EncryptAndEncode(json_t * jsondata);
      char *EncryptAndEncode(const char* plaintextdata);

      int SendPacket (Ptr<Packet> packet, Ipv4Address destination, uint16_t port);
      bool SetNodeId(string nodeid);
      string GetNodeId();
      bool SetNodeName(string nodeid);
      string GetNodeName();

	    json_t* postCommandResponse(char *messageid, char* command, char*commandid, char *status);
	
   		int getMessageQueueType(int cbid);
   		string getMessageQueueIp(int cbid);
   		int getMessageQueuePort(int cbid);
   		string getMessageQueueUrl(int cbid);

 
      json_t* callbackNodeTest(string jsondata);
      json_t* callbackNodeInfo(string jsondata);


	    json_t* callbackKeyStoreStatus(string jsondata);
      json_t* callbackKeyStoreGetKey(string jsondata);
      json_t* callbackKeyStoreGetKeyId(string jsondata);
      json_t* callbackBB84Sifting(string jsondata);
	    json_t* callbackKeyNotify(string jsondata);
      
      json_t* callbackSDNCommand(string jsondata);
      json_t* callbackNetSquid(string jsondata);

      json_t* callbackRegisterApplication(string jsondata);
      json_t* callbackKeyProvision(string jsondata);
      json_t* callbackKeyProvisionStatus(string jsondata);
   
      json_t* callbackControllerKm(string jsondata);
      json_t* callbackNodeKeyStatus(string jsondata);
      
      string getSDNAgentIP(string nodeid);
      string getSDNAgentIPFromController(string nodeid);
      string doSifting(string bits, string basis, string source, string destination);

      KeyStore store[MAX_SAE_IDS];
      
      int GetStoreId(int sae_id, string source, string destination, int mode=STORE_ID_GET);
      int GetStoreIdd(string node_id,int mode=STORE_ID_GET);
      json_t* ComposeSDNControllerCommandResponse(int messageid, char* commandid, const char *status);
      json_t* ComposeSDNControllerStatusUpdate(int messageId, const char *nodeid, const char *ip, bool status, float qber, float keyrate, string keygen_status, json_t *path);
      bool isChannelId(json_t *path, char *channelId);

      int postCommandFileUpdate(string jsondata);
      int postStatusFileUpdate(string jsondata);
      
      bool postStatusUpdate(bool lin_status,  string keygen_status, float qber, float keyrate, json_t *path);
      bool postCommandUpdate(char * commandid, char * status);
      bool postCommandUpdate(char *messageid, char *command, char *commandid, char *response);

      bool getLinkStatus(const char *nodeid, int qchannelid, char * qcid, json_t *paths);

      string getMatchList(string bits, string basis, string source, string destination);
      string getSiftedKey(string bits, string basis, string source, string destination, string matchlist);    
          
      int GetLogLevel();
      bool SetLogLevel(int level);
      bool Log(string modulename, string data);
      bool Log(string modulename, char *ip, int port, bool status, int bytes);

	    json_t* processCallbackCommands(int cbid, string commands);

	    void ConnectiTxCallbackSuccess(Ptr<Socket> socket);
      void ConnectiTxCallbackFailure(Ptr<Socket> socket);
      void iTxDataSentCallback(Ptr<Socket> socket, uint32_t dataSent);

            
    private:     
      queue<string> restDQ;
      queue<Ptr<Socket>> restSQ;
      queue<Address> restAQ;
      virtual void StartApplication ();
      virtual void StopApplication ();

      Ptr<Socket> m_recv_socket;     
 
      uint16_t m_port; 
      Ptr<Socket> m_send_socket; 
      int log_level;  
      
      TSQueue<Ptr<Message>> rxQueue;
      TSQueue<Ptr<Message>> txQueue;
      TSQueue<Ptr<Message>> iRxQueue;
      TSQueue<Ptr<Message>> iTxQueue;
      map<Ptr<Socket>, Ptr<Message>> rxMessageMap;
      map<Ptr<Socket>, Ptr<Message>> iRxMessageMap; 
      
  };
}

#endif
