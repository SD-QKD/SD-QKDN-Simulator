########################################################################
# 
# File Name: BB84_Protocol.py
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
# Description : MAQAN Simulation using BB84 Protocol
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


import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.nodes.connections import DirectConnection,Connection
from netsquid.components import ClassicalChannel,QuantumChannel
from netsquid.qubits import create_qubits
from netsquid.qubits.operators import *
from random import randint, random
import random
from netsquid.components import Channel, QuantumChannel, ClassicalChannel
import array as arr
from netsquid.protocols import Protocol
from netsquid.qubits.qubitapi import *
from Netsquid_BB84 import hybridnetwork
from Netsquid_BB84  import BB84fibreloss
from Netsquid_BB84.BB84fibreloss import BB84FibreLossModel
import sys

hnw = hybridnetwork.Hybridnetwork(name="Maqan" ,port="5071",nodes="0")

matchList1=[]

class BB84(Protocol):
        
###GLOBAL VARIABLES FOR STORING BOB MEASUREMENT AND ALICE BASIS
    
    measurement=[]
    stateList=[]
    errorrate=[]
    qlist=[]
    alicebits=[]
    new_list=[]
    KeyB=[]
    Bobbasis=[]
    Alicebasis=[]
    KeyA=[]
    Qber=[]
    
    
    def BB84_Alice_sendQubits(self,sourcenode):
       
        qlist=[]
        self.stateList,qlist=Create_random_qubits(self.num_bits)
        
        self.sourcenode.ports[self.sourceport].tx_output(qlist)
        print("STEP 1:",sor ,"SENDING RANDOM BITS TO",dest,"VIA QUANTUM CHANNEL")
        print("\n")
        print(qlist)
        print("")
       
        BB84.Alicebasis=''.join(str(item) for item in self.stateList)
        
        print("SOURCE BASIS ",BB84.Alicebasis)
        print("\n")
        return qlist
    

    def BB84_Bob_measure_send(self,qlisttmp): # some qubits might be lost

        global bobbit
        bobbit=[]
        global bobmeasuredbit
        bobmeasuredbit=[]
        
        qlisttmp=qlisttmp.items
                  
        if not isinstance(qlisttmp[0], ns.qubits.qubit.Qubit): #case of not receiving qubits      
            pass
        else:
            B_basis, self.res_measure = Random_ZX_measure(self.num_bits,qlisttmp) 
            
            if B_basis[0] == 0 or B_basis[0] == 1 or B_basis[0] == 2:
                self.destinationnode.ports[self.destinationport].tx_output(B_basis)  # B send measurement
                               
                
            else :
                print("Bob measuring - Failed")
        BB84.Bobbasis=''.join(str(item) for item in B_basis)
        print("")
        print("STEP 2 : ",dest,"MEASURING BITS WITH PROBABILITY ")  
        print("\n")  
        print(self.res_measure)
        print("\n")
        print("MEASURED BITS LENGTH : ",len(self.res_measure))
        print("\n")
        print("STEP 3 : ",dest,"SENDING BASIS TO ",sor)
        print("\n")  
        print(B_basis)
        print("\n")
        print("LENGTH OF TRANSMITTED BASIS : ",len(B_basis))
        
        for i in self.res_measure:
            if type(i)==int:
                bobbit.append(i)
            if type(i)==tuple:
                bobbit.append(i[0])
        print("\n")
        print ("Destination measured bits                                   : ",bobbit)
        print("Length of Bob bit ",len(bobbit))
        for i in bobbit:
            if i!=2:
                bobmeasuredbit.append(i)
        print("Bob measured Bit  :",bobmeasuredbit)      
        BB84.measurement = ''.join(str(item) for item in bobmeasuredbit)
        return B_basis

    def BB84_Eve_measure_send(self,qlisttmp): # some qubits might be lost

        global bobbit
        bobbit=[]
        global bobmeasuredbit
        bobmeasuredbit=[]
        
        qlisttmp=qlisttmp.items
        print("INTERCEPTION BY EVE ")
                  
        if not isinstance(qlisttmp[0], ns.qubits.qubit.Qubit): #case of not receiving qubits      
            pass
        else:
            B_basis, self.res_measure = Random_ZXEve_measure(self.num_bits,qlisttmp)
            for i in self.res_measure:
                if type(i)==int:
                    bobbit.append(i) 
                elif type(i)==tuple:
                    bobbit.append(i[0])
            Evemeasurement="".join(str(item) for item in bobbit)
            evebasis="".join(str(item) for item in B_basis)
            print("Basis used by Eve :  ",evebasis)
            print("Measurement by Eve : ",Evemeasurement)
            self.switch_eve.ports[self.port_eve4].tx_output(qlisttmp)
        
        return B_basis
    
         
    def BB84_Alice_measure_send_keygen(self,opList):
        global matchlength  
        
        matchList=Compare_measurement(self.num_bits,self.stateList,opList.items) #get opList 
        matchlength=len(matchList)
        print("STEP 4: SENDING MATCHLIST TO ",dest)
        print("\n")
        print(matchList)
        
        self.sourcenode.ports[self.sourceclassicalport].tx_output(matchList)#  RETURNS MATCHLIST 
                     
        for i in matchList:
            self.key_A.append(self.stateList[i]%2) 
        
        print("\n")
        print("STEP 5: KEY GENERATION AT SOURCE ",sor)
        print(self.key_A)
        print("")
        BB84.KeyA=''.join(str(item) for item in self.key_A)
        
        return self.key_A
  
    
    
    def BB84_Bob_keygen(self,matchList):
        errorbit=[]
        for i in matchList.items:
            self.key_B.append(self.res_measure[int(i)][0])

        print("")
        print("STEP 6: KEY GENERATION AT DESTINATION ",dest)
        print(self.key_B)
        BB84.KeyB=''.join(str(item) for item in self.key_B)
        if(len(BB84.KeyB)==len(BB84.KeyA)):
            for i,j in zip(BB84.KeyA,BB84.KeyB):
                if(i!=j):
                    errorbit.append(i)
                else:
                    exit

            print("ERROR BIT ",errorbit)
        
        print("length of error bit",len(errorbit))
        qber=(len(errorbit)/len(bobmeasuredbit)*100)
        print("QBER   ",qber)
        
        BB84.Qber=round(qber,2)

        return self.key_B
        
    def setDestnode(self):
        connected_nodes[0][0]=self.node_a
        connected_nodes[0][1]=self.node_b

        connected_nodes[1][0]=self.node_a
        connected_nodes[1][1]=self.node_b
        connected_nodes[1][2]=self.node_eve

    def get_switch_index(self,switch_name):
        for index, value in enumerate(switches):
            if value == switch_name:
                return index
                break
            else: # no break
                print("") 


    def __init__(self, num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name): #,model=default
        super().__init__()
        global measurement
        global dest
        global sor
        global tmpport
        global switches
        global connected_ports
        global tx_port
        global connected_nodes
        global tx_node
        global switches
        global fibrelen
        global numQubit
        global model
     
        connected_ports= [[0 for columns in range(10)] for rows in range(5)]
        tx_port= [[0 for columns in range(10)] for rows in range(5)]
        connected_nodes=  [[0 for coulmns in range(10)] for rows in range (5)]
        tx_node= [[0 for coulmns in range(10)] for rows in range (5)]
        switches= []

        try:
            hnw.add_node("node_a")
            hnw.add_node("node_b")
            hnw.add_node("node_eve")
            hnw.add_node("switch_b")
            hnw.add_node("switch_eve")
        except:
            print("Node Already in Network")

        self.sourcenode = hnw.get_node(source)
        sor=self.sourcenode
        self.destinationnode = hnw.get_node(destination)
        dest=self.destinationnode
       
        self.switch_b = hnw.get_node("switch_b")
        self.switch_c = hnw.get_node("switch_eve")
       
        self.num_bits = num_bits
        numQubit=self.num_bits
        self.stateList = None
        self.res_measure = None
        self.key_A = []
        self.key_B = []
        self.fiberLenth = fibre_len
        self.fibre_loss_init = fibre_loss_init
        self.fibre_loss_length = fibre_loss_length
        self.fibre_lossmodel=fibre_lossmodel
        self.source = source
        self.destination = destination
        fibrelen=fibre_len
        model=self.fibre_lossmodel
      
        print("BB84_Protocol:: Init [ ", self.num_bits, " , ", self.fiberLenth, ", ", self.fibre_loss_init, " , ", self.fibre_loss_length , ",",self.fibre_lossmodel , ",", self.source,  ",", self.destination ," ]")
        print("\n")
        print("STARTING SIMULATION BETWEEN ",source," and ",destination, ) 
        print("\n") 
      
       
    def stop(self):
        super().stop()
        self._running = False


    def is_connected():
        super().is_connected()
        pass     
   
    def configure(self):
            source= self.source
            destination=self.destination
                   
            if(source=="node_a" and destination=="node_b"):
                print("PROVISIONING PATH IS READY ")

                self.switch_b.ports[self.port_switchb1].forward_input(self.switch_b.ports[self.port_switchb2])
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_1")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node('switch_b'), label="classical_2AB")
                self.tmp2port,self.sourceclassicalport = hnw.get_connected_ports(hnw.get_node('switch_b'),self.sourcenode,label="classical_4")    
       
    def get_nodes(self):
        global switches 
        self.node_a = hnw.get_node("node_a")
        self.node_b = hnw.get_node("node_b")
        self.node_eve = hnw.get_node("node_eve")
        
        self.switch_b = hnw.get_node("switch_b")
        self.switch_eve = hnw.get_node("switch_eve")
        
        switches =[self.switch_b,self.switch_eve]  

    def setup_connection(self):
        
        print("TOPOLOGY SIMULATED ")
        self.MyQfiber=QuantumChannel("QFibre_A->B", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)     
        self.MyQfiber1=QuantumChannel("QFibre_A1->B1", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber2=QuantumChannel("QFibre_SB->SC", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber3=QuantumChannel("QFibre_SC->C", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber4=QuantumChannel("QFibre_SC->SE", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber5=QuantumChannel("QFibre_SE->F", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber6=QuantumChannel("QFibre_SB->SD", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber7=QuantumChannel("QFibre_SD->D", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber8=QuantumChannel("QFibre_B->SB", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber9=QuantumChannel("QFibre_C->SC", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber10=QuantumChannel("QFibre_D->SD", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        self.MyQfiber11=QuantumChannel("QFibre_SD->SE", length=self.fiberLenth, loss_model=BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init), 
        depolar_rate=0)
        hnw.add_quantumconnection("node_a", "switch_b", label="quantum_1",  channel_to=self.MyQfiber,  bidirectional="", port_name_node1="", port_name_node2="",ip="127.0.0.1", port="7070")
        self.port_a1, self.port_switchb1 = hnw.get_connected_ports("node_a", "switch_b", label="quantum_1")    
        
        hnw.add_quantumconnection("switch_b", "node_b", label="quantum_2AB", channel_to=self.MyQfiber1, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchb2, self.port_b1 = hnw.get_connected_ports("switch_b", "node_b", label="quantum_2AB")
        
        hnw.add_quantumconnection("node_b", "switch_b", label="quantum_3AB", channel_to=self.MyQfiber8,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_b2,self.port_switchb3  = hnw.get_connected_ports("node_b", "switch_b", label="quantum_3AB")

        hnw.add_quantumconnection("node_a", "switch_eve",  label="quantum_ASEve",  channel_to=self.MyQfiber4,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_a2, self.port_eve1 = hnw.get_connected_ports("node_a", "switch_eve", label="quantum_ASEve")  

        hnw.add_quantumconnection("switch_eve", "node_b",  label="quantum_SEveB",  channel_to=self.MyQfiber11,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_eve4, self.port_b3 = hnw.get_connected_ports("switch_eve", "node_b", label="quantum_SEveB")        
        

        hnw.add_quantumconnection("switch_eve", "node_eve",  label="quantum_SNEve",  channel_to=self.MyQfiber10,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_eve3, self.port_nqeve2 = hnw.get_connected_ports("switch_eve", "node_eve", label="quantum_SNEve")        
        
        hnw.add_quantumconnection( "node_eve","switch_eve",  label="quantum_SNEve1",  channel_to=self.MyQfiber2,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_nqeve1,self.port_eve2 = hnw.get_connected_ports("switch_eve", "node_eve", label="quantum_SNEve1")        

        ###CLASSICAL CONNECTION
        hnw.add_connection("switch_b", "node_a", delay=(1,4), label="classical_1AB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchbC2,self.port_Ca  = hnw.get_connected_ports("switch_b","node_a", label="classical_1AB")

        hnw.add_connection("switch_eve","node_a",  delay=(1,4), label="classical_ASEve", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Ceve1,self.port_Ca1 = hnw.get_connected_ports("switch_eve","node_a",label="classical_ASEve")
        hnw.add_connection("switch_eve", "node_eve", delay=(1,4), label="classical_SSEve", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Ceve2,self.port_nCeve1 = hnw.get_connected_ports("switch_eve", "node_eve",label="classical_SSEve")
        hnw.add_connection("node_b", "switch_eve", delay=(1,4), label="classical_SEveB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Cb2,self.port_Ceve3 = hnw.get_connected_ports("node_b", "switch_eve",label="classical_SEveB")


        hnw.add_connection("node_b","switch_b",  delay=(1,4), label="classical_2AB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Cb,self.port_switchbC1  = hnw.get_connected_ports("node_b","switch_b", label="classical_2AB")

        hnw.add_connection("node_f", "switch_e", delay=(1,4), label="classical_1", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")

        hnw.add_connection("switch_e","switch_c", delay=(1,4), label="classical_2", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")

        hnw.add_connection("switch_c", "switch_b", delay=(1,4), label="classical_3", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")

        hnw.add_connection("switch_b", "node_a", delay=(1,4), label="classical_4", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchbC2, self.port_Ca = hnw.get_connected_ports("switch_b", "node_a", label="classical_4")

        hnw.add_connection("node_d", "switch_d", delay=(1,4), label="classical_3DD", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        hnw.add_connection("switch_e","switch_d", delay=(1,4), label="classical_2ED", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")

        hnw.add_connection("switch_d", "switch_b", delay=(1,4), label="classical_3DB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")

        hnw.add_connection("node_c", "switch_c", delay=(1,4), label="classical_1AC", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        
       
    def get_port(self, switch_x, node_x):
        port_list=[]
        for i in range(len(connected_nodes)):
            if i == switch_x:
                for j in range(len(connected_nodes[i])):
                    node_count=1
                    try:
                        node_count = len(connected_nodes[i][j])
                    except:
                        node_count=1
                    for k in range(node_count):
                        if(node_count > 1):
                            if(node_x == connected_nodes[i][j][k]):
                                port_list.append(j)   
                        else:
                            if(node_x == connected_nodes[i][j]):
                                port_list.append(j)
                                
                            break
        return port_list
        

    def get_port_name(self,switch_index, port_index):
        return connected_ports[switch_index][port_index]
    
        
    def handlers(self):    

        handler_b1 = lambda qlist: print(f"\n Bob received \n{qlist} at {ns.sim_time()}!")
        handler_c1 = lambda qlist: print(f"\n C received \n{qlist} at {ns.sim_time()}!")
        handler_f1 = lambda qlist: print(f"\n F received via C \n{qlist} at {ns.sim_time()}!")       
        handler_e1 = lambda qlist: print(f"\n E received \n{qlist} from C at {ns.sim_time()}!")

        handler_b2q = lambda qlist: self.switch_b.ports[self.port_switchb4].tx_output(qlist)
        handler_c2q = lambda qlist: self.switch_c.ports[self.port_switchc4].tx_output(qlist)
        handler_e2q = lambda qlist: self.switch_e.ports[self.port_e3].tx_output(qlist)     
        
        handler_b2qAB = lambda qlist: self.switch_b.ports[self.port_switchb2].tx_output(qlist)
        self.switch_b.ports[self.port_switchb2].bind_input_handler(handler_b2qAB)

        handler_seve = lambda qlist: self.switch_eve.ports[self.port_eve4].tx_output(qlist)
        self.switch_eve.ports[self.port_eve4].bind_input_handler(handler_seve)

        handler_b2q = lambda qlist: self.switch_b.ports[self.port_switchb5].tx_output(qlist)
        handler_d2q = lambda qlist: self.switch_d.ports[self.port_switchd4].tx_output(qlist)
        handler_e2q = lambda qlist: self.switch_e.ports[self.port_e3].tx_output(qlist)

##A TO C
        handler_c2qAC = lambda qlist: self.switch_c.ports[self.port_switchc2].tx_output(qlist)
###A TO D

        handler_d2qDD = lambda qlist: self.switch_d.ports[self.port_switchd2].tx_output(qlist)
        self.node_b.ports[self.port_b3].bind_input_handler(self.BB84_Bob_measure_send)##A TO B
        
        self.sourcenode.ports[self.sourceclassicalport].bind_input_handler(self.BB84_Alice_measure_send_keygen)
        
        self.destinationnode.ports[self.destinationport].bind_input_handler(self.BB84_Bob_keygen)
    def handlerseve(self):    

        handler_b1 = lambda qlist: print(f"\n Bob received \n{qlist} at {ns.sim_time()}!")
        handler_c1 = lambda qlist: print(f"\n C received \n{qlist} at {ns.sim_time()}!")
        handler_f1 = lambda qlist: print(f"\n F received via C \n{qlist} at {ns.sim_time()}!")       
        handler_e1 = lambda qlist: print(f"\n E received \n{qlist} from C at {ns.sim_time()}!")

        handler_b2q = lambda qlist: self.switch_b.ports[self.port_switchb4].tx_output(qlist)
        
        handler_c2q = lambda qlist: self.switch_c.ports[self.port_switchc4].tx_output(qlist)
        handler_e2q = lambda qlist: self.switch_e.ports[self.port_e3].tx_output(qlist)
     
        
        handler_b2qAB = lambda qlist: self.switch_b.ports[self.port_switchb2].tx_output(qlist)
        self.switch_b.ports[self.port_switchb2].bind_input_handler(handler_b2qAB)

        handler_seve = lambda qlist: self.switch_eve.ports[self.port_eve4].tx_output(qlist)
        self.switch_eve.ports[self.port_eve4].bind_input_handler(handler_seve)
        
        self.switch_eve.ports[self.port_eve4].bind_input_handler(self.BB84_Eve_measure_send)


        handler_b2q = lambda qlist: self.switch_b.ports[self.port_switchb5].tx_output(qlist)

        handler_d2q = lambda qlist: self.switch_d.ports[self.port_switchd4].tx_output(qlist)
        handler_e2q = lambda qlist: self.switch_e.ports[self.port_e3].tx_output(qlist)

##A TO C
        handler_c2qAC = lambda qlist: self.switch_c.ports[self.port_switchc2].tx_output(qlist)

###A TO D

        handler_d2qDD = lambda qlist: self.switch_d.ports[self.port_switchd2].tx_output(qlist)
        self.node_b.ports[self.port_b3].bind_input_handler(self.BB84_Bob_measure_send)##A TO B
        
        self.sourcenode.ports[self.sourceclassicalport].bind_input_handler(self.BB84_Alice_measure_send_keygen)
        
        self.destinationnode.ports[self.destinationport].bind_input_handler(self.BB84_Bob_keygen)
    def switches_connected(self):
        s=self.source
        d=self.destination
        if(s=="node_a" and d=="node_b"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)

        if(s=="node_a" and d=="node_c"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)
            print(self.switch_c)

        if(s=="node_a" and d=="node_d"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)
            print(self.switch_d)

        if(s=="node_a" and d=="node_f"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)
            print(self.switch_c)
            print(self.switch_e)


        if(s=="node_b" and d=="node_c"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)
            print(self.switch_c)

        if(s=="node_b" and d=="node_d"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)
            print(self.switch_d)

        if(s=="node_b" and d=="node_f"):
            print("CONNECTED SWITCHES ")
            print(self.switch_b)
            print(self.switch_c)
            print(self.switch_e)

        if(s=="node_c" and d=="node_f"):
            print("CONNECTED SWITCHES ")
            print(self.switch_c)
            print(self.switch_e)

        if(s=="node_d" and d=="node_f"):
            print("CONNECTED SWITCHES ")
            print(self.switch_d)
            print(self.switch_e)


    def handler_x(self):

         ####A TO C
        s=self.source
        d=self.destination
        switch_index = self.get_switch_index(self.switch_b)
        switch_index1 = self.get_switch_index(self.switch_eve)
            
        if(s=="node_a" and d=="node_b"):
            port_index = self.get_port(switch_index, hnw.get_node(s))
            switch_index = self.get_switch_index(self.switch_b)
            port_index1 = self.get_port(switch_index, hnw.get_node(d))
            handler_1 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index[0])].tx_output(Bobbasis)
            self.switch_b.ports[self.port_switchbC1].bind_input_handler(handler_1)
            handler_2 = lambda matchList: self.switch_b.ports[self.get_port_name(switch_index,port_index1[0])].tx_output(matchList)
            self.switch_b.ports[self.port_switchbC2].bind_input_handler(handler_2)
   
 
    def sendqubits(self):
        self.BB84_Alice_sendQubits(sor)
        
        
def startsim(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name):
    print("TOPOLOGY SIMULATED")
    b=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name)
    b.get_nodes()
    b.setup_connection()
def provisioningnodes(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,sourcep,destp):
    
    b1=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination)

    b1.get_nodes()

    sorce=hnw.get_node(sourcep)
    destn=hnw.get_node(destp)

   
    if sorce.name==source and destn.name==destination:
        print("ALL NODES ARE PROVISIONED AND PATH IS CLEAR")
        #b1.get_nodes()
        b1.switches_connected()
        try:
            b1.configure()
        except:
            print("")
    
    else:
        print("Node is not up")

    print("")



def startcommand(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination):
    print("SIMULATION STARTED")
    b2=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination)
    #print("CHECK#########")
    b2.get_nodes()
    b2.setup_connection()
    
    b2.switches_connected()
    b2.configureeve()
    
    b2.setTxPorts()
    b2.setDestnode()
    b2.handler_xeve()
    b2.sendqubits()
    b2.handlers()

def linkstatus(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,tr,rx):
    b4=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination)
    print("SOURCE ",source)
    if tr==b4.source and rx==b4.destination:
        b4.setup_connection()
        sorce=hnw.get_node(source)
        destn=hnw.get_node(destination)
        print("Node up",hnw.get_node(tr),hnw.get_node(rx))
        print("tr.name",sorce.name)
        q_conn = hnw.get_connection(sorce, destn.name,label="quantum_1")
        q_conn1 = hnw.get_connection(source, destination)
        print("QConnection ",q_conn)
        print("link up")
    else:
        print("link down")    

    
    
# if there's a qubit loss, both opList and loc_res_measure will have value 2 in the such slot in the list
def Random_ZX_measure(num_bits,qlist):
    opList = [2]*num_bits
    loc_res_measure=[2]*num_bits
    for q in qlist:
        rbit = randint(0,1)
        num=int(q.name[1:]) # get value before qubit name "Q"
        opList[num] = rbit
        if rbit==0:
            loc_res_measure[num]=ns.qubits.qubitapi.measure(q,observable=Z) #measure in standard basis
        elif rbit==1:
            loc_res_measure[num]=ns.qubits.qubitapi.measure(q,observable=X) #measure in Hadamard basis
        else:
            print("Measuring - ERROR\n")
   
   
    return opList,loc_res_measure

# returns a list of stats and a list of qubits
def Create_random_qubits(num_bits):
    res_state=[]
    
    qlist=[]
    global measuredsourcebit
    sourcebit=[]
    global sbit
    sbit=[]
    measuredsourcebit=[]
    
    qlist=create_qubits(num_bits,system_name="Q") 
    for i in range(0,num_bits):
        res_state.append(randint(0,3))
    for a,b in zip(res_state, qlist):
        if   a == 0: # 0 state
            sourcebit.append(ns.qubits.qubitapi.measure(b,observable=Z))
          
            pass
        elif a == 1: # 1 state    #X
            operate(b, X)
            sourcebit.append(ns.qubits.qubitapi.measure(b,observable=Z))
            
        elif a == 2: # + state    #H
            operate(b, H)
            sourcebit.append(ns.qubits.qubitapi.measure(b,observable=X))
         
        elif a == 3: # - state    #XH
            operate(b, X)
            operate(b, H)
            sourcebit.append(ns.qubits.qubitapi.measure(b,observable=X))
            
        else :
            print("Create random bits - ERROR")
    
    for i in sourcebit:
        sbit.append(i[0])
        
        measuredsourcebit=''.join(str(item) for item in sbit)
    print("MEASURED SOURCE BIT ",measuredsourcebit)    
    
    return res_state, qlist


# Campare two list of measurements then return a list of match cases  
def Compare_measurement(num_bits,stateList,opList):
    matchList=[]
    for i in range(0,num_bits):
        if stateList[i]<2 and opList[i]==0:    #measure in standard basis
            matchList.append(i)
        elif stateList[i]>=2 and opList[i]==1: #measure in Hadamard basis
            matchList.append(i)
        else:
            pass
    
    return matchList


