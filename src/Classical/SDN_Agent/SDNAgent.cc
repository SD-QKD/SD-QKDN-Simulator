/*######################################################################
#
# File Name: SDNAgent.cc
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
# Description : SDN Agent Simulation for NS3 and REST service to TestApp
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
#include "ns3/log.h"
#include "ns3/udp-socket.h"
#include "ns3/simulator.h"
#include "ns3/csma-net-device.h"
#include "ns3/ethernet-header.h"
#include "ns3/arp-header.h"
#include "ns3/ipv4-header.h"
#include "ns3/udp-header.h"
#include "ns3/tcp-header.h"
#include "ns3/uinteger.h"
#include "ns3/boolean.h"
#include "ns3/ipv4-raw-socket-impl.h"
#include "ns3/socket-factory.h"
#include "ns3/ipv4-raw-socket-impl.h"
#include "ns3/ipv4-l3-protocol.h"
#include "ns3/icmpv4.h"
#include <ns3/callback.h>
#include <ns3/config.h>
#include <ns3/pointer.h>
#include <ns3/uinteger.h>
#include <ns3/packet.h>
#include <ns3/socket.h>
#include <ns3/tcp-socket.h>
#include <ns3/tcp-socket-factory.h>
#include <ns3/inet-socket-address.h>
#include <ns3/unused.h>
#include <string.h>
#include <cstring>
#include <unistd.h>
#include <bits/stdc++.h>
#include <iostream>
#include <queue>
#include <string>
#include <vector>
#include <sstream>
#include <pthread.h>
#include <iostream>
#include <numeric>
#include "SDNAgent.h"
#include "post-processing.h"
#include "crypto.h"
#include "ns3/core-module.h"
#include "../Simulator_Service/utility.h"
#include "../QKD_Node/QKDNode.h"
using namespace std;
using namespace ns3;

namespace ns3
{
	char *g_command_id = NULL;

	SDNAgent::SDNAgent()
	{
		Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1460));
		m_port = SDN_AGENT_PORT;
		this->msgIdStatusSent = 0;
		this->msgIdCommandSent = 100000;
		g_command_id = (char *)malloc(128);
		this->basis = "";
		this->nodeid="";
		ofstream logfile;
		string qne_home = getQNEHome();
		string logfilename = qne_home + QKD_NODE_FILE_BASE + GetNodeId() + "/" + LOG_FILE_NAME;
		logfile.open(logfilename);
		logfile<<"";
		logfile.close();

		thread_tsq_process = thread(&SDNAgent::processQueues, this, this->thread_tsq_params);
		processQ = true;
	}

	SDNAgent::~SDNAgent()
	{
		processQ = false;
		thread_tsq_process.join();
		//cout<<endl<<"SDN Agent STOP - FINISHED"<<endl;
	}

	bool SDNAgent::ConnectionRequestCallback(Ptr<Socket> socket, const Address &address)
	{
		return true; // accept the connection request.
	}

	void SDNAgent::NewConnectionCreatedCallback(Ptr<Socket> socket, const Address &address)
	{
		// cout<<"New Connection Created      ["<<socket<<" :  "<<address<<"]"<<endl;
		socket->SetCloseCallbacks (MakeCallback (&SDNAgent::NormalCloseCallback,this), MakeCallback (&SDNAgent::ErrorCloseCallback, this));
		socket->SetRecvCallback (MakeCallback (&SDNAgent::rxMessageReceived, this)); 
		socket->SetDataSentCallback(MakeCallback(&SDNAgent::DataSentCallback, this));
	}

	void SDNAgent::NormalCloseCallback(Ptr<Socket> socket)
	{
		;//socket->Close();
	}


	void SDNAgent::ErrorCloseCallback(Ptr<Socket> socket)
	{
		log_socket(socket, "ERROR");
		
	}


	void SDNAgent::DataSentCallback(Ptr<Socket> socket, uint32_t datsent)
	{
		socket->ShutdownSend();
		 //if(ret!=0)
		 //	cout<<"Socket close - Failed"<<endl;
		 return;
	}

	long int rxCount=0;
	void SDNAgent::rxMessageReceived(Ptr<Socket> socket)
	{
		Ptr<Packet> packet;
		Address from;
		uint8_t *rbuffer;
		rbuffer = (uint8_t *)malloc(4096);
		memset(rbuffer,0,4096);
		string strrbuffer="";

		while ((packet = socket->RecvFrom(from))) // single packet
		{
			if (packet->GetSize() == 0)
			{
				cout << "Packet Size is 0" << endl;
				return; 
			}
			if(packet->GetSize() >= 4096)
				cout<<"Packet Size above 4096"<<endl;
			
			int copiedbytes = packet->CopyData(rbuffer, packet->GetSize());
			strrbuffer = string(reinterpret_cast<char *>(rbuffer),copiedbytes);
			//cout<<"\n\n <<<< Received String  : \n  " <<strrbuffer<<endl;
			if ((int)strrbuffer.length() > copiedbytes)
			{
				cout << "ERROR : Packet size and string length mismatch "<< copiedbytes << "and "<<(int)strrbuffer.length() <<endl;
				strrbuffer.resize(copiedbytes+1);
				strrbuffer = strrbuffer.insert(copiedbytes+1,0x00);
				//cout<<"strbuffer    : "<<strrbuffer<<endl;
			}
			cout<<" <<<< Received Message (#"<<(rxCount++)<<")  "<<endl;
			log_socket(socket, "RX");
			Ptr<Message> rxMsg = CreateObject<Message>(); 
			rxMsg->packet = strrbuffer;
			rxMsg->socket = socket;
			rxQueue.push(rxMsg);
			//cout<<"Pushed to rxQueue "<<"[ size : "<<rxQueue.size()<<" ]"<<endl;
		}
		free(rbuffer);
		return;	
	}


	void SDNAgent::iRxMessageReceived (Ptr<Socket> socket)
	{
		Ptr<Packet> packet;
		Address from;
		uint8_t *rbuffer;
		string strrbuffer;
		rbuffer = (uint8_t *)malloc(4096);
		memset(rbuffer,0,4096);
		while ((packet = socket->RecvFrom (from)))
		{
			if (packet->GetSize () == 0)
			{ 
				cout<<"No Data"<<endl;
				break;
			}

			if (InetSocketAddress::IsMatchingType (from))
			{        
				int copiedbytes = packet->CopyData(rbuffer, packet->GetSize());
				strrbuffer = string(reinterpret_cast<char *>(rbuffer),copiedbytes);
				if((int)strrbuffer.length() > copiedbytes)
				{
						cout << "ERROR iRx: Packet size and string length mismatch "<< copiedbytes << "and "<<(int)strrbuffer.length() <<endl;
						strrbuffer.resize(copiedbytes+1);
						strrbuffer = strrbuffer.insert(copiedbytes+1,0x00);
				}
				//cout<<endl<<"<<<< Received Message"<<endl;
				log_socket(socket, "iRX");

				//cout<<"\n\niRx Message Receive live | DATA : \n"<<strrbuffer<<endl<<endl;

				Ptr<Message> iRxMsg = CreateObject<Message>();
				//cout<<"Created Message from iRx"<<endl;
				
				iRxMsg->isocket = socket;
				iRxMsg->packet = strrbuffer;

				/*if(!(isJsonData(strrbuffer))) //For handling string data, expected is JSON 
				//{
				//	iRxMsg->packet = MESSAGE_REST_FAILURE; 
				//	cout<<"Handling string data as Failure"<<endl;
				//}*/

				//cout<<"\niRx Message Packet Updated | DATA : \n"<<iRxMsg->packet<<endl<<endl;
				//cout << "Updated iRx Message with iSocket and packet content"<<endl;
				iRxQueue.push(iRxMsg);
				//cout<<"Pushed to iRxQueue "<<"[ size : "<<iRxQueue.size()<<" ]"<<endl;				
			}
		}
		free(rbuffer);
		int ret = socket->Close();
		if(ret!=0)
			cout<<"Socket Close - Failed"<<endl;
	}


	void SDNAgent::processQueues(int thread_tsq_params)
	{
		string strdataq;
		Address from;
		Ptr<Socket> socket; 		
		string strstatus;
		while(1)
		{
			if(rxQueue.size()>0)
			{			
				//cout<<endl<<"Processing thread : rxQueue Size : "<<rxQueue.size()<<endl;
				Ptr<Message> rxMsg;		
				rxMsg = rxQueue.blocking_pop();
							
				//validate data type is JSON

				string strpacket;
				Ptr<Message> prevMsg1 = rxMessageMap[rxMsg->socket];
				if(prevMsg1)
				{
					strpacket = (prevMsg1->packet) + (rxMsg->packet);
				}
				else
				{
					strpacket = rxMsg->packet;
				}

				//cout << "\n\nPop Message RX DATA packet: \n"<<strpacket<<endl;
				string strjsondata = getJsonData(strpacket);

				if(isJsonData(strjsondata))
				{
					//messages need immediate responses from the agent
					int cbid = getRestCallbackID(strpacket);
					cout << "\nCall Back Id :" << cbid << endl;
					Log("Process Data", "Call back Id : "+to_string(cbid));

					rxMsg->cbid = cbid;
					json_t* json_response;
					int mq_type = getMessageQueueType(cbid);
					json_response = processCallbackCommands(cbid, strjsondata);
					if(json_response)
					{
						switch (mq_type)
						{
							case MESSAGE_QUEUE_TYPE_NONE:
							case MESSAGE_QUEUE_TYPE_TX:
								rxMsg->packet = json_dumps(json_response,0); 
								txQueue.push(rxMsg);
								cout<<"Command(MQ_TX) - Processed"<<endl;
								break;
							case MESSAGE_QUEUE_TYPE_ITX:
								rxMsg->packet = getJsonData(rxMsg->packet);

								rxMsg->toIp = getMessageQueueIp(cbid);
								rxMsg->toPort = getMessageQueuePort(cbid);
								rxMsg->toUrl = getMessageQueueUrl(cbid);
								iTxQueue.push(rxMsg);
								//cout<<"Command(MQ_ITX) - Processed"<<endl;
								break;
							default:
								//cout<<"Command(MQ_NONE) - TODO"<<endl;
								break;
						}										
						
					}
					else
					{
						cout<<"Waiting for response"<<endl;
						//cout<<"Error message to be issued "<<endl;
					}			

					Ptr<Message> prevMsg = rxMessageMap[rxMsg->socket];
					rxMessageMap.erase(rxMsg->socket);
					cout<<"Erased prevMsg Message"<<endl;
				}
				else
				{
					cout<<"\tMessage Partial, update records "<<endl;
					Ptr<Message> prevMsg = rxMessageMap[rxMsg->socket];
					if(prevMsg)
					{
						prevMsg->packet.append(rxMsg->packet);

					}
					else
					{
					 	rxMessageMap[rxMsg->socket] = rxMsg;
						//cout << "Insert Message into rxMessageMap"<<endl;
					}

				}
    		}

			//iRxQueue processing
			if(iRxQueue.size()>0)
			{
				cout<<endl<<"Processing thread : iRxQueue Size : "<<iRxQueue.size()<<endl;

				Ptr<Message> iRxMsg;
				iRxMsg = iRxQueue.blocking_pop();
				//cout << "Get Message from iRxQueue"<<endl;

				string strpacket;
				Ptr<Message> prevMsg1 = rxMessageMap[iRxMsg->isocket];
				if(prevMsg1)
				{
					strpacket = (prevMsg1->packet) + (iRxMsg->packet);
				}
				else
				{
					strpacket = iRxMsg->packet;
				}

				//cout<<"\n\niRx Packet \n "<<strpacket<<endl;

				string strjsondata = getJsonData(strpacket);
				if(isJsonData(strjsondata))
				{

					//cout<<"\tMessage Complete"<<endl;
					Ptr<Message> prevMsg = iRxMessageMap[iRxMsg->isocket];
					//prevMsg->packet.append(iRxMsg->packet);

					//cout<<"Message Request : "<<prevMsg->cbid<<"  "<<prevMsg->packet<<endl;
					//cout<<"Get Message from iRxMessageMap,   Content : "<<strjsondata<<endl;
					
					if(prevMsg->cbid == CALLBACK_REGISTER_APPLICATION)
					{
						//set saeid_map
						SetSAEIdMap(prevMsg->packet, strjsondata);
					}


					iRxMsg->socket = prevMsg->socket;
					//cout<<"iRsMsg Message updated with prevMsg socket"<<endl;
	
					iRxMsg->packet = strjsondata; 
					txQueue.push(iRxMsg);
					//cout<<"\tPushed to txQueue "<<endl<<endl;
					iRxMessageMap.erase(prevMsg->isocket);
					//cout<<"Removed prevMsg Message from iRxMessageMap"<<endl;
					iRxMsg->isocket->Unref();
				}
				else
				{
					//cout<<"\tMessage partial, update records "<<endl;
					Ptr<Message> prevMsg = iRxMessageMap[iRxMsg->isocket];
					if(prevMsg)
					{
						prevMsg->packet.append(iRxMsg->packet);

					}
					else
					{
						iRxMessageMap[iRxMsg->socket] = iRxMsg;
						//cout << "Insert Message into rxMessageMap"<<endl;
					}
					
				}
    		}

			if(processQ==false)
			{
				break;
			}

  		}
		return;
	}
	
	bool SDNAgent::SetSAEIdMap(string request, string response)
	{
		char *sae_id=NULL, *source_id=NULL, *target_id=NULL;

		//cout<<"Request Msg  : "<<request<<endl;
		//cout<<"Response Msg : "<<response<<endl;

		json_t *json_data = json_object();
		json_error_t error;
		json_data = json_loads(request.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			return false;
		}
		else
		{
			source_id = (char*)json_string_value(json_object_get(json_data, "source_KME_ID"));
			target_id = (char*)json_string_value(json_object_get(json_data, "target_KME_ID"));		
		}


		json_t *json_data_sae = json_object();
		json_error_t error_sae;
		json_data_sae = json_loads(response.c_str(), 0, &error_sae);
		if (!json_data_sae)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			return false;
		}
		else
		{
			sae_id = (char*)json_string_value(json_object_get(json_data_sae, "SAE_ID"));
		
		}

		cout<<"SAE Id : "<<sae_id<<"  Source ID : "<<source_id<<"  Target ID : "<<target_id<<endl;
		if (source_id == NULL || target_id == NULL || sae_id == NULL)
		{
			cout<<"Id is NULL"<<endl;
			return false;
		}

		string str_source_id(source_id), str_target_id(target_id), str_sae_id(sae_id);
		saeid_map[str_sae_id]=make_pair(str_source_id, str_target_id);
		return true;
	}


	void SDNAgent::ScheduleTxDataQueue()
	{
		if(txQueue.size()>0)
		{
			//cout<<"TX SCHEDULE (App Response): Tx Data Queue (Size : "<<txDQ.size()<<")"<<endl;
			Ptr<Message> txMsg = txQueue.blocking_pop();
			Ptr<Socket> sock = txMsg->socket;
			//cout<<"Get socket form txMsg Message"<<endl;
			if(!sock)
			{
				//cout<<"Socket - Not available [ continue as NEW message] "<<endl; //updated for new rest message
				int stat = RestSend(txMsg);
			}
			else
			{
				log_socket(sock, "TX");
				RestSendResponse(sock, txMsg->packet);

			}
			cout<<endl;
		}		
		return;
	}



	void SDNAgent::ScheduleiTxDataQueue()
	{
		if(iTxQueue.size()>0)
		{
			cout<<"TX SCHEDULE: Controller Tx Data Queue (Size : "<<iTxQueue.size()<<")"<<endl;
			Ptr<Message> message = iTxQueue.blocking_pop();
			cout<<"Pop Message from iTxQueue"<<endl;
			cout<<"iTX SCHEDULE:" <<message->iTxCState<<"socket "<< message->socket<<"  Content : " <<message->packet <<endl;
			if(message->iTxCState==0)
			{
				Ptr<Socket> sock = message->socket;
				m_send_socket = Socket::CreateSocket(sock->GetNode(), TcpSocketFactory::GetTypeId());
				m_send_socket->Ref();
				m_send_socket->BindToNetDevice(sock->GetNode()->GetDevice(0));

	
				string serverip = message->toIp; 
				int port = message->toPort; 

				Ipv4Address destinationip(serverip.c_str());
				Address addrr = InetSocketAddress(destinationip, port);

				if(addrr.IsInvalid() )
					cout<<" No Address Available"<<endl;
				else
				{

					int ret = m_send_socket->Connect(addrr);
					if(ret!=0)
						cout<<"Socket connect - Failure"<<endl;

					m_send_socket->SetRecvCallback (MakeCallback (&SDNAgent::iRxMessageReceived, this));
					m_send_socket->SetConnectCallback (MakeCallback (&SDNAgent::ConnectiTxCallbackSuccess, this), MakeCallback(&SDNAgent::ConnectiTxCallbackFailure, this));
					m_send_socket->SetDataSentCallback(MakeCallback(&SDNAgent::iTxDataSentCallback, this));
					message->iTxCState=1;
					
					//cout << "Updated Message iTxCState to 1"<<endl;
					iTxQueue.push(message);
					//cout << "Pushed Message back to iTxQueue"<<endl;
					cout<<"Connected to peer & registered callbacks, socket"<<sock <<" : "<<m_send_socket <<endl;
				}
			}
			else
			{
				iTxQueue.push(message);
				//cout << "Pushed Message back to iTxQueue"<<endl;
				//cout << "Already connected socket "<<message->socket << endl;
			}
		}

		return;
		
	}



	void SDNAgent::ConnectiTxCallbackSuccess(Ptr<Socket> socket)
	{
		//cout<<"Connect Callback ( Queue size : "<<txCDQ.size()<<" )"<<endl;
		if(iTxQueue.size() > 0)
		{
			log_socket(socket, "TX");
			//cout << "Controller connection success "<<endl;

			//cout<<"\nTransmit packet "<<endl;
			Ptr<Message> iTxMsg = iTxQueue.blocking_front();
			//cout << "Get Message from iTxQueue"<<endl;

			string serverip = iTxMsg->toIp; 
			int port = iTxMsg->toPort;  
			Ipv4Address destinationip(serverip.c_str());
			Address addrr = InetSocketAddress(destinationip, port);
			string toUrl = iTxMsg->toUrl;
			//cout<<"URL : "<<toUrl<<endl;
			cout<<"Send packet : " << getJsonData(iTxMsg->packet) <<endl;

			cout<<" Server IP : "<<serverip<<"  Port : "<<port<<endl;
			cout<<" URL : "<<toUrl<<endl;

			string strdata = getJsonData(iTxMsg->packet);

			//for resolving encrypt/plaintext of messages in provision status
			if(strcmp(toUrl.c_str(), KEYPROVISION_STATUS_CONTROLLER_URL_APPEND) == 0)
				RestSend(socket, strdata, addrr, toUrl, false);
			else
				RestSend(socket, strdata, addrr, toUrl, false);

			cout<<" Data : "<<strdata<<endl;
			//update itx socket on map
			iTxMsg->isocket = socket;
			//cout << "Updated Message with iSocket"<<endl;
			iRxMessageMap[iTxMsg->isocket]=iTxMsg;
			//cout<<"Insert Message to iRxMesageMap"<<endl;

			iTxQueue.blocking_pop();
			//cout <<"Pop Message from iTxQueue"<<endl;

		}else{
			socket->Unref();
			socket->Close();
		}

	}

	void SDNAgent::ConnectiTxCallbackFailure(Ptr<Socket> socket)
	{
		//cout<<"Connect Callback - Failed"<<endl;
		socket->Unref();
		int ret = socket->Close();
		if(ret!=0)
			cout<<"Socket close - Failed ( ret : "<<ret<<" )"<<endl;

	}

	void SDNAgent::iTxDataSentCallback(Ptr<Socket> socket, uint32_t dataSent)
	{
		//cout<<"Controller DataSentCallback "<<endl;
		int ret = socket->ShutdownSend();
		if(ret!=0)
			cout<<"Socket shutdown send - Failed"<<endl;
	}



	//using from scheduler function only
	int SDNAgent::RestSend(Ptr<Socket> socket, string data, Address to, string append_url)
	{
		string encoded="";
		encoded =  encoded.append("POST ");
		encoded =  encoded.append(append_url);
		// encoded =  encoded.append(" ");
		encoded =  encoded.append(" HTTP/1.1\r\nContent-Type: application/json\r\nUser-Agent: IE/7.29.2\r\nAccept: */*\r\nHost: 127.0.0.1:7500\r\nAccept-Encoding: gzip, deflate, br\r\nContent-Length: ");


		char *jsonCipherTextEncoded = EncryptAndEncode(data.c_str());
		string data_enc = jsonCipherTextEncoded;

		//encoded =  encoded.append(to_string(data.length()));
		encoded =  encoded.append(to_string(data_enc.length()));
		encoded =  encoded.append("\r\n\r\n");

		//encoded =  encoded.append(data);
		encoded =  encoded.append(data_enc);
		// cout << "Encoded Request: " << encoded << endl;

		Ptr<Packet> restpacket = Create<Packet>(reinterpret_cast<const uint8_t *>(&encoded[0]), encoded.length());
    	int ret = socket->Send(restpacket);
		printf("Ret: %d\n", ret);
		return ret;
	}


	int SDNAgent::RestSend(Ptr<Socket> socket, string data, Address to, string append_url, bool crypto)
	{
		string encoded="";
		encoded =  encoded.append("POST ");
		encoded =  encoded.append(append_url);
		// encoded =  encoded.append(" ");
		encoded =  encoded.append(" HTTP/1.1\r\nContent-Type: application/json\r\nUser-Agent: IE/7.29.2\r\nAccept: */*\r\nHost: 127.0.0.1:7500\r\nAccept-Encoding: gzip, deflate, br\r\nContent-Length: ");
	
		
		char *jsonCipherTextEncoded = EncryptAndEncode(data.c_str());
		string data_enc = jsonCipherTextEncoded;

		if(crypto)
		{
			encoded =  encoded.append(to_string(data_enc.length()));
			encoded =  encoded.append("\r\n\r\n");
			encoded =  encoded.append(data_enc);
		}
		else
		{
			encoded =  encoded.append(to_string(data.length()));
			encoded =  encoded.append("\r\n\r\n");
			encoded =  encoded.append(data);

		}

		// cout << "Encoded Request: " << encoded << endl;
		Ptr<Packet> restpacket = Create<Packet>(reinterpret_cast<const uint8_t *>(&encoded[0]), encoded.length());
    	int ret = socket->Send(restpacket);
		return ret;
	}




	bool SDNAgent::log_socket(Ptr<Socket> socket, string modulename)
	{
		Address localaddr, remoteaddr;
		socket->GetSockName(localaddr);
		socket->GetPeerName(remoteaddr);

		cout<<Simulator::Now().GetMilliSeconds()<<" ms\t|  "<<modulename<< "\t | "<< InetSocketAddress::ConvertFrom(localaddr).GetIpv4()<<" : " <<InetSocketAddress::ConvertFrom(localaddr).GetPort()<<"\t<<==>>\t"<<InetSocketAddress::ConvertFrom(remoteaddr).GetIpv4()<<" : " <<InetSocketAddress::ConvertFrom(remoteaddr).GetPort()<<endl;
		return true;
	}





	json_t* SDNAgent::processCallbackCommands(int cbid, string json_command)
	{
		json_t* json_response = json_object();
		switch (cbid)
		{
			case CALLBACK_NONE:
				json_response = callbackNodeTest(json_command);
				break;
			case CALLBACK_NODEINFO:
				json_response = callbackNodeInfo(json_command);
				break;
			case CALLBACK_NETSQUID:
				json_response = callbackNetSquid(json_command);
				break;
			case CALLBACK_KEYSTORE_STATUS:
				json_response = callbackKeyStoreStatus(json_command);
				break;
			case CALLBACK_KEYSTORE_GETKEY:
				json_response = callbackKeyStoreGetKey(json_command);
				break;
			case CALLBACK_KEYSTORE_GETKEYID:
				json_response = callbackKeyStoreGetKeyId(json_command);
				break;
			case CALLBACK_BB84_SIFTING:
				json_response = callbackBB84Sifting(json_command);
				break;
			case CALLBACK_KEY_NOTIFY:
				json_response = callbackKeyNotify(json_command);
				break;
			case CALLBACK_SDN_COMMAND:
				json_response = callbackSDNCommand(json_command);
				break;
			case CALLBACK_REGISTER_APPLICATION:
				json_response = callbackRegisterApplication(json_command);
				break;
			case CALLBACK_KEY_PROVISION:
				json_response = callbackKeyProvision(json_command);
				break;
			case CALLBACK_KEY_PROVISION_STATUS:
				json_response = callbackKeyProvisionStatus(json_command);
				break;
			case CALLBACK_CONTROLLER_KM:
				json_response = callbackControllerKm(json_command);
				break;
			case CALLBACK_NODE_KEY_STATUS:
				json_response = callbackNodeKeyStatus(json_command);
				break;
			default:
				cout << "\nCall Back - NOT REGISTERED [id: " << cbid << "]" << endl;
				break;
		}
		return json_response;
	}


	int SDNAgent::getMessageQueueType(int cbid)
	{
		int mq_type=0;
		switch (cbid)
		{
		case CALLBACK_NONE:
		case CALLBACK_NODEINFO:
		case CALLBACK_NETSQUID:
		case CALLBACK_KEYSTORE_STATUS:
		case CALLBACK_KEYSTORE_GETKEY:
		case CALLBACK_KEYSTORE_GETKEYID:
		case CALLBACK_BB84_SIFTING:
		case CALLBACK_KEY_NOTIFY:
		case CALLBACK_SDN_COMMAND:
		case CALLBACK_NODE_KEY_STATUS:
		case CALLBACK_CONTROLLER_KM:
			mq_type = MESSAGE_QUEUE_TYPE_TX;
			break;
		
		case CALLBACK_REGISTER_APPLICATION:
		case CALLBACK_KEY_PROVISION:
		case CALLBACK_KEY_PROVISION_STATUS:
		//case CALLBACK_CONTROLLER_KM:
			mq_type = MESSAGE_QUEUE_TYPE_ITX;
			break;
		
		default:
			mq_type = MESSAGE_QUEUE_TYPE_NONE;
			break;
		}

		return mq_type;
	}



	string SDNAgent::getMessageQueueIp(int cbid)
	{
		string ip="";
		switch (cbid)
		{
			case CALLBACK_NONE:
			case CALLBACK_NODEINFO:
			case CALLBACK_NETSQUID:
			case CALLBACK_KEYSTORE_STATUS:
			case CALLBACK_KEYSTORE_GETKEY:
			case CALLBACK_KEYSTORE_GETKEYID:
			case CALLBACK_BB84_SIFTING:
			case CALLBACK_KEY_NOTIFY:
			case CALLBACK_SDN_COMMAND:
			case CALLBACK_NODE_KEY_STATUS:
				//mq_type = MESSAGE_QUEUE_TYPE_TX;
				break;
			
			case CALLBACK_REGISTER_APPLICATION:
			case CALLBACK_KEY_PROVISION:
			case CALLBACK_KEY_PROVISION_STATUS:
			case CALLBACK_CONTROLLER_KM:
				ip = getControllerIP();
				break;
			
			default:
				//ip = MESSAGE_QUEUE_TYPE_NONE;
				break;
		}
		return ip;
	}
	int SDNAgent::getMessageQueuePort(int cbid)
	{
		int port=0;
		switch (cbid)
		{
			case CALLBACK_NONE:
			case CALLBACK_NODEINFO:
			case CALLBACK_NETSQUID:
			case CALLBACK_KEYSTORE_STATUS:
			case CALLBACK_KEYSTORE_GETKEY:
			case CALLBACK_KEYSTORE_GETKEYID:
			case CALLBACK_BB84_SIFTING:
			case CALLBACK_KEY_NOTIFY:
			case CALLBACK_SDN_COMMAND:
			case CALLBACK_NODE_KEY_STATUS:
				//mq_type = MESSAGE_QUEUE_TYPE_TX;
				break;
			
			case CALLBACK_REGISTER_APPLICATION:
			case CALLBACK_KEY_PROVISION:
			case CALLBACK_KEY_PROVISION_STATUS:
			case CALLBACK_CONTROLLER_KM:
				port = getControllerPort();
				break;
			
			default:
				//port = MESSAGE_QUEUE_TYPE_NONE;
				break;
		}
		return port;
	}
	string SDNAgent::getMessageQueueUrl(int cbid)
	{
		string url="";
		switch (cbid)
		{
			case CALLBACK_NONE:
			case CALLBACK_NODEINFO:
			case CALLBACK_NETSQUID:
			case CALLBACK_KEYSTORE_STATUS:
			case CALLBACK_KEYSTORE_GETKEY:
			case CALLBACK_KEYSTORE_GETKEYID:
			case CALLBACK_BB84_SIFTING:
			case CALLBACK_KEY_NOTIFY:
			case CALLBACK_SDN_COMMAND:
			case CALLBACK_NODE_KEY_STATUS:
				//mq_type = MESSAGE_QUEUE_TYPE_TX;
				break;
			
			case CALLBACK_REGISTER_APPLICATION:
				url = KEYMANAGER_CONTROLLER_URL_APPEND;
				break;
			case CALLBACK_KEY_PROVISION:
				url = KEYPROVISION_CONTROLLER_URL_APPEND;
				break;
			case CALLBACK_KEY_PROVISION_STATUS:
				url = KEYPROVISION_STATUS_CONTROLLER_URL_APPEND;
				break;
			case CALLBACK_CONTROLLER_KM:
				url = CONTROLLER_KEYMANAGER_URL_APPEND;
				//ip = getControllerIP();
				break;
			
			default:
				//ip = MESSAGE_QUEUE_TYPE_NONE;
				break;
		}
		return url;
	}

	string SDNAgent::getJsonData(string packetData)
	{
		string jdata;
		// cout<<"Packet Data \n"<<packetData<<endl;

		for (int i = 0; i < (int)packetData.length(); i++)
		{
			if (packetData[i] == '{')
			{
				jdata = packetData.substr(i, ((int)packetData.length()) - i);
				// cout<<packetData[i]<<endl;
				// cout<<jdata<<endl;
				break;
			}
		}
		return jdata;
	}

	bool SDNAgent::isJsonData(string strpacket)
	{
		json_t *json_data = json_object();
		json_error_t error;
		cout<<"Validating JSON Data..."<<endl;
		json_data = json_loads(strpacket.c_str(), 0, &error);
		if (json_data)
		{
			return true;
		}
		cout<<"JSON DATA : Invalid"<<endl;
		return false;
	}


	//int prev_cbid = CALLBACK_NONE;
	int SDNAgent::getRestCallbackID(string packetData)
	{
		int cbid = CALLBACK_NONE;
		string deli = " ";
		int start = 0;
		int end = packetData.find(deli);
		int line = 0;
		string strcbid;

		while (end != -1)
		{

			if (line == 1)
			{
				// cout << packetData.substr(start, end - start) << endl;
				strcbid = packetData.substr(start, end - start);
				// cout<<strcbid<<endl;
			}
			start = end + deli.size();
			end = packetData.find(deli, start);
			line++;
		}
		// cout<<" cbid : "<<strcbid<<endl;

		// cout << packetData.substr(start, end - start);
		if (strcbid == SDN_SERVER_URL_APPEND)
			cbid = CALLBACK_NODEINFO;
		else if (strcbid == SDN_NODEINFO_URL_APPEND)
			cbid = CALLBACK_NODEINFO;
		else if (strcbid == SDN_NETSQUID_URL_APPEND)
			cbid = CALLBACK_NETSQUID;
		else if (strcbid == SDN_KEY_STATUS_URL_APPEND)
			cbid = CALLBACK_KEYSTORE_STATUS;
		else if (strcbid == SDN_GET_KEY_URL_APPEND)
			cbid = CALLBACK_KEYSTORE_GETKEY;
		else if (strcbid == SDN_GET_KEY_ID_URL_APPEND)
			cbid = CALLBACK_KEYSTORE_GETKEYID;
		else if (strcbid == BB84_SIFTING_URL_APPEND)
			cbid = CALLBACK_BB84_SIFTING;
		else if (strcbid == SDN_GET_KEY_NOFIFY_URL_APPEND)
			cbid = CALLBACK_KEY_NOTIFY;
		else if (strcbid == SDN_COMMAND_URL_APPEND)
			cbid = CALLBACK_SDN_COMMAND;
		else if(strcbid == REGISTER_APPLICATION_URL_APPEND)
			cbid= CALLBACK_REGISTER_APPLICATION;
		else if(strcbid == KEY_PROVISION_URL_APPEND)
			cbid= CALLBACK_KEY_PROVISION;
		else if(strcbid == KEY_PROVISION_STATUS_URL_APPEND)
			cbid= CALLBACK_KEY_PROVISION_STATUS;
		else if(strcbid == CONTROLLER_KEYMANAGER_URL_APPEND)
			cbid= CALLBACK_CONTROLLER_KM;
		else if(strcbid == NODE_KEY_STATUS_URL_APPEND)
			cbid= CALLBACK_NODE_KEY_STATUS;
		else
		{
			cbid = CALLBACK_NONE;
		}
		return cbid;
	}




	void SDNAgent::StartApplication()
	{
		Config::SetDefault("ns3::TcpSocket::InitialCwnd", UintegerValue(10));
		Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1460));
		m_recv_socket = Socket::CreateSocket(GetNode(), TcpSocketFactory::GetTypeId()); // working
		m_recv_socket->SetAttribute("SegmentSize", UintegerValue(1460));

		m_recv_socket->SetAcceptCallback(MakeCallback(&SDNAgent::ConnectionRequestCallback, this), MakeCallback(&SDNAgent::NewConnectionCreatedCallback, this));
		InetSocketAddress baddress = InetSocketAddress(Ipv4Address::GetAny(), m_port);
		if (m_recv_socket->Bind(baddress) == -1)
		{
			cout << "Bind socket  - FAILED" << endl;
		}
		//cout << "REST Callback on " << GetNodeId() << "  REGISTERD" << endl<<endl;
		cout <<GetNodeId()<<"  Bind " << Ipv4Address::GetAny() << " Port : " << m_port << "  " << baddress <<"  Callbacks - REGISTERED"<<endl;

		m_recv_socket->Listen();

		PeriodicStatusUpdate();
	}

    void SDNAgent::StopApplication ()
	{
		m_recv_socket->Close();
	}

	

	void SDNAgent::PeriodicStatusUpdate()
	{
		//cout << GetNodeId() << " Periodical updates [ " << Simulator::Now().GetSeconds() << " sec ]\n";
		UpdateNodeStatus(MESSAGE_TYPE_STATUS, GetNodeId(), "UP");
		//Log("STATUS", "Periodical updates");
	}


	int SDNAgent::UpdateNodeStatus(string messagetype, string nodeid, string status)
	{
		// cout<<"NodeUpdate:: Node Id "<<nodeid<<" Status "<<status;
		string strbasepath = getQNEHome() + NODE_CONF_FILE_DIR;
		
		string statusfilepath, commandfilepath, restserverip, idValue = "0";

		if (messagetype == MESSAGE_TYPE_STATUS)
		{
			statusfilepath = strbasepath + "/" + nodeid + "/" + STATUS_FILE_NAME;
			// cout<<"\nStatus file :  "<<statusfilepath<<endl;
		}
		else if (messagetype == MESSAGE_TYPE_COMMAND)
		{
			statusfilepath = strbasepath + "/" + nodeid + "/" + COMMAND_FILE_NAME;
			//cout<<"\nCommand file :  "<<statusfilepath<<endl;
		}
		else
		{
			cout << "Message Type - Unknown" << endl;
		}

		// sources from SDN-AGENT.cc from MAQAN SDN Agent
		char *jsonCipherTextEncoded;

		FILE *fstatus;
		fstatus = fopen(statusfilepath.c_str(), "r");
		if (fstatus == NULL)
		{
			cout<<"STATUS File does not exists"<<endl;
			return 0;
		}

		const size_t line_size = 4096;

		char *payload = (char *)malloc(line_size);
		int fileUpdatedFlag = 0, statusResponse;
		json_error_t error;
		

		while (fgets(payload, line_size, fstatus) != NULL)
		{
			//cout <<endl<<endl<< "Line size : "<<line_size<< " Payload : "<<payload << endl;
			payload[strcspn(payload, "\r\n")] = 0;
			json_t *statusJson = json_loads(payload, 0, &error), *messageId;
			if (!json_is_object(statusJson) || statusJson == NULL)
			{
				cout<<"JSON Load - Failed"<<endl;

				// fprintf(stderr, "error: data is not an object\n");
				json_decref(statusJson);
				continue;
			}
			messageId = json_object_get(statusJson, "MESSAGE_ID");
			if (messageId == NULL || strcmp(json_string_value(messageId), "(null)") == 0 || strcmp(json_string_value(messageId), "\n") == 0)
				continue;
			int intmessageId = atoi(json_string_value(messageId));

			// SDN AGent Port Number
			json_object_set_new(statusJson, "NODE_PORT", json_string(SDN_AGENT_PORT_STRING));

			char *data = (char *)malloc(4096);
			strcpy(data, json_dumps(statusJson, 0));

			if (intmessageId > (this->msgIdStatusSent))
			{
				Log("Node Status", " STATUS_UPDATE ");
				if (json_dumps(statusJson, 0) == NULL)
				{
					printf("\nError\n");
				}
				else
				{

					jsonCipherTextEncoded = EncryptAndEncode(data);

					int sentbyte = SendToQ(getControllerIP(), getControllerPort(), SDN_SERVER_URL_APPEND, statusJson, false);
					if(sentbyte < 0)
						cout<<"Sent Data (SDN Controller - STATUS) - FAILED"<<endl;
					
					
					//cout<<"DATA : "<<json_dumps(statusJson, 0)<<endl<<endl;
					string jstr= json_dumps(statusJson, 0);
					Log("SDN Controller(STATUS)", jstr+"\n");
				}

				if(intmessageId > (this->msgIdStatusSent))
					this->msgIdStatusSent = intmessageId;
			}
			else
			{

				if(intmessageId == (this->msgIdStatusSent))
				{
					//cout<<"Update message - NO UPDATE "<<endl;
					json_object_set_new(statusJson, "STATUS_TYPE", json_string("NO_UPDATE"));
					strcpy(data, json_dumps(statusJson, 0));
				
					jsonCipherTextEncoded = EncryptAndEncode(data);


					int bytes = SendToQ(getControllerIP(), getControllerPort(), SDN_SERVER_URL_APPEND, statusJson, false);
					if(bytes < 0)
						cout<<" Sent data(SDN Controller - NO_UPDATE) - FAILED"<<endl;
					
					string jstr=json_dumps(statusJson, 0);
					Log("SDN Controller(NO UPDATE)", jstr+"\n");
				}
				//return 0;
			}
			json_decref(statusJson);
			free(data);
		}
		fclose(fstatus);
		return 0;
	}




   	int SDNAgent::SendToQ(char *ip, int port, string url, json_t *json_data, bool crypto)
	{
		Ptr<Message> Msg = CreateObject<Message>();			
		Msg->packet = json_dumps(json_data,0); 
		Msg->toIp = ip;
		Msg->toPort = port;
		Msg->toUrl = url;
		Msg->crypto = crypto;
		txQueue.push(Msg);
		//cout<<"Data Pushed to Tx Q "<<endl;
		return 0;
	}

	int SDNAgent::RestSend(Ptr<Message> Msg)
	{
		if(Msg->toIp == "")
			return -1;
		char request_header[1000] = {" HTTP/1.1\r\nContent-Type: application/json\r\nUser-Agent: IE/7.29.2\r\nAccept: */*\r\nHost: 127.0.0.1:7500\r\nAccept-Encoding: gzip, deflate, br\r\nContent-Length: "};
		char encoded[4096];
		strcpy(encoded, "POST ");
		strcat(encoded, Msg->toUrl.c_str());
		// strcat(encoded, " ");
		strcat(encoded, request_header);

		char *strlength = (char *)malloc(12);
		strcpy(strlength, "");

		const char *data = (char *)malloc(4096);
		data = Msg->packet.c_str();
		if(Msg->crypto == true)
		{
			char *jsonCipherTextEncoded;
			//data = Msg->packet.c_str();
			jsonCipherTextEncoded = EncryptAndEncode(data);
			data = jsonCipherTextEncoded;
		}

		sprintf(strlength, "%d", (int)strlen(data));

		strcat(encoded, strlength);
		strcat(encoded, "\r\n\r\n");
		strcat(encoded, data);

		Ipv4Address destinationip(Msg->toIp.c_str());
		Ptr<Packet> restpacket = Create<Packet>(reinterpret_cast<const uint8_t *>(encoded), strlen(encoded));

		// cout << "Encoded Request: " << encoded << endl;
		int bytes = SendPacket(restpacket, destinationip, Msg->toPort);
		return bytes;	
	}


	int SDNAgent::SendPacket(Ptr<Packet> packet, Ipv4Address destination, uint16_t port)
	{
		m_send_socket = Socket::CreateSocket(GetNode(), TcpSocketFactory::GetTypeId()); // working
		m_send_socket->Connect(InetSocketAddress(Ipv4Address::ConvertFrom(destination), port));
		bool stat;
		char *ipaddr = new char(32);
		int ipa = destination.Get();
		string strip = to_string(ipa >> 24) + "." + to_string((ipa >> 16) & 0xff) + "." + to_string((ipa >> 8) & 0xff) + "." + to_string(ipa & 0xff);
		strcpy(ipaddr,strip.c_str());

		int bytes = m_send_socket->Send(packet);
		if (bytes == -1)
		{
			stat = false;
			cout << endl << "SENT Bytes : FAILED " << endl;
			Log("Send Packet ", ipaddr, port, stat, bytes);

		}
		else
		{
			stat=true;
			Log("Send Packet ",ipaddr, port, stat, bytes);
		}
		
		// m_send_socket->ShutdownSend();
		// m_send_socket->Close();
		return bytes;
	}


	int SDNAgent::RestSendResponse(Ptr<Socket> socketresponse, string data)
	{
		char encoded[1600]="";
    	char response_header[1024] = "HTTP/1.1 200\r\nContent-Type: application/json\r\nContent-Length: ";
		if(data=="")
			data = "{\"STATUS\":\"Unknwon\"}";
    	strcpy(encoded, response_header);

		char *strlength = (char *)malloc(12);
		strcpy(strlength, "");
		sprintf(strlength, "%d", (int)strlen(data.c_str()));
		strcat(encoded, strlength);
		strcat(encoded, "\r\n\r\n");
		strcat(encoded, data.c_str());
		Ptr<Packet> restpacket = Create<Packet>(reinterpret_cast<const uint8_t *>(encoded), strlen(encoded));
    	int ret = socketresponse->Send(restpacket);

		// cout << "Encoded Request: " << encoded << endl;
		if(ret == -1) 
			Log("Response Sent - FAILED", data);
		else
			Log("Response Sent - SUCCESS", data);
		return ret;
	}

	bool SDNAgent::SetNodeId(string node_id)
	{
		this->nodeid = node_id;
		return true;
	}

	string SDNAgent::GetNodeId()
	{
		return (this->nodeid);
	}

	bool SDNAgent::SetNodeName(string nodename)
	{
		this->nodename = nodename;
		return true;
	}

	string SDNAgent::GetNodeName()
	{
		return (this->nodename);
	}

    json_t* SDNAgent::callbackNodeTest(string jsondata)
	{
		json_t *json_body = json_object();
		json_object_set_new(json_body, "Status", json_string("Running"));
		json_object_set_new(json_body, "Node Name", json_string(GetNodeName().c_str()));
		return json_body;
	}

	json_t* SDNAgent::callbackNodeInfo(string jsondata)
	{
		json_t *json_body = json_object();
		json_error_t error;

		json_body = json_loads(jsondata.c_str(), 0, &error);
		if (!json_body)
			printf(" Failed loading string to json object\n");
		string nodeid = "";
		json_t *id;
		id = json_object_get(json_body, "NODE_ID");
		if (id)
		{
			nodeid = json_string_value(id);
			//cout << "Node Id : " << nodeid << endl;
		}

		return json_body;

	}



	string SDNAgent::getSDNAgentIP(string nodeid)
	{
		int UIntIP = GetNode()->GetObject<Ipv4>()->GetAddress(1, 0).GetLocal().Get();
		string strip = to_string(UIntIP >> 24) + "." + to_string((UIntIP >> 16) & 0xff) + "." + to_string((UIntIP >> 8) & 0xff) + "." + to_string(UIntIP & 0xff);

		return (strip);
	}

	

	string SDNAgent::doSifting(string bits, string basis, string source, string destination)
	{
		// cout<<"Swifting "<< endl;
		string siftedkey;
		string sdnagentip = getSDNAgentIPFromController(destination);

		json_t *json_body = json_object();
		json_object_set_new(json_body, "bits", json_string(bits.c_str()));
		json_object_set_new(json_body, "basis", json_string(basis.c_str()));
		json_object_set_new(json_body, "source", json_string(source.c_str()));
		json_object_set_new(json_body, "destination", json_string(destination.c_str()));

		string data = json_dumps(json_body, 0);
		if (sdnagentip != "")
		{
			int stat = SendToQ((char*)sdnagentip.c_str(), SDN_AGENT_PORT, BB84_SIFTING_URL_APPEND, json_body, false);

			//cout << endl
			//	 << ">>> SENT Basis and Bits for Sifting [ " << sdnagentip << " : " << SDN_AGENT_PORT << " ]" << endl;
			Log("doSifting", "SENT Basis and Bits");
		}
		else
			cout << "Sifting procedure - Failed(send basis)" << endl;

		// TODO Get matchlist as response
		string matchlist = getMatchList(bits, basis, source, destination);
		// TODO Compare with matchlist and generate key
		siftedkey = getSiftedKey(bits, basis, source, destination, matchlist);
		return siftedkey;
	}

	string SDNAgent::getMatchList(string bits, string basis, string source, string destination)
	{
		// get current basis and compare with received basis
		string matchlist = "";
		if ((this->basis).length() != basis.length())
			return "";
		for (int i = 0; i < basis.length(); i++)
		{
			if (basis[i] == (this->basis[i]))
			{

				if (matchlist.length() > 0)
					matchlist.append(1, ',');
				matchlist.append(to_string(i));
			}
		}
		// cout<<"Match List : "<<matchlist<<endl;
		return matchlist;
	}

	string SDNAgent::getSiftedKey(string bits, string basis, string source, string destination, string matchlist)
	{
		//cout << "Get Sifted Key " << endl;
		string skey = "";
		stringstream ssml(matchlist);
		vector<string> mltokens;
		string strtemp;
		while (getline(ssml, strtemp, ','))
		{
			mltokens.push_back(strtemp);
		}
		for (int i = 0; i < mltokens.size(); i++)
		{
			skey.append(1, bits[stoi(mltokens[i])]);
		}
		// cout<<" key "<<skey<<endl;
		return skey;
	}

	json_t *SDNAgent::ComposeSDNControllerCommandResponse(int messageid, char *commandid, const char *status)
	{
		json_t *json_response_body = json_object();
		json_t *json_status[1];
		json_t *json_arrays = json_array();
		json_status[0] = json_object();

		json_object_set_new(json_response_body, "MESSAGE_ID", json_string(to_string((messageid)).c_str()));
		json_object_set_new(json_response_body, "MESSAGE_TYPE", json_string("RESPONSE"));
		json_object_set_new(json_response_body, "NODE_ID", json_string(GetNodeId().c_str()));

		json_object_set_new(json_response_body, "COMMAND", json_string("QUANTUM_CHANNEL_START"));
		json_object_set_new(json_response_body, "COMMAND_ID", json_string(commandid));

		json_object_set_new(json_response_body, "TIMESTAMP", json_string(getCurrentDateTime()));

		json_object_set_new(json_status[0], "STATUS", json_string(status));
		json_array_append_new(json_arrays, json_status[0]);
		json_object_set_new(json_response_body, "RESPONSE_PARAMS", json_arrays);

		return json_response_body;
	}

bool SDNAgent::isChannelId(json_t *path, char *currChannelId)
{
	bool is_channel=false;
	//cout<<endl<<endl<<" Current Path : "<<currChannelId<<"  All Path  : "<<json_dumps(path,0)<<endl;

 	if (!json_is_array(path)) 
	{
        cout<<"JSON data Path - Not Available"<<endl;
        is_channel = false;
    }

	size_t path_count = json_array_size(path);
	//cout<<"Paths  : "<<path_count<<endl;
	
    for (size_t i = 0; i < path_count; i++) 
	{
        json_t* item = json_array_get(path, i);


		if(!item)
			continue;

        const char* value = json_string_value(item);
		if(strcmp(currChannelId, value) == 0)
		{
			is_channel = true;
			break;
		}
        //}
    }
	cout<<" Path available : "<<(is_channel?" Yes ": " No ")<<endl<<endl;
	return is_channel;
}

json_t *SDNAgent::ComposeSDNControllerStatusUpdate(int messageId, const char *nodeid, const char *ip, bool link_status, float qber, float keyrate, string keygen_status, json_t *path)
{
	json_t *json_body = json_object();
	json_t *json_link[3];
	json_t *json_arrays = json_array();
	json_t *json_clink[3];
	json_t *json_carrays = json_array();

	json_object_set_new(json_body, "MESSAGE_ID", json_string(to_string(messageId).c_str()));
	json_object_set_new(json_body, "NODE_ID", json_string(nodeid));
	json_object_set_new(json_body, "NODE_NAME", json_string(GetNodeName().c_str()));
	json_object_set_new(json_body, "STATUS_TYPE", json_string("STATUS_UPDATE"));
	json_object_set_new(json_body, "NODE_IP", json_string(ip)); 
	json_object_set_new(json_body, "NODE_PORT", json_integer(SDN_AGENT_PORT));
	json_object_set_new(json_body, "KM_IP", json_string(ip)); 
	json_object_set_new(json_body, "KM_PORT", json_integer(SDN_AGENT_PORT));


	//json_object_set_new(json_body, "TIMESTAMP", json_string(datetime_string));  
	json_object_set_new(json_body, "TIMESTAMP", json_string(getCurrentDateTime()));
	  
	int qc_channels = getQuantumChannels(nodeid);
	for (int i =0; i < qc_channels; i++)
	{
		json_link[i] = json_object();
		json_object_set_new(json_link[i], "QC_ID", json_string(getChannelParams(nodeid,(i+1),PARAM_LINK_ID)));

		//find exact link names
		json_object_set_new(json_link[i], "LINK_ID_QUANTUM", json_string(getChannelParams(nodeid,(i+1), PARAM_LINK_NAME)));
		//json_object_set_new(json_link[i], "QC_NAME", json_string(getChannelParams(nodeid,(i+1), PARAM_LINK_NAME)));
		bool linkup = true;
		//cout<<"Link status : "<<linkup<<endl;
		if(linkup == true)
		{
			json_object_set_new(json_link[i], "LINK_STATUS_QUANTUM", linkup ? json_string("UP") : json_string("DOWN"));
			//json_object_set_new(json_link[i], "QC_STATUS", linkup ? json_string("UP") : json_string("DOWN"));
			
			char *currChannelId = getChannelParams(nodeid,(i+1),PARAM_LINK_ID);		
			if(isChannelId(path, currChannelId))
			{
				json_object_set_new(json_link[i], "QBER", json_string(to_string(qber).c_str()));
				json_object_set_new(json_link[i], "KEY_GEN_STATUS", json_string(keygen_status.c_str()));
				json_object_set_new(json_link[i], "KEY_RATE", json_string(to_string(keyrate).c_str()));
			}
			else
			{
				json_object_set_new(json_link[i], "LINK_STATUS_QUANTUM", json_string("DOWN"));
				json_object_set_new(json_link[i], "QBER", json_string("-1"));
				json_object_set_new(json_link[i], "KEY_GEN_STATUS", json_string("Idle"));
				json_object_set_new(json_link[i], "KEY_RATE", json_string("-1"));

			}
		}
		else
		{
			//json_object_set_new(json_link[i], "QC_STATUS", json_string("DOWN"));
			json_object_set_new(json_link[i], "LINK_STATUS_QUANTUM", json_string("DOWN"));
			json_object_set_new(json_link[i], "QBER", json_string("-1"));
			json_object_set_new(json_link[i], "KEY_GEN_STATUS", json_string("Idle"));
			json_object_set_new(json_link[i], "KEY_RATE", json_string("-1"));

		}
		json_array_append_new(json_arrays, json_link[i]);
	}
	json_object_set_new(json_body, "QUANTUM_CHANNEL", json_arrays);   

	int cc_channels = 1;
	for (int i =0; i < cc_channels; i++)
	{
		json_clink[i] = json_object();


		json_object_set_new(json_clink[i], "CC_ID", json_string(to_string(i+1).c_str()));
		json_object_set_new(json_clink[i], "LINK_ID_QUANTUM", json_string("tap0"));
		json_object_set_new(json_clink[i], "LINK_STATUS_QUANTUM", json_string("UP"));
		json_array_append_new(json_carrays, json_clink[i]);
	}
	json_object_set_new(json_body, "CLASSICAL_CHANNEL", json_carrays); 

	return json_body; 
}

bool SDNAgent::getLinkStatus(const char *nodeid, int qchannelid, char *qcid, json_t *paths)
{
	int pathnum = json_array_size(paths);
	json_t *link;
	char *linkid = NULL;
	for(int i=0; i<pathnum; i++)
	{
		linkid = (char *)json_string_value(json_array_get(paths, (size_t)i));
		
		if(strcmp(qcid,linkid)==0)
		{
			//cout<<"Link is Active"<<endl;
			return true;
		}

	}
	return false;
}




bool SDNAgent::postStatusUpdate(bool link_status, string keygen_status, float qber, float keyrate, json_t *path)
{
	json_t *json_stat = ComposeSDNControllerStatusUpdate(++(this->msgIdStatusSent), GetNodeId().c_str(), getSDNAgentIP(GetNodeId()).c_str(), link_status, qber, keyrate, keygen_status, path);
	string str_json_status = json_dumps(json_stat, 0);
	postStatusFileUpdate(str_json_status);

	char *datacmd = (char *)malloc(4096);
	char *jsonCipherTextEncoded;
	strcpy(datacmd, json_dumps(json_stat, 0));		
	jsonCipherTextEncoded = EncryptAndEncode(datacmd);

	int stat = SendToQ(getControllerIP(), getControllerPort(), SDN_SERVER_URL_APPEND, json_stat, false);
	Log("Data (STATUS)", str_json_status);
	return true;
}


string SDNAgent::getSDNAgentIPFromController(string nodeid)
{
    // TODO get the SDN Agent IP from controller for key notification

    string strnwbase = getNetworkBase();
    //strnwbase.erase(strnwbase.end() - 1, strnwbase.end());
 
    return "";
}

	json_t* SDNAgent::postCommandResponse(char *messageid, char* command, char* commandid, char *status)
	{

		json_t *json_response_body = json_object();
		json_t *json_status[1];
		json_t *json_arrays = json_array();
		json_status[0] = json_object();

		int msgid = atoi(messageid);
		json_object_set_new(json_response_body, "MESSAGE_ID", json_string(to_string((msgid+1)).c_str()));

		json_object_set_new(json_response_body, "MESSAGE_TYPE", json_string("RESPONSE"));
		json_object_set_new(json_response_body, "NODE_ID", json_string(GetNodeId().c_str()));

		json_object_set_new(json_response_body, "COMMAND", json_string(command));
		json_object_set_new(json_response_body, "COMMAND_ID", json_string(commandid));

		json_object_set_new(json_response_body, "TIMESTAMP", json_string(getCurrentDateTime()));

		json_object_set_new(json_status[0], "STATUS", json_string(status));
		json_array_append_new(json_arrays, json_status[0]);
		json_object_set_new(json_response_body, "RESPONSE_PARAMS", json_arrays);

		return json_response_body;

	}

	static int inc = 0;
	static int key_size = 0;

	

	json_t* SDNAgent::callbackNetSquid(string jsondata)
	{
		//cout << "<<< Receive : Quantum Bits from NetSquid" << endl;
		Log("<<< Receive :", "Response Message from NetSquid");
		Log("Data : ", jsondata);


		json_t *json_body = json_object();
		json_t *json_ns_data = json_object();
		json_t *json_controller_data = json_object();
		json_error_t error;

		json_t *json_response = json_object();

		json_t *json_status[2];
		json_t *json_arrays = json_array();
		json_status[0] = json_object();
		json_status[1] = json_object();

		json_ns_data = json_loads(jsondata.c_str(), 0, &error);

		if (!json_ns_data)
		{
			printf(" Failed loading string to json object\n");
			json_object_set_new(json_body, "STATUS", json_string("Invalid Data Format"));
			return json_body;
		}

		//filter message type - Link provision/start/stop
	
		char *cmdtype = NULL;
		char *messageid=NULL, *command=NULL, * commandid=NULL, *response=NULL;

		json_t *cmd;
		cmd = json_object_get(json_ns_data, "Type");
		if(cmd)
		{
			json_t *provison_path = json_object_get(json_ns_data, "all_links");

			cmdtype = (char *)json_string_value(cmd);
			messageid = (char *)json_string_value(json_object_get(json_ns_data, "message_id"));
			command = (char *)json_string_value(json_object_get(json_ns_data, "command"));
			commandid = (char *)json_string_value(json_object_get(json_ns_data, "command_id"));
			response = (char *)json_string_value(json_object_get(json_ns_data, "response"));
			if(strcmp(cmdtype,"command") == 0)
			{
				//save to file and send to controller
				Log("Callback NetSquid", " Type - command");
				json_object_set_new(json_body, "STATUS", json_string("Success"));
				//TODO return json_body;


				postCommandUpdate(messageid, command, commandid, response);

				if (json_is_array(provison_path)) 
				{
					Log("Path ", json_dumps(provison_path,0));
					postStatusUpdate(true," ",0,0,provison_path);
				}
				return json_body;
			}
			json_object_set_new(json_body, "STATUS", json_string("Failure"));
			return json_body; 
		}
		
		

		char *source = NULL, *destination = NULL, *basis = NULL, *bits = NULL, *key = NULL;
		char *srcip = NULL, *destip = NULL;
		source = (char *)json_string_value(json_object_get(json_ns_data, "source"));
		destination = (char *)json_string_value(json_object_get(json_ns_data, "destination"));
		basis = (char *)json_string_value(json_object_get(json_ns_data, "basis"));
		bits = (char *)json_string_value(json_object_get(json_ns_data, "bits"));
		key = (char *)json_string_value(json_object_get(json_ns_data, "key"));

		string strbasis = basis;
		this->basis = strbasis;
	
		float qber = stof(json_string_value(json_object_get(json_ns_data, "qber")));
		//cout<<"QBER : " <<json_string_value(json_object_get(json_ns_data, "qber"))<<endl;
		inc++;
		key_size += strlen(key);
	

		json_t *path = json_object_get(json_ns_data, "all_link");
    	if (!json_is_array(path)) 
		{
        	//printf("JSON Data Posted - Status : FAIL (Node info)\n");
			Log("Path ", " Not Available");
        	//return U_CALLBACK_CONTINUE;
    	}
		else
		{
			Log("Path ", json_dumps(path,0));
		}


		postStatusUpdate(true, "Quantum Transmission", 0, 0, path);

		int sid = GetStoreId(0, source, destination, STORE_ID_GET_CREATE);
		if (sid == KEY_STORE_NOT_AVAILABLE)
		{
			//cout << "Key Store - Not Available" << endl;
			Log("Key Store ", "Not Available");
			json_object_set_new(json_body, "STATUS", json_string("No KeyStore"));
			return json_body;
		}

		store[sid].SetSourceID(source);
		store[sid].SetTargetID(destination);

		json_controller_data = ComposeSDNControllerCommandResponse(++(this->msgIdCommandSent), g_command_id, "Quantum Transmission");
		string data = json_dumps(json_controller_data, 0);
		postCommandFileUpdate(data);

		char *jsonCipherTextEncoded;
		jsonCipherTextEncoded = EncryptAndEncode(json_controller_data);

		int stat = SendToQ(getControllerIP(), getControllerPort(), SDN_COMMAND_RESPONSE_URL_APPEND, json_controller_data, false);

		Log("", "SENT Data To SDN Controller");
		Log("Data", data);

		///////////TODO Enable Post processing
		
				PostProMessage MsgPostPro;
				MsgPostPro.id = 1;
				MsgPostPro.node_type = 0;
				MsgPostPro.bits = bits;
				MsgPostPro.basis = basis;
				MsgPostPro.source = store[sid].GetSourceID();
				MsgPostPro.destination = store[sid].GetTargetID();
				MsgPostPro.key = key;

				string str_key_pp = PostProcess(MsgPostPro); // TODO update    NOT used key now
				if (str_key_pp == "")
				{
					cout << "No Key " << endl;
					json_object_set_new(json_body, "STATUS", json_string("No Key"));
					return json_body;
				}
			
		/////////////////
		
		Log("Sifting", "Sifting Started");
		//cout << "Sifting : [ " << store[sid].GetSourceID()<<" <---> " << store[sid].GetTargetID() << " ]"<< endl;
		Log("Sifting", store[sid].GetSourceID()+" <---> " + store[sid].GetTargetID());
		string siftedKey = doSifting(bits, basis, store[sid].GetSourceID(), store[sid].GetTargetID());

		// REST Send to SDN controller - Swifting
		json_t *status_sf = ComposeSDNControllerCommandResponse(++(this->msgIdCommandSent), g_command_id, "Sifting");
		string str_status_sf = json_dumps(status_sf, 0);
		postCommandFileUpdate(str_status_sf);

		// REST Send to SDN controller - Error Correction
		json_t *status_ec = ComposeSDNControllerCommandResponse(++(this->msgIdCommandSent), g_command_id, "Error Correction");
		string str_status_ec = json_dumps(status_ec, 0);
		postCommandFileUpdate(str_status_ec);

		cout << endl
			 << " Sifted Key (NetSquid) : " << key << endl;


		postStatusUpdate(true, "Sifting", 0, 0, path);

		int status;
		//if (key == siftedKey)
		//if (key == str_key_pp)
		if (str_key_pp != "")
		{
			//status = store[sid].StoreKey(siftedKey); // TODO ensure both keys are same
			status = store[sid].StoreKey(str_key_pp);
			Log(" STORE KEY(Post Pro)", "SUCCESS");
		}
		else
		{
			if(qber == 0.0)
			{
				status = store[sid].StoreKey(key); // fallback mechanism, if NS3 postprocessing fails
				//cout << " STORE KEY - SUCCESS (Netsquid sifted key as NS3 sifting keys not matching ) qber "<<qber<< endl;
				Log(" STORE KEY", "SUCCESS (Netsquid sifted key as NS3 sifting keys not matching ) qber ");
			}
			else
			{
				cout<<" STORE KEY - FAILURE (Qber is "<<qber<<" ) "<<endl;
				Log(" STORE KEY", "FAILURE (Qber is not Zero)");
			}
		}


		json_t *json_stoplink = json_object();
		if (status == KEY_STORE_FULL)
		{
			json_object_set_new(json_stoplink, "NODE_ID", json_string(GetNodeId().c_str()));
			json_object_set_new(json_stoplink, "COMMAND", json_string("QUANTUM_CHANNEL_STOP"));
			json_object_set_new(json_stoplink, "TRANSMITTER", json_string(source));
			json_object_set_new(json_stoplink, "RECEIVER", json_string(destination));

			// STOP Qunatum transmission request //TODO clarify in SDN conroller mode
			int stat = SendToQ(getNetSquidIP(), getNetSquidPort(), NETSQUID_LINK_STOP_URL_APPEND, json_stoplink, false);

			cout << ">>>> STOP Link, Data : "
				 << " QQC_SERVER : " << getNetSquidIP() << " Port : " << getNetSquidPort() << endl;
			Log(">>>> STOP Link","Requested");
			if(stat<=0)
				json_object_set_new(json_body, "status", json_string("fail"));
			else
				json_object_set_new(json_body, "status", json_string("success"));
		}
		else if (status == KEY_STORE_READY)
		{
			json_object_set_new(json_body, "status", json_string("success"));
		}
		else
		{
			json_object_set_new(json_body, "status", json_string("unknown"));
		}

		// REST Send to SDN controller
		json_t *status_pa = ComposeSDNControllerCommandResponse(++(this->msgIdCommandSent), g_command_id, "Privacy Amplification");
		string str_status_pa = json_dumps(status_pa, 0);
		postCommandFileUpdate(str_status_pa);

		postStatusUpdate(true, "Error Correction", 0, 0, path);
		postStatusUpdate(true, "Privacy Amplification", 0, 0, path);

		postCommandUpdate(g_command_id, (char *)"Key Generated");
		postStatusUpdate(true, "Key Generated", qber, (float)(key_size / inc), path);
		postStatusUpdate(true, " ", int(-1), int(-1), path);
		postCommandUpdate(g_command_id, (char *)"EXECUTED\n");
		
		// postStatusUpdate(true, "", qber, (-1), path);
		// postCommandUpdate(g_command_id, (char *)"");



		return json_body;

	
		json_decref(json_ns_data);
		json_decref(json_body);
		return json_body;
	}

	bool SDNAgent::postCommandUpdate(char *commandid, char *status)
	{
		json_t *status_qt = ComposeSDNControllerCommandResponse(++(this->msgIdCommandSent), commandid, status);
		string str_status_qt = json_dumps(status_qt, 0);
		postCommandFileUpdate(str_status_qt);

		char *jsonCipherTextEncoded;
		jsonCipherTextEncoded = EncryptAndEncode(status_qt);

		int stat = SendToQ(getControllerIP(), getControllerPort(), SDN_COMMAND_RESPONSE_URL_APPEND, status_qt, false);

		Log("Data (COMMAND): ", "SENT Data To SDN Controller");
		//cout << "Data (COMMAND): " << str_status_qt << endl;
		Log("Data (COMMAND): ", str_status_qt);

		return true;
	}


	bool SDNAgent::postCommandUpdate(char *messageid, char *command, char *commandid, char *response)
	{
		json_t *status_qt = postCommandResponse(messageid, command, commandid, response);

		string str_status_qt = json_dumps(status_qt, 0);
		postCommandFileUpdate(str_status_qt);

		char *jsonCipherTextEncoded;
		jsonCipherTextEncoded = EncryptAndEncode(status_qt);
		
		int stat = SendToQ(getControllerIP(), getControllerPort(), SDN_COMMAND_RESPONSE_URL_APPEND, status_qt, false);
		Log("Data (COMMAND): ", "SENT Data To SDN Controller");
		Log("Data (COMMAND): ", str_status_qt);

		return true;
	}





	json_t* SDNAgent::callbackKeyStoreStatus(string jsondata)
	{
		//cout << "<<< Receive : Key Store Status" << endl;
		Log("<<< Receive : Key Store Status", " Request - RECEIVED");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_error_t error;
		char *sourceid = NULL, *targetid = NULL, *saeid = NULL, *keytype=NULL;
		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			printf(" Failed loading string to json object\n");
			json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
			return json_body;
		}
		else
		{
			sourceid = (char *)json_string_value(json_object_get(json_data, "source_KME_ID"));
			targetid = (char *)json_string_value(json_object_get(json_data, "target_KME_ID"));
			saeid = (char *)json_string_value(json_object_get(json_data, "master_SAE_ID"));
			keytype = (char *)json_string_value(json_object_get(json_data, "type"));
			if (sourceid == NULL || targetid == NULL)
			{
				printf(" Source ID & Target ID - Not Valid\n");
				json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
				return json_body;
			}
			if(keytype == NULL)
			{
				printf(" Key Type - No\n");
				json_object_set_new(json_body, "message", json_string("Key Type - No"));
				return json_body;
			}
			else
			{
				if (strcmp(keytype,(char *)KEY_TYPE_QUANTUM) != 0)
				{
					printf(" Key Store - Not Available\n");
					json_object_set_new(json_body, "message", json_string("Key Store - Not Available"));
					return json_body;
				}
			}

			int sid = GetStoreId(0, sourceid, targetid);
			if (sid == KEY_STORE_NOT_AVAILABLE)
			{
				cout << "Key Store - Not Available" << endl;
				json_object_set_new(json_body, "message", json_string("Key Store - Not Available "));
				return json_body;
			}
			else
			{
				json_object_set_new(json_body, "source_KME_ID", json_string(store[sid].GetSourceID().c_str()));
				json_object_set_new(json_body, "target_KME_ID", json_string(store[sid].GetTargetID().c_str()));
				json_object_set_new(json_body, "type", json_string("Quantum"));

				json_object_set_new(json_body, "master_SAE_ID", json_string("NA"));
				json_object_set_new(json_body, "slave_SAE_ID", json_string("NA"));

				json_object_set_new(json_body, "key_size", json_integer(store[sid].GetKeyStoreSize()));		// bytes //35
				json_object_set_new(json_body, "stored_key_count", json_integer(store[sid].GetKeyCount())); // 25000
				json_object_set_new(json_body, "max_key_count", json_integer(MAX_KEY_IDS));					// 100000
				json_object_set_new(json_body, "max_key_per_request", json_integer(1));						// 128

				json_object_set_new(json_body, "max_key_size", json_integer(1024));
				json_object_set_new(json_body, "min_key_size", json_integer(64));
				json_object_set_new(json_body, "max_SAE_ID_count", json_integer(0));
				json_object_set_new(json_body, "max_key_store_size", json_integer(MAX_KEY_STORAGE));

				cout << "Source Id :" << store[sid].GetSourceID() << "  KeyStore size :" << store[sid].GetKeyStoreSize() << endl;
				return json_body;

			}
		}
		json_decref(json_data);
		json_decref(json_body);
		return json_body;
	}




json_t* SDNAgent::callbackKeyStoreGetKey(string jsondata)
	{
		//cout << "<<< Receive : Key Store GetKey" << endl;
		Log("<<< Receive : Key Store GetKey", "Request - RECEIVED");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_error_t error;

		char *sourceid = NULL, *targetid = NULL, *saeid = NULL;

		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
			return json_body;
		}
		else
		{
			sourceid = (char *)json_string_value(json_object_get(json_data, "source_KME_ID"));
			targetid = (char *)json_string_value(json_object_get(json_data, "target_KME_ID"));
			saeid = (char *)json_string_value(json_object_get(json_data, "master_SAE_ID"));
			if (sourceid == NULL || targetid == NULL)
			{
				json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
				cout << "JSON Data Posted - Status : Source ID & Target ID - Not Valid" << endl;
				return json_body;
			}

			int sid = GetStoreId(0, sourceid, targetid);
			if (sid == KEY_STORE_NOT_AVAILABLE)
			{
				cout << "Key Store - Not Available" << endl;
				json_object_set_new(json_body, "message", json_string("Key Store - Not Available "));
				return json_body;
			}
			else
			{
				int keynumber = json_integer_value(json_object_get(json_data, "number"));
				int keysize = json_integer_value(json_object_get(json_data, "size"));
				cout << "Number : " << keynumber << " Size : " << keysize << endl;
				if (keynumber != 1)
				{
					json_object_set_new(json_body, "message", json_string("key number not supported"));
					cout << "JSON Data Posted - Status : Failed(key number not supported)" << endl;
					return json_body;
				}
				if ((keysize < 64) || (keysize > 1024) || ((keysize % 8) != 0))
				{
					json_object_set_new(json_body, "message", json_string("key size not supported"));
					cout << "JSON Data Posted - Status : Failed (invalid key size)" << endl;
					return json_body;
				}

				json_t *json_key[2];
				json_t *json_arrays = json_array();
				json_key[0] = json_object();
				json_key[1] = json_object();

				string keyid = store[sid].GetKey(keysize);
				string keyvalue = store[sid].GetKey(keyid);
				if (keyid == "" || keyvalue == "")
				{
					json_object_set_new(json_body, "message", json_string(" key not available "));
					cout << "JSON Data Posted - Status : Failed (no key available)" << endl;
					return json_body;
				}

				json_object_set_new(json_key[0], "key_ID", json_string(keyid.c_str()));
				cout << endl
					 << endl
					 << "Key Id : " << keyid.c_str() << endl;
				cout << endl
					 << "Key Value : " << keyvalue.c_str() << endl;
				json_object_set_new(json_key[0], "key", json_string(keyvalue.c_str()));
				json_array_append_new(json_arrays, json_key[0]);
				json_object_set_new(json_body, "keys", json_arrays);

				string sdnagentip = getSDNAgentIPFromController(store[sid].GetTargetID());
				json_t *json_body_target = json_object();

				json_object_set_new(json_body_target, "source_KME_ID", json_string(targetid));
				json_object_set_new(json_body_target, "target_KME_ID", json_string(sourceid));
				json_object_set_new(json_body, "type", json_string("Quantum"));

				json_object_set_new(json_body_target, "master_SAE_ID", json_string(saeid));

				json_object_set_new(json_body_target, "number", json_integer(keynumber));
				json_object_set_new(json_body_target, "size", json_integer(keysize));
				json_object_set_new(json_body_target, "key_ID", json_string(keyid.c_str()));
				string data = json_dumps(json_body_target, 0);
				cout << "Key Notify : [ " << store[sid].GetSourceID() << " <->" << store[sid].GetTargetID() << " ] " << sdnagentip << " : " << SDN_AGENT_PORT << " data : " << data << endl;
				cout << " | " << getSDNAgentIPFromController(store[sid].GetSourceID()) << " <-> " << getSDNAgentIPFromController(store[sid].GetTargetID()) << " | " << endl;

				cout << "JSON Data Posted - Status : Success" << endl;
				return json_body;
			}
		}
		json_decref(json_data);
		//json_decref(json_body);

		return json_body;
	}





json_t* SDNAgent::callbackKeyProvision(string jsondata)
	{
		//cout << "<<< Receive : Key Store GetKey" << endl;
		Log("<<< Receive :KeyProvision", "Request - RECEIVED................");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_t *json_response = json_object();
		json_error_t error;

		char *sourceid = NULL, *targetid = NULL, *saeid = NULL;

		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
			return json_body;
		}
		else
		{
			sourceid = (char *)json_string_value(json_object_get(json_data, "source_SAE_ID"));
			targetid = (char *)json_string_value(json_object_get(json_data, "target_SAE_ID"));
			int keynumber = json_integer_value(json_object_get(json_data, "Number"));
			int keysize = json_integer_value(json_object_get(json_data, "Size"));
			if (sourceid == NULL || targetid == NULL)
			{
				json_object_set_new(json_response, "status", json_string("Failed"));
				cout << "JSON Data Posted - Status : Source ID & Target ID - Not Valid" << endl;
				return json_response;
			}

			json_t *json_body_target = json_object();

			json_object_set_new(json_body_target, "source_SAE_ID", json_string(sourceid));
			json_object_set_new(json_body_target, "target_SAE_ID", json_string(targetid));

			json_object_set_new(json_body_target, "Number", json_integer(keynumber));
			json_object_set_new(json_body_target, "Size", json_integer(keysize));
			//string data = json_dumps(json_body_target, 0);
			return json_body_target;
		}
		return json_body;
	}


	json_t* SDNAgent::callbackKeyProvisionStatus(string jsondata)
	{
		//cout << "<<< Receive : Key Store GetKey" << endl;
		Log("<<< Receive :KeyProvisionStatus", "Request - RECEIVED................");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_t *json_response = json_object();
		json_error_t error;

		//char *sourceid = NULL, *targetid = NULL, *saeid = NULL;
		char *keyid = NULL;

		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "message", json_string("Key ID - Not Valid"));
			return json_body;
		}
		else
		{
			//sourceid = (char *)json_string_value(json_object_get(json_data, "source_SAE_ID"));
			//targetid = (char *)json_string_value(json_object_get(json_data, "target_SAE_ID"));
			//int keynumber = json_integer_value(json_object_get(json_data, "Number"));
			//int keysize = json_integer_value(json_object_get(json_data, "Size"));
			keyid = (char *)json_string_value(json_object_get(json_data, "key_ID"));
			if (keyid == NULL)
			{
				json_object_set_new(json_response, "status", json_string("Failed"));
				cout << "JSON Data Posted - Status : Key ID - Not Valid" << endl;
				return json_response;
			}

			json_t *json_body_target = json_object();
			json_object_set_new(json_body_target, "key_ID", json_string(keyid));
			return json_body_target;
		}
		return json_body;
	}



	json_t* SDNAgent::callbackControllerKm(string jsondata)
	{
		Log("<<< Receive :callbackControllerKm", "Request - RECEIVED................");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_error_t error;

		char *source_saeid = NULL, *target_saeid=NULL;
		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
			return json_body;
		}
		else
		{
			cout<<"BEFRE CONVERSION"<<endl;
			source_saeid = (char *)json_string_value(json_object_get(json_data, "source_SAE_ID"));
			target_saeid = (char *)json_string_value(json_object_get(json_data, "target_SAE_ID"));
			int keynumber = json_integer_value(json_object_get(json_data, "Number"));
			int keysize = json_integer_value(json_object_get(json_data, "Size"));
			cout<<"AFTER CONVERSION"<<endl;
			if (source_saeid == NULL || target_saeid == NULL)
			{
				json_object_set_new(json_body, "message", json_string("Source SAE ID & Target SAE ID - Not Valid"));
				cout << "JSON Data Posted - Status : Source SAE ID & Target SAE ID - Not Valid" << endl;
				return json_body;
			}

			json_t *json_body_target = json_object();

			json_object_set_new(json_body_target, "source_SAE_ID", json_string(source_saeid));
			json_object_set_new(json_body_target, "target_SAE_ID", json_string(target_saeid));

			json_object_set_new(json_body_target, "Number", json_integer(keynumber));
			json_object_set_new(json_body_target, "Size", json_integer(keysize));
			string data = json_dumps(json_body_target, 0);
			
			string keyid;
			string str_source_saeid(source_saeid);
			string str_target_saeid(target_saeid);

			string source_id = saeid_map[str_source_saeid].first;
			string target_id = saeid_map[str_source_saeid].second;

			if(source_id.empty() || target_id.empty())
			{
				source_id = saeid_map[str_target_saeid].first;
				target_id = saeid_map[str_target_saeid].second;
			}

			cout<<"SAE ID : ["<<str_source_saeid<<":"<<str_target_saeid<<"] Source ID : "<<source_id<<" Target ID : "<<target_id<<endl;
			if (source_saeid == NULL || target_saeid == NULL)
			{
				json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
				cout << "JSON Data Posted - Status : Source ID & Target ID - Not Valid" << endl;
				return json_body;
			}


			json_t *json_key[2];
			json_t *json_arrays = json_array();
			json_key[0] = json_object();
			json_key[1] = json_object();
			int sid = GetStoreId(0, source_id, target_id);
			if (sid == KEY_STORE_NOT_AVAILABLE)
			{
				cout << "Key Store - Not Available" << endl;
				json_object_set_new(json_body, "message", json_string("Key Store - Not Available "));
				return json_body;
			}
			else
			{
				char *keyid = NULL;
				keyid = (char *)json_string_value(json_object_get(json_data, "key_ID"));
				cout << "Number : " << keynumber << " Size : " << keysize << " key ID : " << keyid << endl;

				int ret = store[sid].KeyReserve(keysize, keyid);
				if (ret == 0)
				{
					json_object_set_new(json_body, "provision_status", json_string("Complete"));
					json_object_set_new(json_body, "key_ID", json_string("Success"));
					json_object_set_new(json_body, "provision_message", json_string("Success"));
				}
				else
				{
					json_object_set_new(json_body, "provision_status", json_string("Failed"));
					json_object_set_new(json_body, "key_ID", json_string("Failed"));
					json_object_set_new(json_body, "provision_message", json_string("Failed"));

				}
				return json_body;
			}
		}
		json_decref(json_data);
		json_decref(json_body);
	}






	json_t* SDNAgent::callbackNodeKeyStatus(string jsondata)
		{
			//cout << "<<< Receive : Key Store GetKey" << endl;
			Log("<<< Receive :callbackNodeKeyStatus", "Request - RECEIVED................");
			json_t *json_body = json_object();
			json_t *json_data = json_object();
			json_error_t error;

			char *node_id = NULL;

			json_data = json_loads(jsondata.c_str(), 0, &error);
			if (!json_data)
			{
				cout << "Empty JSON data / Failed loading string to json object" << endl;
				json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
				return json_body;
			}
			else
			{
				
				node_id  = (char *)json_string_value(json_object_get(json_data, "node_id"));
			
				for(int i=0;i<MAX_SAE_IDS;i++)
				{
					if(store[i].GetStatus()==true)
					{
					cout<<"keystore values----"<<"TARGET_NODE---"<<store[i].GetTargetID()<<endl;
					cout<<"keystore values----"<<"KEYSTORE_USED---"<<store[i].GetKeyStoreSize()<<endl;
					cout<<"keystore values----"<<"KEY STORE---"<<store[i].GetMaxKeyStoreSize()<<endl;
					cout<<"keystore values----"<<"SERVED_KEYCOUNT---"<<store[i].GetKeyCount()<<endl;
					cout<<"keystore values----"<<"MAX_KEYCOUNT---"<<store[i].GetMaxKeyCount()<<endl;
					cout<<"keystore values----"<<"ISPROVISIONED---"<<store[i].GetStatus()<<endl;
					
				
					json_object_set_new(json_body,"target_node",json_string(store[i].GetTargetID().c_str()));
					json_object_set_new(json_body,"keystore_used",json_integer(store[i].GetKeyStoreSize()));
					json_object_set_new(json_body,"keystore",json_integer(store[i].GetMaxKeyStoreSize()));
					json_object_set_new(json_body,"served_keycount",json_integer(store[i].GetKeyCount()));
					json_object_set_new(json_body,"max_keycount",json_integer(store[i].GetMaxKeyCount()));
					json_object_set_new(json_body,"isprovisioned",json_boolean(store[i].GetStatus()));
					}
				}
				return json_body;
			}
				
			
			json_decref(json_data);
			//json_decref(json_body);
			return json_body;
		}





json_t* SDNAgent::callbackKeyStoreGetKeyId(string jsondata)
	{
		cout << "<<< Receive : Key Store GetKeyID" << endl;
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_error_t error;
		char *sourceid = NULL, *targetid = NULL, *saeid = NULL;

		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (json_data == NULL)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "message", json_string("Source ID/Traget ID/Key ID - Not Available "));
			return json_body;
		}
		else
		{
			sourceid = (char *)json_string_value(json_object_get(json_data, "source_KME_ID"));
			targetid = (char *)json_string_value(json_object_get(json_data, "target_KME_ID"));
			saeid = (char *)json_string_value(json_object_get(json_data, "master_SAE_ID"));
			if (sourceid == NULL || targetid == NULL)
			{
				json_object_set_new(json_body, "message", json_string("Source ID/Traget ID/Key ID - Not Available "));
				cout << "JSON Data Posted - Status : Source ID/Traget ID/Key ID - Not Available" << endl;
				return json_body;
			}

			int sid = GetStoreId(0, sourceid, targetid);
			if (sid == KEY_STORE_NOT_AVAILABLE)
			{
				cout << "Key Store - Not Available" << endl;
				json_object_set_new(json_body, "message", json_string("Key Store - Not Available "));
				return json_body;
			}
			else
			{
				if (json_object_get(json_data, "key_ID") == NULL)
				{
					json_object_set_new(json_body, "message", json_string("Key_ID is not provided "));
					cout << "JSON Data Posted - Status : Failed(no key id)" << endl;
					return json_body;
				}

				string keyid = json_string_value(json_object_get(json_data, "key_ID"));

				json_t *json_key[2];
				json_t *json_arrays = json_array();
				json_key[0] = json_object();
				json_key[1] = json_object();

				string keyvalue = store[sid].GetKey(keyid);
				if (keyvalue == "")
				{
					json_object_set_new(json_body, "message", json_string(" key is not available "));
					cout << "JSON Data Posted - Status : Failed( no key available )" << endl;
					return json_body;
				}
				else
				{
					json_object_set_new(json_key[0], "key", json_string(keyvalue.c_str()));
					json_array_append_new(json_arrays, json_key[0]);
					json_object_set_new(json_body, "keys", json_arrays);
					cout << "Key ID : " << keyid << " Value : " << keyvalue << endl;
					cout << "JSON Data Posted - Status : Success" << endl;
					return json_body;
				}
			}
		}
		//json_decref(json_data);
		//json_decref(json_body);

		return json_body;
	}



	json_t* SDNAgent::callbackBB84Sifting(string jsondata)
	{
		Log("<<< RECEIVED Sifting Request", jsondata);
		json_t *json_body = json_object();
		char *source = NULL, *destination = NULL, *bits = NULL, *basis = NULL;
		json_t *json_data = json_object();
		json_error_t error;
		json_data = json_loads(jsondata.c_str(), 0, &error);
		string matchlist;
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			return json_body;
		}
		else
		{
			source = (char *)json_string_value(json_object_get(json_data, "source"));
			destination = (char *)json_string_value(json_object_get(json_data, "destination"));
			bits = (char *)json_string_value(json_object_get(json_data, "bits"));
			basis = (char *)json_string_value(json_object_get(json_data, "basis"));

			if (source == NULL || destination == NULL || bits == NULL || basis == NULL)
			{
				cout << "Source/Destination/bits/basis - Not Valid\n"
					 << endl;
				return json_body;
			}
			else
			{
				// cout<<"Preparing matchlist "<<endl;
				string matchlist = getMatchList(bits, basis, source, destination);
				string siftedkey = getSiftedKey(bits, basis, source, destination, matchlist);
			}
		}
		json_object_set_new(json_body, "source", json_string(source));
		json_object_set_new(json_body, "destination", json_string(destination));
		json_object_set_new(json_body, "matchlist", json_string(matchlist.c_str()));

		return json_body;
	}


	json_t* SDNAgent::callbackKeyNotify(string jsondata)
	{
		//	 << "<<< RECEIVED Key Notification " << endl; //<<jsondata<<endl;
		Log("<<< RECEIVED Key Notification ", jsondata);
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_error_t error;
		char *sourceid = NULL, *targetid = NULL, *saeid = NULL;

		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "message", json_string("Source ID & Target ID - Not Valid"));
			return json_body;
		}
		else
		{
			sourceid = (char *)json_string_value(json_object_get(json_data, "source_KME_ID"));
			targetid = (char *)json_string_value(json_object_get(json_data, "target_KME_ID"));
			saeid = (char *)json_string_value(json_object_get(json_data, "master_SAE_ID"));
			int sid = GetStoreId(0, targetid, sourceid);

			if (sid == KEY_STORE_NOT_AVAILABLE)
			{
				cout << "Key Store - Not Available" << endl;
				json_object_set_new(json_body, "message", json_string("Key Store - Not Available "));
				return json_body;
			}
			else
			{
				int keynumber = json_integer_value(json_object_get(json_data, "number"));
				int keysize = json_integer_value(json_object_get(json_data, "size"));
				char *keyid = NULL;
				keyid = (char *)json_string_value(json_object_get(json_data, "key_ID"));
				cout << "Number : " << keynumber << " Size : " << keysize << " key ID : " << keyid << endl;

				int ret = store[sid].KeyReserve(keysize, keyid);
				if (ret == 0)
					json_object_set_new(json_body, "status", json_string("success"));
				else
					json_object_set_new(json_body, "status", json_string("fail"));
				return json_body;
			}
		}
		return json_body;
	}



	json_t* SDNAgent::callbackSDNCommand(string jsondata)
	{
		//cout << endl
		//	 << "<<< RECEIVED Link Provision Request " << endl; //<<jsondata<<endl;
		Log("<<< RECEIVED Link Provision/Start/Stop Request ","");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_error_t error;

		const char *messageid = NULL, *messagetype = NULL, *command = NULL, *commandid = NULL;
		string response;
		Log(" Recevied Provision Message ", jsondata);

		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "response", json_string("Fail (invalid data)"));
			json_object_set_new(json_body, "Type", json_string("command"));
			return json_body;
		}

		postCommandFileUpdate(jsondata);

		messageid = json_string_value(json_object_get(json_data, "MESSAGE_ID"));
		messagetype = json_string_value(json_object_get(json_data, "MESSAGE_TYPE"));
		command = json_string_value(json_object_get(json_data, "COMMAND"));
		commandid = json_string_value(json_object_get(json_data, "COMMAND_ID"));

		strcpy(g_command_id, commandid);

		json_object_set_new(json_data, "IP", json_string(getSDNAgentIP("node_x").c_str()));  //node name argument not used
		json_object_set_new(json_data, "PORT", json_string("7500"));

		cout << "messageid : " << messageid << " messagetype : " << messagetype << " command : " << command << endl;

		// int ret = kstore.KeyReserve(keysize,keyid);
		Log(" SendTo(NetSquid) Provision Message ", jsondata);
		int ret = SendToQ(getNetSquidIP(), getNetSquidPort(), NETSQUID_PROVISION_URL_APPEND, json_data, false);

		cout << "Send Data : "
			 << " Messageid : " << messageid << " QQC_SERVER : " << getNetSquidIP() << " Port : " << getNetSquidPort() << endl;
		if(ret==-1)
		{
			json_object_set_new(json_body, "response", json_string("Fail"));
			response = "Fail";
		}
		else
		{
			json_object_set_new(json_body, "response", json_string("Success"));
			response = "Success";
		}
		json_object_set_new(json_body, "Type", json_string("command"));

		postCommandUpdate((char*)messageid, (char*)command, (char*)commandid, (char*)response.c_str());
		
		return json_body;

	}


	
	char * SDNAgent::EncryptAndEncode(json_t * jsondata)
	{
		char *jsonCipherTextEncoded;
		char keyInFile[64];
		FILE *fptr;
		string qne_home = getQNEHome();
		string keyfile = qne_home+FILENAME_SHARED_KEY;
		if ((fptr = fopen(keyfile.c_str(), "r")) == NULL) 
		{
			cout<<"File Open(shared key) - Failure ( "<<keyfile<<" )"<<endl;
			Log("Key File", "Open - Failure");
		}
		fscanf(fptr, "%[^\n]", keyInFile);
		fclose(fptr);
		const char *keyInHex = keyInFile;

		char *datacmd = (char *)malloc(4096);
		strcpy(datacmd, json_dumps(jsondata, 0));
		jsonCipherTextEncoded = encrypt(datacmd, keyInHex);
		return jsonCipherTextEncoded;
	}

	char * SDNAgent::EncryptAndEncode(const char* plaintextdata)
	{
		char *jsonCipherTextEncoded;
		char keyInFile[64];
		FILE *fptr;
		string qne_home = getQNEHome();
		string keyfile = qne_home+FILENAME_SHARED_KEY;
		if ((fptr = fopen(keyfile.c_str(), "r")) == NULL) 
		{
			cout<<"File Open(shared key) - Failure ( "<<keyfile<<" )"<<endl;
			Log("Key File", "Open - Failure");
		}
		fscanf(fptr, "%[^\n]", keyInFile);
		fclose(fptr);
		const char *keyInHex = keyInFile;
		jsonCipherTextEncoded = encrypt(plaintextdata, keyInHex);
		return jsonCipherTextEncoded;

	}


	json_t* SDNAgent::callbackRegisterApplication(string jsondata)
	{
		Log("<<< RECEIVED Register application Request ","");
		json_t *json_body = json_object();
		json_t *json_data = json_object();
		json_t *json_response = json_object();
		json_error_t error;

		string response;
		const char *source_KME_ID =NULL,*target_KME_ID =NULL,*application_type=NULL ,*saeid=NULL;
		source_KME_ID = (char *)malloc(128);
		target_KME_ID = (char *)malloc(128);
		application_type = (char *)malloc(128);
		Log(" Recevied Application request Message ", jsondata);
		json_data = json_loads(jsondata.c_str(), 0, &error);
		if (!json_data)
		{
			cout << "Empty JSON data / Failed loading string to json object" << endl;
			json_object_set_new(json_body, "response", json_string("Fail (invalid data)"));
			return json_body;

		}
		postCommandFileUpdate(jsondata);
		
		source_KME_ID = (char *)json_string_value(json_object_get(json_data, "source_KME_ID"));
		target_KME_ID = (char *)json_string_value(json_object_get(json_data, "target_KME_ID"));
		string data = json_dumps(json_data, 0);
		

		return json_data;
	}

	
	int SDNAgent::GetStoreId(int sae_id, string source, string destination, int mode)
	{
		int sid = KEY_STORE_NOT_AVAILABLE;
		for (int i = 0; i < MAX_STORE_IDS; i++)
		{
			if ((source == store[i].GetSourceID() && destination == store[i].GetTargetID()) || (source == store[i].GetTargetID() && destination == store[i].GetSourceID()))
			{
				sid = i;
				cout << " | " << GetNodeId() << " | Store ID : " << sid << " | Source Id : " << store[sid].GetSourceID() << " | Target ID : " << store[sid].GetTargetID() << " | " << endl;
				return sid;
			}
		}

		if (mode == STORE_ID_GET_CREATE)
		{
			if (sid == -1)
			{
				for (int i = 0; i < MAX_STORE_IDS; i++)
				{

					if (store[i].GetSourceID() == "" || store[i].GetTargetID() == "")
					{
						sid = i;
						store[sid].SetSourceID(source);
						store[sid].SetTargetID(destination);
						store[sid].SetStatus(true);

						cout << " | " << GetNodeId() << " | Store ID : " << sid << "(New) | Source Id : " << store[sid].GetSourceID() << " | Target ID : " << store[sid].GetTargetID() << " | " << endl;
						return sid;
					}
				}
			}
		}
		return sid;
	}
	
	int SDNAgent::postCommandFileUpdate(string jsondata)
	{
		ofstream commandfile;
		string qne_home = getQNEHome();
		string commandfilename = qne_home + QKD_NODE_FILE_BASE + GetNodeId() + "/" + QKD_COMMAND_FILE;
		commandfile.open(commandfilename, std::ios_base::app);

		commandfile << jsondata << "\n";
		commandfile.close();
		return 0;
	}

	int SDNAgent::postStatusFileUpdate(string jsondata)
	{
		ofstream statusfile;
		string qne_home = getQNEHome();
		string statusfilename = qne_home + QKD_NODE_FILE_BASE + GetNodeId() + "/" + QKD_STATUS_FILE;
		//cout << "Status File Path : " << statusfilename << endl;
		statusfile.open(statusfilename, std::ios_base::app);

		statusfile << jsondata << "\n";
		statusfile.close();
		return 0;
	}

	int SDNAgent::GetLogLevel()
	{
		return(this->log_level);

	}

    bool SDNAgent::SetLogLevel(int level)
	{
		this->log_level = level;
		return true;
	}

	bool SDNAgent::Log(string modulename, string data)
	{
		time_t curr_time;
		tm *curr_tm;
		char datetime_string[64];
		time(&curr_time);
		curr_tm = localtime(&curr_time);
		strftime(datetime_string, 64, "%d-%m-%Y %H:%M:%S", curr_tm);
		string dt(datetime_string);

		string qne_home = getQNEHome();
		ofstream logfile;
		string logfilename = qne_home + QKD_NODE_FILE_BASE + GetNodeId() + "/" + LOG_FILE_NAME;
		string msg="";
		msg=dt+" | "+modulename+"  |   DATA: "+data+"\n";
		switch(GetLogLevel())
		{
			case LOG_LEVEL_DEFAULT:
				;//cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				break;
			case LOG_LEVEL_PACKETS:
				cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl<<endl;
				break;
			case LOG_LEVEL_PERIODICAL:
				cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				break;
			case LOG_LEVEL_DEBUG:
				cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl<<endl;
				break;
			case LOG_TO_FILE:
				logfile.open (logfilename, std::ios_base::app);
				//logfile << datetime_string<< " | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				logfile << msg;
				logfile.close();
				//cout<<"Log File  : "<<logfilename<<" Data Added "<<endl;
				//cout<<datetime_string<< "  "<<modulename<<" : "<<modulename<<"  DATA: "<<data<<endl;
				break;
			default:
				break;
		}

		json_t *json_data = json_object();
		json_object_set_new(json_data, "datetime", json_string(dt.c_str()));
		json_object_set_new(json_data, "node", json_string(GetNodeId().c_str()));
		json_object_set_new(json_data, "module", json_string(modulename.c_str()));
		json_object_set_new(json_data, "data", json_string(data.c_str()));

		// int stat = SendToQ(getControllerIP(), getControllerPort(), SDN_SERVER_LOG_URL_APPEND, json_data, false);
		// if(stat < 0)
		// 	Log("Send Log o Controller","Failed");

		return true;
	}

	bool SDNAgent::Log(string modulename, char *ip, int port, bool status, int bytes)
	{
		time_t curr_time;
		tm *curr_tm;
		char datetime_string[64];
		time(&curr_time);
		curr_tm = localtime(&curr_time);
		strftime(datetime_string, 64, "%d-%m-%Y %H:%M:%S", curr_tm);
		string dt(datetime_string);

		ofstream logfile;
		string logfilename = QKD_NODE_FILE_BASE + GetNodeId() + "/" + LOG_FILE_NAME;
		string msg="";
		string ipaddr(ip);

		string strstatus = status?" SUCCESS.... ":" FAILURE ";
		msg=dt+" | " + GetNodeId() + "  | "+modulename+"  |   IP : "+ipaddr+":"+to_string(port)+" | Bytes : "+to_string(bytes)+" | "+strstatus+"\n";
		switch(GetLogLevel())
		{
			case LOG_LEVEL_DEFAULT:
				;//
				break;
			case LOG_LEVEL_PACKETS:
				;//cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				break;
			case LOG_LEVEL_PERIODICAL:
				;//cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				break;
			case LOG_LEVEL_DEBUG:
				//cout<<datetime_string<< " | "<<GetNodeId()<<"  | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				cout<<msg;
				break;
			case LOG_TO_FILE:
				logfile.open (logfilename, std::ios_base::app);
				//logfile << datetime_string<< " | "<<modulename<<" : "<<"  DATA: "<<data<<endl;
				logfile << msg;
				logfile.close();
				//cout<<"Log File  : "<<logfilename<<" Data Added "<<endl;
				//cout<<datetime_string<< "  "<<modulename<<" : "<<modulename<<"  DATA: "<<data<<endl;
				break;
			default:
				break;
		}

		return true;
	}


}
