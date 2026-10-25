########################################################################
# 
# File Name: qqc.py
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 30/10/2022
# 
# Purpose : Quantum Simulation
# 
# Description : QKD Quantum Channel(QQC) Simulation and REST service 
# 
# Author(s) : Neethu V,neethuv@cdac.in
# 
# Version No : v1.0
# 
# Revisions : 
# 
# Remarks : 
# 
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
########################################################################
from glob import glob
from hmac import trans_36
from click import command
import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.nodes.connections import DirectConnection
from netsquid.components import ClassicalChannel
from netsquid.components import FibreLossModel

from netsquid.components.models.qerrormodels import DepolarNoiseModel, DephaseNoiseModel
from netsquid.qubits import create_qubits
from netsquid.qubits.operators import *
from random import randint
from Netsquid_BB84 import hybridQchannel
from Netsquid_BB84.hybridQchannel import QLinkparameter
from Netsquid_BB84 import hybridGeneralparameter
from Netsquid_BB84.hybridGeneralparameter import Generalparameters
from Netsquid_BB84.nodestatus import Nodestatus

from Netsquid_BB84 .Maqan import BB84
from Netsquid_BB84 .Maqan import *
from Netsquid_BB84  import Maqan
from Netsquid_BB84 import hybridnetwork
from Netsquid_BB84 import hybridprovision
from Netsquid_BB84.hybridprovision import Provision
from Netsquid_BB84 import BB84_eveparameters
from Netsquid_BB84.BB84_eveparameters import Eveparameter
from Netsquid_BB84 import hybridtopology
from Netsquid_BB84.hybridtopology import Topology
from Netsquid_BB84 import hybridnodeprovision
from Netsquid_BB84.hybridnodeprovision import Nodeprovision

from Netsquid_BB84 .BB84_TwonodeEve import BB84
from Netsquid_BB84 .BB84_TwonodeEve import *
from Netsquid_BB84  import BB84_TwonodeEve

import time
from flask import Flask, json, jsonify, request
import time

SERVER_CONFIG_FILE="server.conf"
GUI_SERVER="gui"
QCC_SERVER="simulator"
SDN_SERVER="sdncontroller"
QQC_SERVER="quantumchannel"
qconf = [0 for i in range(10)] 
global Qlink
class QnsConfig:
    count=0
    def __init__(self,servername,ip, port):
        self.servername = servername         
        self.ip= ip  
        self.port = port
        
def get_qcc_server_ip(sever):
    for i in range(0,4):
        if(qconf[i].servername == sever):    
            return qconf[i].ip
            
def get_qcc_server_port(sever):
    for i in range(0,4):
        if(qconf[i].servername == sever):    
            return qconf[i].port
            
def load_default_configuration():
    qconf[0]= QnsConfig("gui","127.0.0.1","5050")
    qconf[1]= QnsConfig("simulator","127.0.0.1","5071")
    qconf[2]= QnsConfig("quantumchannel","127.0.0.1","5072")
    qconf[3]= QnsConfig("sdncontroller","127.0.0.1","8080")
    
                
def load_confiuration():
    try:            
        file1 = open(SERVER_CONFIG_FILE, 'r')
        Lines = file1.readlines()
        count = 0
        for line in Lines:
            x = line.split("=", 1)
            y = x[1].split(":",1)
            qconf[count]= QnsConfig(x[0].strip(),y[0].strip(),y[1].strip())
            count += 1
    except:
        load_default_configuration()      

load_confiuration()
def generate_version_number():
    with open("version.txt", "r+") as file:
        version_number = int(file.read().strip())
        version_number += 1
        file.seek(0)
        file.write(str(version_number))
        file.truncate()
    return version_number

# Usage
version = generate_version_number()
print("version - 0.0.",version)

api = Flask(__name__)

def run_BB84_sim_provision(runtimes=1,num_bits=8,fibre_len=10**-6,fibre_loss_init=0.01,fibre_loss_length=0.4,fibre_lossmodel=FibreLossModel,source="node_a", destination="node_b",topology_id="1",topology_name="MAQAN"):

    bb84_list=[]  
    linkstatus=1 
    global b1
 
    if runtimes <= 0 :
        runtimes = 10000000000000000000000000000000000000000000
    
    for i in range(runtimes):
        
        print("Userapp:: run_BB84_sim: #",i," ... ", source,"->", destination)
        if topology_id=="1":
            Maqan.startcommand(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel, source,destination,topology_id,topology_name)
        elif topology_id=="2": 
            BB84_TwonodeEve.startcommand(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel, source,destination,topology_id,topology_name)
        elif topology_id=="3":
            BB84_TwonodeEve.startcommandeve(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel, source,destination,topology_id,topology_name,eve.attacktype,eve.attackpercentage)

        try:
            ns.sim_run()
        except:
            print("")
        Hybrid_Send(source, destination,topology_id,topology_name)
        
        time.sleep(2) 
    
    return bb84_list

def BB84_main_provision(transmitter_id, receiver_id,topology_id,topology_name, mcommand):
        
        
        run_times=0
        num_bits=100
        print("qlink  ",Qlink)
        distance=Qlink.length
        print("distance Qlink ",distance)
        fibre_loss_init=Qlink.ploss_init
        fibre_loss_length=Qlink.ploss_length
        fibre_lossmodel=Qlink.lossmodel

        print("*********** BB84 Protocol Simulation ***************")
        
        print("QQC:: main [ ", run_times, " , ", num_bits, ", ", distance, " ]")
        ns.sim_reset()
        print("TRANSMITTER ID : ",transmitter_id)
        keylist=run_BB84_sim_provision(run_times,num_bits,distance/1000,fibre_loss_init,fibre_loss_length,fibre_lossmodel, source=transmitter_id, destination=receiver_id,topology_id=topology_id,topology_name=topology_name)
        keylen = len(keylist)
        
        print("QQC:: main: Key ", keylist)
        print("QCC:: main: Key length ", keylen)

        Hybrid_Send(transmitter_id, receiver_id,topology_id,topology_name)

        print("")

def run_BB84_start_topology(runtimes=1,num_bits=8,fibre_len=10**-6,fibre_loss_init=0.01,fibre_loss_length=0.4,fibre_lossmodel="",source="node_a", destination="node_b",topology_id="1", topology_name="MAQAN"):

    bb84_list=[]  
    linkstatus=1 
    if runtimes <= 0 :
        runtimes = 10000000000000000000000000000000000000000000
    
    for i in range(1):
        ns.sim_run()
        if topology_id=="1":
            {
                Maqan.startsim(num_bits,Qlink.length,Qlink.ploss_init,Qlink.ploss_length,Qlink.lossmodel,source,destination,topology_id,topology_name)
            }

        elif topology_id=="2":
            {
               BB84_TwonodeEve.startsim(num_bits,Qlink.length,Qlink.ploss_init,Qlink.ploss_length,Qlink.lossmodel,source,destination,topology_id,topology_name)
            }
        elif topology_id=="3":
            {
                BB84_TwonodeEve.startsim(num_bits,Qlink.length,Qlink.ploss_init,Qlink.ploss_length,Qlink.lossmodel,source,destination,topology_id,topology_name)
            }
        
        time.sleep(2)  
     
    
    return bb84_list

def BB84_provision(runtimes=1,num_bits=8,fibre_len=10**-6,fibre_loss_init=0.01,fibre_loss_length=0.4,fibre_lossmodel=FibreLossModel,source="node_a", destination="node_b"):

    bb84_list=[] 
    linkstatus=1
    
    b=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel, source,destination)
    runtimes=2
        
    if runtimes <= 0 :
        runtimes = 10000000000000000000000000000000000000000000
    
    for i in range(runtimes):
        ns.sim_run()
        Maqan.provisioningnodes(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination) 
        time.sleep(2)
       
        print("")
    
    return bb84_list
def BB84_start_topology(topology_id, topology_name):
        
        
        run_times=0
        num_bits=100
        distance=Qlink.length
        
        
        
        print("*********** SIMULATOR UP ***************")
        
        
        print("QQC:: main [ ", run_times, " , ", num_bits, ", ", distance, " ]")
        print(topology_id,topology_name)
        ns.sim_reset()
        
        keylist=run_BB84_start_topology(run_times,num_bits,distance, topology_id=topology_id, topology_name=topology_name)
        keylen = len(keylist)

        print("")
    
def BB84_mainsimulation1(msource, mdestination, mcommand):
        
        
        run_times=0
        num_bits=100
        distance=Qlink.length
        
        print("*********** SIMULATOR UP ***************")

        print("QQC:: main [ ", run_times, " , ", num_bits, ", ", distance, " ]")
        ns.sim_reset()
        
        keylist=BB84_provision(run_times,num_bits,distance/1000, source=msource, destination=mdestination)
        keylen = len(keylist)
        
        print("")

def BB84_status(runtimes=1,num_bits=8,fibre_len=10**-6,fibre_loss_init=0.01,fibre_loss_length=0.4,fibre_lossmodel=FibreLossModel,source="node_a", destination="node_b"):

    bb84_list=[] 
    linkstatus=1
    
    b=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel, source,destination)
        
    if runtimes <= 0 :
        runtimes = 10000000000000000000000000000000000000000000
    
    for i in range(runtimes):
        ns.sim_run()

        Maqan.provisioningnodes(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination) 
        time.sleep(2)
    
    return bb84_list        
def BB84_mainstatus(msource, mdestination, mcommand):

        run_times=0
        num_bits=100
        distance=Qlink.length
        
        print("*********** SIMULATOR UP ***************")
        
        print("QQC:: main [ ", run_times, " , ", num_bits, ", ", distance, " ]")
        ns.sim_reset()
        
        keylist=BB84_status(run_times,num_bits,distance/1000, source=msource, destination=mdestination)
        keylen = len(keylist)

        print("")

##SEND TO HYBRID NETWORK 
def Hybrid_Send(transmitter_id, receiver_id,topology_id,topology_name):  
    
    hnbb84 = hybridnetwork.Hybridnetwork(name="hybrid_network" ,port=get_qcc_server_port(QCC_SERVER),nodes="0")
   
    try:
        print("#############")
        print (" TOPOLOGYID SED ", topology_id)
        if topology_id=="1":
            print()
            print("=Nodeprovision.ip",nodeprovisionobj.ip)
            
            hnbb84.send(source=transmitter_id,destination=receiver_id,sourcebit=str(Maqan.measuredsourcebit),res_measure=str(Maqan.BB84.measurement),B_basis=str(Maqan.BB84.Bobbasis),stateList=str(Maqan.BB84.Alicebasis),sourceip=provision_store.destinationip[0],destinationip=provision_store.destinationip[1],keyA=str(Maqan.BB84.KeyA),keyB=str(Maqan.BB84.KeyB),port=nodeprovisionobj.port,qber=str(Maqan.BB84.Qber))
        
        elif topology_id=="2" or topology_id=="3":
            print("TOPOLOGYID2")
            hnbb84.send(source=transmitter_id,destination=receiver_id,sourcebit=str(BB84_TwonodeEve.measuredsourcebit),res_measure= str(BB84_TwonodeEve.BB84.measurement),B_basis= str(BB84_TwonodeEve.BB84.Bobbasis),stateList=str(BB84_TwonodeEve.BB84.Alicebasis),sourceip=provision_store.destinationip[0],destinationip=provision_store.destinationip[1],keyA=str(BB84_TwonodeEve.BB84.KeyA),keyB=str(BB84_TwonodeEve.BB84.KeyB),port=nodeprovisionobj.port,qber=str(BB84_TwonodeEve.BB84.Qber))
            #TODO send source, destination, and( bit, basis, key) of both
    except:
        print("REST server connection - Failed\n")


api = Flask(__name__)

@api.route('/sim/status', methods=['POST'])
def get_simulator_status():
    print("Simulator Status")
    json_data = request.json
    print(json.dumps(json_data))
    topology_id = json_data["topology-id"]
    topology_name = json_data["topology-name"]
    i=ns.sim_state()
    user = request.args.get(i)
    print("SIM STATUS",user)
    return jsonify(i)


@api.route('/sim/probe/topology', methods=['POST'])
def get_simulator_probe_topoloy():
    print("Probe Simulator Topology")
    json_data = request.json
    return json.dumps(json_data)


@api.route('/sim/simulatetopology', methods=['POST'])
def get_simulator_simulate_topoloy():
    print("Simulate Topology")
    json_data = request.json
    print(json.dumps(json_data))
    topology_id = json_data["topology-id"]
    topology_name = json_data["topology-name"]

    global qlength,nodeidarray,nodeidarray2nodes,nodeidarray3nodes
    nodeidarray=[]
    nodeidarray2nodes=[]
    nodeidarray3nodes=[]
    if topology_id=="1":
        node_ids = [node['nodeid'] for node in json_data['nodes']]
        print(node_ids)
        nodeidarray.append(node_ids)
    elif topology_id=="2" :
        node_ids = [node['nodeid'] for node in json_data['nodes']]
        print(node_ids)
        nodeidarray2nodes.append(node_ids)
    elif topology_id=="3":
        node_ids = [node['nodeid'] for node in json_data['nodes']]
        print(node_ids)
        nodeidarray3nodes.append(node_ids)
    
    qlength = int(json_data["links"][0]["fiberlength"])
    print(qlength)
    qlossmodel = json_data["links"][0]["fiberlossmodel"]
    
    qploss_init= float(json_data["links"][0]["fiberlossinint"])
    qploss_length=float(json_data["links"][0]["fiberlosslength"])
    print("qploss_init",qploss_init)
    print("qploss_length",qploss_length)
    if topology_id=="3":
        attacktype=json_data['nodes'][1]['attacktype']
        print("ATTACKTYPE###",attacktype)
        attackpercentage=json_data['nodes'][1]['attackpercentage']
        print("ATTACKPERCENTAGE###", attackpercentage)
        global eve
        eve=Eveparameter(attacktype,attackpercentage)

    qnum_bits=100
    global Qlink,Qchannel,Genp,bq,Nodep,Pr,topologyobj
    Qlink= QLinkparameter(qlength,qnum_bits,qlossmodel,qploss_init,qploss_length)
    print("len*****",Qlink.length)

    topologyobj=Topology(topology_id,topology_name)

    print("Topology Id   :", topology_id)
    print("Topology Name :", topology_name) 
    BB84_start_topology(topology_id, topology_name) 
    return json.dumps("Success/Fail"),200



@api.route('/sim/stoptopology', methods=['POST'])
def get_simulator_stop_topoloy():
    print("Stop Topology")
    json_data = request.json
    topology_id = json_data["topology-id"]
    topology_name = json_data["topology-name"]
    print("Topology Id   :", topology_id)
    print("Topology Name :", topology_name) 
    ns.sim_stop()

    
    return json.dumps("Success/Fail"),200

@api.route('/sim/statustopology', methods=['POST'])
def get_simulator_status_topoloy():
    print("Status Topology")
    json_data = request.json
    topology_id=json_data["topology-id"]
    topology_name=json_data["topology-name"]
    print("Topology Id:",topology_id)
    print("Topology Name:",topology_name)
    return json.dumps("Success/Fail"),200

class Provisiondestinationstore():
    transmitterid=[]
    receiverid=[]
    destinationip=[]
           
    def reset(self):
        self.transmitterid = []
        self.receiverid = []
        self.destinationip = []

global request_counter
request_counter = 0

provision_store = Provisiondestinationstore()
@api.route('/sim/link/provision', methods=['POST'])

def post_simulator_link_provision():
    json_data = request.json
    command_id = json_data["COMMAND_ID"]
    command = json_data["COMMAND"]
    print("JSONDATA    ", json_data)
    transmitter_id = json_data['COMMAND_PARAMS'][0]['TRANSMITTER']
    receiver_id = json_data['COMMAND_PARAMS'][0]['RECEIVER']
    nip = json_data["IP"]
    nport = json_data["PORT"]

    global nodeprovisionobj, provision_store
    nodeprovisionobj = Nodeprovision(nip, nport)

    print("")
    print("Command Id        : ", command_id, ", Command : ", command)
    print("TRANSMITTER Id    : ", transmitter_id)
    print("RECEIVER Id       : ", receiver_id)
    print("Ip & Port         : ", nip, ",", nport)

    if command == "QUANTUM_CHANNEL_PROVISION":
        print("Link Provision ")
        
        provision_store.transmitterid.append(transmitter_id)
        provision_store.receiverid.append(receiver_id)
        provision_store.destinationip.append(nip)

        if len(provision_store.transmitterid) >= 2 and len(provision_store.receiverid) >= 2 and provision_store.transmitterid[0] == provision_store.transmitterid[1] and provision_store.receiverid[0] == provision_store.receiverid[1]:
            BB84_main_provision(transmitter_id, receiver_id, topologyobj.topologyid, topologyobj.topologyname, command)
        else:
            print("Wait for second request")
        global request_counter
        request_counter += 1
        if request_counter == 2:
            provision_store.reset()
            request_counter = 0

    return jsonify({'data': json_data}), 201


@api.route('/sim/link/stop', methods=['POST'])
def get_simulator_link_stop():
    print("Link Stop")
    json_data = request.json
    ns.sim_stop()
    return json.dumps(json_data)
    
@api.route('/sim/link/status', methods=['POST'])
def get_simulator_link_status():
    print("Link Status")
    json_data = request.json
    return json.dumps(json_data)


if __name__ == '__main__':
    api.run(host=get_qcc_server_ip(QQC_SERVER), port=get_qcc_server_port(QQC_SERVER)) 

