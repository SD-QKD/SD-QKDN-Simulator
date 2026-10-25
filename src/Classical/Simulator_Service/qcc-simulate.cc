/*###################################################################### 
# 
# File Name: qcc-simulate.cc
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
# Description : SDN Agent Simulation for NS3 and REST service 
# 
# Author(s) : Sajimon P C(pcsaji@cdac.in)
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : SDN agent module
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/ 
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/internet-module.h"
#include "ns3/csma-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/tap-bridge-module.h"
//#include "ns3/distributed-simulator-impl.h"
#include "qcc-simulate.h"
#include "../SDN_Agent/SDNAgent.h"
#include "../QKD_Node/QKDNode.h"
#include "../Simulator_Service/utility.h"
#include "../Simulator_Service/simulator.h"


void updateSimulation();
void scheduleTxDataQueue();
void scheduleiTxDataQueue();

using namespace ns3;
using namespace std;

Ptr <SDNAgent> tcp[5]; 
Ptr <QKDNode> qkdn[5];

/*
Starting simulation of SDN agents after receiving requests from User Application
Core module of topology simulation/network setup
*/  
void* QCCSimulationServerThread(void *arg)
{
  std::string mode = "ConfigureLocal";
  std::string tapName = "tap0";
 
  string networkbase = "10.1.1.0"; //setting default values
  string networkmask = "255.255.255.0";
  
  Config::SetDefault ("ns3::CsmaNetDevice::Mtu", UintegerValue (1500));  //default MTU
  Config::SetDefault ("ns3::TcpSocket::InitialCwnd", UintegerValue (10)); //default congestion window size
  Config::SetDefault ("ns3::TcpSocket::SegmentSize", UintegerValue (1460)); //deault TCP segment size

  // Change the simulation type to realtime implementation mode for communicating wih realtime appplicationss
  GlobalValue::Bind ("SimulatorImplementationType", StringValue ("ns3::RealtimeSimulatorImpl"));
  
  GlobalValue::Bind ("ChecksumEnabled", BooleanValue (true));

  int topoid = getTopologyID();
  int maxnodes = getNodesInTopology(topoid) ;    
  maxnodes = getNodesCount();  //Fix: For avoiding nodes diffrenece in topology name and JSON data supplied 

  //creating all nodes in the provided topology
  NodeContainer nodes;
  nodes.Create ((maxnodes+1));

  //Setting network connections
  CsmaHelper csma;
  csma.SetChannelAttribute ("DataRate", DataRateValue (5000000));
  csma.SetChannelAttribute ("Delay", TimeValue (MilliSeconds (2)));
  NetDeviceContainer devices = csma.Install (nodes);

  //Installing internet stack
  InternetStackHelper stack;
  stack.Install (nodes);

  //validate IP address base and SetBase
  Ipv4AddressHelper address;
  cout<<"Network Base Address "<<getNetworkBase()<<endl;
  cout<<"Network Base Mask    "<<getNetworkMask()<<endl;
  address.SetBase (getNetworkBase(), getNetworkMask());


  Ipv4InterfaceContainer ifaces;
  ifaces = address.Assign (devices);

  // Tapbridge to connect external applications
  TapBridgeHelper tapBridge;
  tapBridge.SetAttribute ("Mode", StringValue (mode));
  tapBridge.SetAttribute ("DeviceName", StringValue (tapName));

  // Set ip address and netmask from the given topology
  tapBridge.SetAttribute ("IpAddress", Ipv4AddressValue (ifaces.GetAddress(0))); 
  tapBridge.SetAttribute ("Netmask", Ipv4MaskValue (getNetworkMask())); 

  // Install tabridge on first creatd node
  tapBridge.Install (nodes.Get (0), devices.Get (0));

  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();
  Packet::EnablePrinting (); 
  
  // Applying static routing for remaining created nodes to communicate through tab bridge   
  Ptr<Ipv4StaticRouting> staticRouting;
  for (int i=1; i<(maxnodes+1); i++)
  {
  	Ptr<Node> nx = nodes.Get(i);
  	staticRouting = Ipv4RoutingHelper::GetRouting <Ipv4StaticRouting> (nx->GetObject<Ipv4> ()->GetRoutingProtocol ());
    staticRouting->SetDefaultRoute (ifaces.GetAddress(0), 1 );
  } 
    
  cout<<endl<<"||||| SDN Agents |||||"<<endl;
  cout<<"Debug Level/Type : "<<getLogLevel()<<endl<<endl;

  //Create nodes withnode id, name, start, stop parameters
  for(int i=0; i<maxnodes; i++)
  {
    //SDN Agent application
    tcp[i] = CreateObject <SDNAgent> ();
    tcp[i]->SetNodeId(getNodeParams(i, PARAM_NODE_ID));
    tcp[i]->SetNodeName(getNodeParams(i, PARAM_NODE_NAME));
    tcp[i]->SetLogLevel(getLogLevel());
    tcp[i]->SetStartTime (MilliSeconds((i+1)*425));
    tcp[i]->SetStopTime (Seconds (86400)); //one day - 60x60x24

    // QKD Node application
    qkdn[i] = CreateObject <QKDNode> ();
    qkdn[i]->SetNodeId(getNodeParams(i, PARAM_NODE_ID));
    qkdn[i]->SetNodeName(getNodeParams(i, PARAM_NODE_NAME));

    qkdn[i]->SetLogLevel(getLogLevel());
    qkdn[i]->SetStartTime (MilliSeconds((i+1)*50));
    qkdn[i]->SetStopTime (Seconds (86400));
    
    //Installing SDN agent and QKD Node applictaions on nodes
    nodes.Get(i+1)->AddApplication (qkdn[i]); 
    nodes.Get(i+1)->AddApplication (tcp[i]);

  }

  // Store packets on pcap file is log level set to LOG_LEVEL_PACKETS
  string qne_home = getQNEHome();
  if(getLogLevel() == LOG_LEVEL_PACKETS)
  { 
    for(int i=0; i <= maxnodes; i++)
    {
      csma.EnablePcap (qne_home+FILENAME_PREFIX_PCAP, devices.Get (i), true);
    }
  }

  Simulator::Schedule(Seconds(getAgentUpdationInterval()), &updateSimulation);

  Simulator::Schedule(Seconds(0), &scheduleTxDataQueue);
  Simulator::Schedule(Seconds(0), &scheduleiTxDataQueue);


  Simulator::Run ();
  Simulator::Destroy ();
  return 0;	
}



void scheduleTxDataQueue()
{
  int topoid=getTopologyID();
  int maxnodes = getNodesInTopology(topoid);
  maxnodes = getNodesCount();  //Fix: For avoiding nodes diffrenece in topology name and JSON data supplied 

  for(int i=0; i<maxnodes; i++)
  {
    tcp[i]->ScheduleTxDataQueue();
  }
  Simulator::Schedule(MilliSeconds(10), &scheduleTxDataQueue);
}

void scheduleiTxDataQueue()
{
  int topoid=getTopologyID();
  int maxnodes = getNodesInTopology(topoid);
  maxnodes = getNodesCount();  //Fix: For avoiding nodes diffrenece in topology name and JSON data supplied 

  for(int i=0; i<maxnodes; i++)
  {
    tcp[i]->ScheduleiTxDataQueue();
  }
  Simulator::Schedule(MilliSeconds(10), &scheduleiTxDataQueue);
}

/*
API for periodical updates for ADN Agent and QKD application
It upates with defined time duration, default is 10 seconds
*/
void updateSimulation()
{
	Simulator::Schedule(Seconds(getAgentUpdationInterval()), &updateSimulation);
  int topoid=getTopologyID();
  int maxnodes = getNodesInTopology(topoid);
  maxnodes = getNodesCount();  //Fix: For avoiding nodes diffrenece in topology name and JSON data supplied 

  for(int i=0; i<maxnodes; i++)
  {
    qkdn[i]->PeriodicStatusUpdate();
    tcp[i]->PeriodicStatusUpdate();
  }
}


/*
API for stopping the simulation
*/
bool stopSimulation()
{

  Simulator::Stop();
  if(Simulator::IsFinished()==true)
    return true;
  else
    return false;
}



/*
API for getting the current status of simulation
*/
bool statusSimulation()
{
  if(Simulator::IsFinished()==true)
    return true;
  else
    return false;
}

