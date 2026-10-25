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


from cProfile import label
from operator import mod
import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.nodes.connections import DirectConnection,Connection
from netsquid.components import ClassicalChannel,QuantumChannel
from netsquid.qubits import create_qubits
from netsquid.qubits.operators import *
from random import randint
from netsquid.components import Channel, QuantumChannel, ClassicalChannel
import array as arr
from netsquid.protocols import Protocol
from netsquid.qubits.qubitapi import *
from Netsquid_BB84 import hybridnetwork
from Netsquid_BB84  import BB84fibreloss
from Netsquid_BB84.BB84fibreloss import BB84FibreLossModel

import sys

hnw = hybridnetwork.Hybridnetwork(name="Maqan" ,port="5071",nodes="0")

class BB84(Protocol):
        
###CLASS VARIABLES FOR SENDING PURPOSE
    
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
    switchaf=[]
    
    #STEP1 ALICE SEND QUBITS TO BOB

    def BB84_Alice_sendQubits(self,sourcenode):
       
        qlist=[]
        self.stateList,qlist=Create_random_qubits(self.num_bits)
        
        self.sourcenode.ports[self.sourceport].tx_output(qlist)
        print("STEP 1: ",sor ,"SENDING RANDOM BITS TO ",dest," via QUANTUM CHANNEL")
        print("\n")
       
        #print(qlist)
        print("      ")
        
        print("")
       
        BB84.Alicebasis=''.join(str(item) for item in self.stateList)
        
        print("SOURCE BASIS ",BB84.Alicebasis)
        
        print("\n")
       
        return qlist
    
    #BOB MEASURE USING Random_ZX_measure and send basis

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
        print("STEP 2: ",dest,"MEASURING BITS WITH PROBABILITY")  
        print("\n")  
        print(self.res_measure)
        print("\n")
        print("MEASURED BITS LENGTH : ",len(self.res_measure))
        print("\n")
        print("STEP 3: ",dest,"SENDING BASIS TO ",sor)
        print("\n")  
        print(B_basis)
        print("\n")
        print("LENGTH OF TRANSMITTED BASIS: ",len(B_basis))
        
        for i in self.res_measure:
            if type(i)==int:
                bobbit.append(i)
            if type(i)==tuple:
                bobbit.append(i[0])
        print("\n")
        print ("Destination measured bits                                   : ",bobbit)

        for i in bobbit:
            if i!=2:
                bobmeasuredbit.append(i)
        print("Bob measured bit : ",bobmeasuredbit)
        print("LEN BOB MEASURED BIT  : ",len(bobmeasuredbit))
       
        BB84.measurement = ''.join(str(item) for item in bobmeasuredbit)
        
        return B_basis

    
    #ALICE MEASURE USING Compare_measurement and sending matchlist
       
    def BB84_Alice_measure_send_keygen(self,opList):
        global matchlength  
        
        matchList=Compare_measurement(self.num_bits,self.stateList,opList.items) #get opList 
        matchlength=len(matchList)
        print("STEP 4: SENDING MATCHLIST TO ",dest)
        print("\n")
        print(matchList)
        
        #sending matchlist
        self.sourcenode.ports[self.sourceclassicalport].tx_output(matchList)##  RETURNS MATCHLIST 
                     
        for i in matchList:
            self.key_A.append(self.stateList[i]%2) 
        
        print("\n")
        print("STEP 5: KEY GENERATION AT SOURCE ",sor)
        print(self.key_A)
        print("")
        BB84.KeyA=''.join(str(item) for item in self.key_A)
        
        return self.key_A
  
    
    #BOB GENERATES KEY
    def BB84_Bob_keygen(self,matchList):
       
        errorbit=[]
        for i in matchList.items:
            self.key_B.append(self.res_measure[int(i)][0])

        print("")
        print("STEP 6: KEY GENERATION AT DESTINATION ",dest)
        print(self.key_B)
        print("lenkey****",len(self.key_B))
        BB84.KeyB=''.join(str(item) for item in self.key_B)

        #comparing two keys and find errorbits and QBER
        if(len(BB84.KeyB)==len(BB84.KeyA)):
            for i,j in zip(BB84.KeyA,BB84.KeyB):
                if(i!=j):
                    errorbit.append(i)
                else:
                    exit

            print("ERROR BIT  ",errorbit)
        
        print("length of error bit ",len(errorbit))
        qber=(len(errorbit)/len(bobmeasuredbit)*100)
        print("QBER  ",qber)
        
        BB84.Qber=round(qber,2)

        return self.key_B

    #storing ports in two dimensional array corresponding to each link
    def setTxPorts(self):
        ###0 switch_b
        connected_ports[0][0]=self.port_switchbC2
        connected_ports[0][1]=self.port_switchbC1
        connected_ports[0][2]=self.port_switchbC3
        connected_ports[0][3]=self.port_switchbC4
        
        ###1 switch_c
        connected_ports[1][0]=self.port_switchcC1
        connected_ports[1][1]=self.port_switchcC2
        connected_ports[1][2]=self.port_switchcC3

         ###2 switch_d
        connected_ports[2][0]=self.port_switchdC1
        connected_ports[2][1]=self.port_switchdC2
        connected_ports[2][2]=self.port_switchdC3
          
        ###3 switch_e
        connected_ports[3][0]=self.port_eC1
        connected_ports[3][1]=self.port_eC2
        connected_ports[3][2]=self.port_eC3
        
    #storing nodes  in two dimensional array 
    def setDestnode(self):
        ##switch_b
        connected_nodes[0][0]=self.node_a
        connected_nodes[0][1]=self.node_b
        connected_nodes[0][2]=self.node_c,self.node_f
        connected_nodes[0][3]=self.node_d,self.node_f

        ##switch_c
        connected_nodes[1][0]=self.node_b,self.node_a
        connected_nodes[1][1]=self.node_c
        connected_nodes[1][2]=self.node_f

        ##switch_d
        connected_nodes[2][0]=self.node_b,self.node_a
        connected_nodes[2][1]=self.node_d
        connected_nodes[2][2]=self.node_f

        ##switch_e
        connected_nodes[3][0]=self.node_a,self.node_b,self.node_c
        connected_nodes[3][1]=self.node_a,self.node_b,self.node_d
        connected_nodes[3][2]=self.node_f

    def get_switch_index(self,switch_name):
        for index, value in enumerate(switches):
            if value == switch_name:
                return index
                break
            else: # no break
                #print('not found')
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
        nodename=[]

        try:
            hnw.add_node("node_a")
            hnw.add_node("node_b")
            hnw.add_node("node_c")
            hnw.add_node("node_d")
            hnw.add_node("node_f")
            hnw.add_node("switch_c")
            hnw.add_node("switch_b")
            hnw.add_node("switch_d")
            hnw.add_node("switch_e")
        except:
            print("Node Already in Network")

        self.sourcenode = hnw.get_node(source)
        sor=self.sourcenode
        self.destinationnode = hnw.get_node(destination)
        dest=self.destinationnode
       
        self.switch_b = hnw.get_node("switch_b")
        self.switch_c = hnw.get_node("switch_c")
        self.switch_d = hnw.get_node("switch_d")
        self.switch_e = hnw.get_node("switch_e")
        
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
        print("MODEL  ",model)
        self.incoming_links=[]
        self.outgoing_links=[]
      
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
            
            
            source=self.source
            destination=self.destination
            given_path=[]
            given_path=link_path
                        
            if(source=="node_a" and destination=="node_f" and given_path==['AB','BC','CF'] or given_path==['AB','CB','CF']):
                ##A TO F via C
                print("PROVISIONING PATH IS READY ")
                BB84.switchaf=[self.switch_b,self.switch_c,self.switch_e]
                self.switch_b.ports[self.port_switchb1].forward_input(self.switch_b.ports[self.port_switchb4])
                self.switch_c.ports[self.port_switchc1].forward_input(self.switch_c.ports[self.port_switchc4])
                self.switch_e.ports[self.port_e1].forward_input(self.switch_e.ports[self.port_e3])

                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_1")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_e"),  label="classical_1")
                self.tmp2port,self.sourceclassicalport = hnw.get_connected_ports(hnw.get_node("switch_b"),self.sourcenode, label="classical_4")

            elif(source=="node_a" and destination=="node_b" and given_path==['AB'] ):
                print("PROVISIONING PATH IS READY ")

                self.switch_b.ports[self.port_switchb1].forward_input(self.switch_b.ports[self.port_switchb2])
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_1")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node('switch_b'), label="classical_2AB")
                self.tmp2port,self.sourceclassicalport = hnw.get_connected_ports(hnw.get_node('switch_b'),self.sourcenode,label="classical_4")

            
            elif(source=="node_a" and destination=="node_f" and given_path==['AB','BD','DF'] or given_path==['AB','DB','DF'] ):####via D
                print("PROVISIONING PATH IS READY ")
                BB84.switchaf=[self.switch_b,self.switch_d,self.switch_e]
                self.switch_b.ports[self.port_switchb1].forward_input(self.switch_b.ports[self.port_switchb5])
                self.switch_d.ports[self.port_switchd1].forward_input(self.switch_d.ports[self.port_switchd4])
                self.switch_e.ports[self.port_e2].forward_input(self.switch_e.ports[self.port_e3])
                
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_1")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_e"),  label="classical_1")
                self.tmp2port,self.sourceclassicalport = hnw.get_connected_ports(hnw.get_node("switch_b"),self.sourcenode, label="classical_4")
            
            elif(source=="node_a" and destination=="node_c" and given_path==['AB','BC'] or given_path==['AB','CB'] ):
                ##A TO C
                print("PROVISIONING PATH IS READY ")

                self.switch_b.ports[self.port_switchb1].forward_input(self.switch_b.ports[self.port_switchb4])
                self.switch_c.ports[self.port_switchc1].forward_input(self.switch_c.ports[self.port_switchc2])
                
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_1")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_c"),  label="classical_1AC")
                self.tmp2port,self.sourceclassicalport = hnw.get_connected_ports(hnw.get_node("switch_b"),self.sourcenode, label="classical_4")

            elif(source=="node_a" and destination=="node_d"  and given_path==['AB','BD'] or given_path==['AB','DB']):
                ##A TO D
                print("PROVISIONING PATH IS READY ")

                self.switch_b.ports[self.port_switchb1].forward_input(self.switch_b.ports[self.port_switchb5])
                self.switch_d.ports[self.port_switchd1].forward_input(self.switch_d.ports[self.port_switchd2])
                
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_1")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_d"),  label="classical_3DD")
                self.tmp2port,self.sourceclassicalport = hnw.get_connected_ports(hnw.get_node("switch_b"),self.sourcenode, label="classical_4")
            
            elif(source=="node_b" and destination=="node_c" and given_path==['BC'] or given_path==['CB']):
                ##B TO C
                print("PROVISIONING PATH IS READY Via C")

                self.switch_b.ports[self.port_switchb3].forward_input(self.switch_b.ports[self.port_switchb4])
                self.switch_c.ports[self.port_switchc1].forward_input(self.switch_c.ports[self.port_switchc2])

                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_3AB")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_c"),  label="classical_1AC")
                self.sourceclassicalport,self.tmp2port = hnw.get_connected_ports(self.sourcenode,hnw.get_node("switch_b"), label="classical_2AB")

            elif(source=="node_b" and destination=="node_f" and given_path==['BC','CF'] or given_path==['CB','CF']):
                ##B TO F via C
                print("PROVISIONING PATH IS READY ")

                self.switch_b.ports[self.port_switchb3].forward_input(self.switch_b.ports[self.port_switchb4])
                self.switch_c.ports[self.port_switchc1].forward_input(self.switch_c.ports[self.port_switchc4])
                self.switch_e.ports[self.port_e1].forward_input(self.switch_e.ports[self.port_e3])
                                
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_3AB")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_e"),  label="classical_1")
                self.sourceclassicalport,self.tmp2port = hnw.get_connected_ports(self.sourcenode,hnw.get_node("switch_b"), label="classical_2AB")
            
            elif(source=="node_c" and destination=="node_f" and given_path==['CF']):
                ##C TO F  
                print("PROVISIONING PATH IS READY")
              
                self.switch_c.ports[self.port_switchc3].forward_input(self.switch_c.ports[self.port_switchc4])
                self.switch_e.ports[self.port_e1].forward_input(self.switch_e.ports[self.port_e3])

                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_c'),label="quantum_4CC")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_e"),  label="classical_1")
                self.sourceclassicalport,self.tmp2port = hnw.get_connected_ports(self.sourcenode,hnw.get_node("switch_c"), label="classical_1AC")

            elif(source=="node_b" and destination=="node_d" and given_path==['BD'] or given_path==['DB']):
                print("PROVISIONING PATH IS READY")
                self.switch_b.ports[self.port_switchb3].forward_input(self.switch_b.ports[self.port_switchb5])
                self.switch_d.ports[self.port_switchd1].forward_input(self.switch_d.ports[self.port_switchd2])

                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_3AB")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_d"),  label="classical_3DD")
                self.sourceclassicalport,self.tmp2port = hnw.get_connected_ports(self.sourcenode,hnw.get_node("switch_b"), label="classical_2AB")
            
            elif(source=="node_d" and destination=="node_f"  and given_path==['DF']):

                ##D TO F
                print("PROVISIONING PATH IS READY")

                self.switch_d.ports[self.port_switchd3].forward_input(self.switch_d.ports[self.port_switchd4])
                self.switch_e.ports[self.port_e2].forward_input(self.switch_e.ports[self.port_e3])
                
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_d'),label="quantum_3cDD")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_e"),  label="classical_1")
                self.sourceclassicalport,self.tmp2port = hnw.get_connected_ports(self.sourcenode,hnw.get_node("switch_d"), label="classical_3DD")

            elif(source=="node_b" and destination=="node_f" and given_path==['BD','DF'] or given_path==['DB','DF'] ):##via D
                print("PROVISIONING PATH IS READY")
                print("PROVISIONING PATH VIA D")

                self.switch_b.ports[self.port_switchb3].forward_input(self.switch_b.ports[self.port_switchb5])
                self.switch_d.ports[self.port_switchd1].forward_input(self.switch_d.ports[self.port_switchd4])
                self.switch_e.ports[self.port_e2].forward_input(self.switch_e.ports[self.port_e3])
                                
                self.sourceport, self.tmpport =  hnw.get_connected_ports(self.sourcenode, hnw.get_node('switch_b'),label="quantum_3AB")
                self.destinationport,self.tmp1port = hnw.get_connected_ports(self.destinationnode,hnw.get_node("switch_e"),  label="classical_1")
                self.sourceclassicalport,self.tmp2port = hnw.get_connected_ports(self.sourcenode,hnw.get_node("switch_b"), label="classical_2AB")
        
    def get_nodes(self):
        global switches 
        self.node_a = hnw.get_node("node_a")
        self.node_b = hnw.get_node("node_b")
        self.node_c = hnw.get_node("node_c")
        self.node_d = hnw.get_node("node_d")
        self.node_f = hnw.get_node("node_f")
                
        self.switch_b = hnw.get_node("switch_b")
        self.switch_c = hnw.get_node("switch_c")
        self.switch_d = hnw.get_node("switch_d")
        self.switch_e = hnw.get_node("switch_e")
        
        switches =[self.switch_b,self.switch_c,self.switch_d,self.switch_e]  


    def setup_connection(self):
        
        print("TOPOLOGY SIMULATED ")
        print("self.fibre_loss_length ",self.fibre_loss_length)
        print("self.fibre_loss_init ",self.fibre_loss_init)
        print("length ",self.fiberLenth)
        print("MODEL ",model)
        if(model=="BB84FibreLossModel"):
            self.MyQfiber=QuantumChannel("QFibre_A->B", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)     
            self.MyQfiber1=QuantumChannel("QFibre_A1->B1", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber2=QuantumChannel("QFibre_SB->SC", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber3=QuantumChannel("QFibre_SC->C", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber4=QuantumChannel("QFibre_SC->SE", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber5=QuantumChannel("QFibre_SE->F", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber6=QuantumChannel("QFibre_SB->SD", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber7=QuantumChannel("QFibre_SD->D", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber8=QuantumChannel("QFibre_B->SB", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber9=QuantumChannel("QFibre_C->SC", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber10=QuantumChannel("QFibre_D->SD", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            self.MyQfiber11=QuantumChannel("QFibre_SD->SE", length=self.fiberLenth, models={"quantum_loss_model":BB84FibreLossModel(p_loss_length=self.fibre_loss_length,p_loss_init=self.fibre_loss_init)}, 
            depolar_rate=0)
            hnw.add_quantumconnection("node_a", "switch_b", label="quantum_1",  channel_to=self.MyQfiber,  bidirectional="", port_name_node1="", port_name_node2="",ip="127.0.0.1", port="7070")
            self.port_a1, self.port_switchb1 = hnw.get_connected_ports("node_a", "switch_b", label="quantum_1")
            
            hnw.add_quantumconnection("switch_b", "switch_c", label="quantum_2", channel_to=self.MyQfiber2,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchb4, self.port_switchc1 = hnw.get_connected_ports("switch_b", "switch_c", label="quantum_2")
            
            hnw.add_quantumconnection("switch_c", "switch_e",  label="quantum_3",  channel_to=self.MyQfiber4,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchc4, self.port_e1 = hnw.get_connected_ports("switch_c", "switch_e", label="quantum_3")       
            
            
            hnw.add_quantumconnection("switch_b", "node_b", label="quantum_2AB", channel_to=self.MyQfiber1, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchb2, self.port_b1 = hnw.get_connected_ports("switch_b", "node_b", label="quantum_2AB")
            
            hnw.add_quantumconnection("node_b", "switch_b", label="quantum_3AB", channel_to=self.MyQfiber8,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_b2,self.port_switchb3  = hnw.get_connected_ports("node_b", "switch_b", label="quantum_3AB")
            
            hnw.add_quantumconnection("switch_d", "node_d",label="quantum_3AD", channel_to=self.MyQfiber7, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchd2, self.port_d1 = hnw.get_connected_ports("switch_d", "node_d", label="quantum_3AD")
            
            hnw.add_quantumconnection("node_d", "switch_d",label="quantum_3cDD", channel_to=self.MyQfiber10, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_d2,self.port_switchd3  = hnw.get_connected_ports("node_d", "switch_d", label="quantum_3cDD")
            
            hnw.add_quantumconnection("switch_b", "switch_d", label="quantum_2AD", channel_to=self.MyQfiber6,bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchb5, self.port_switchd1 = hnw.get_connected_ports("switch_b", "switch_d", label="quantum_2AD")
            
            hnw.add_quantumconnection("switch_d", "switch_e",label="quantum_3DE",channel_to=self.MyQfiber11,bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchd4, self.port_e2 = hnw.get_connected_ports("switch_d", "switch_e", label="quantum_3DE")       
            
            hnw.add_quantumconnection("switch_e", "node_f",  label="quantum_4EF",  channel_to=self.MyQfiber5,bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_e3, self.port_f1 = hnw.get_connected_ports("switch_e", "node_f", label="quantum_4EF")
            
            hnw.add_quantumconnection("switch_c", "node_c", label="quantum_4AC",channel_to=self.MyQfiber3, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchc2, self.port_c1 = hnw.get_connected_ports("switch_c", "node_c", label="quantum_4AC")

            hnw.add_quantumconnection("node_c", "switch_c", label="quantum_4CC",channel_to=self.MyQfiber9, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_c2,self.port_switchc3= hnw.get_connected_ports("node_c","switch_c",  label="quantum_4CC")
        elif(model==""):
            self.MyQfiber=QuantumChannel("QFibre_A->B", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)     
            self.MyQfiber1=QuantumChannel("QFibre_A1->B1", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber2=QuantumChannel("QFibre_SB->SC", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber3=QuantumChannel("QFibre_SC->C", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber4=QuantumChannel("QFibre_SC->SE", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber5=QuantumChannel("QFibre_SE->F", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber6=QuantumChannel("QFibre_SB->SD", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber7=QuantumChannel("QFibre_SD->D", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber8=QuantumChannel("QFibre_B->SB", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber9=QuantumChannel("QFibre_C->SC", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber10=QuantumChannel("QFibre_D->SD", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            self.MyQfiber11=QuantumChannel("QFibre_SD->SE", length=self.fiberLenth, models={"quantum_loss_model":None}, 
            depolar_rate=0)
            hnw.add_quantumconnection("node_a", "switch_b", label="quantum_1",  channel_to=self.MyQfiber,  bidirectional="", port_name_node1="", port_name_node2="",ip="127.0.0.1", port="7070")
            self.port_a1, self.port_switchb1 = hnw.get_connected_ports("node_a", "switch_b", label="quantum_1")
            
            hnw.add_quantumconnection("switch_b", "switch_c", label="quantum_2", channel_to=self.MyQfiber2,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchb4, self.port_switchc1 = hnw.get_connected_ports("switch_b", "switch_c", label="quantum_2")
            
            hnw.add_quantumconnection("switch_c", "switch_e",  label="quantum_3",  channel_to=self.MyQfiber4,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchc4, self.port_e1 = hnw.get_connected_ports("switch_c", "switch_e", label="quantum_3")       
            
            hnw.add_quantumconnection("switch_b", "node_b", label="quantum_2AB", channel_to=self.MyQfiber1, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchb2, self.port_b1 = hnw.get_connected_ports("switch_b", "node_b", label="quantum_2AB")
            
            hnw.add_quantumconnection("node_b", "switch_b", label="quantum_3AB", channel_to=self.MyQfiber8,  bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_b2,self.port_switchb3  = hnw.get_connected_ports("node_b", "switch_b", label="quantum_3AB")
            
            hnw.add_quantumconnection("switch_d", "node_d",label="quantum_3AD", channel_to=self.MyQfiber7, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchd2, self.port_d1 = hnw.get_connected_ports("switch_d", "node_d", label="quantum_3AD")
            
            hnw.add_quantumconnection("node_d", "switch_d",label="quantum_3cDD", channel_to=self.MyQfiber10, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_d2,self.port_switchd3  = hnw.get_connected_ports("node_d", "switch_d", label="quantum_3cDD")
            
            hnw.add_quantumconnection("switch_b", "switch_d", label="quantum_2AD", channel_to=self.MyQfiber6,bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchb5, self.port_switchd1 = hnw.get_connected_ports("switch_b", "switch_d", label="quantum_2AD")
            
            hnw.add_quantumconnection("switch_d", "switch_e",label="quantum_3DE",channel_to=self.MyQfiber11,bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchd4, self.port_e2 = hnw.get_connected_ports("switch_d", "switch_e", label="quantum_3DE")       
            
            hnw.add_quantumconnection("switch_e", "node_f",  label="quantum_4EF",  channel_to=self.MyQfiber5,bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_e3, self.port_f1 = hnw.get_connected_ports("switch_e", "node_f", label="quantum_4EF")
            
            hnw.add_quantumconnection("switch_c", "node_c", label="quantum_4AC",channel_to=self.MyQfiber3, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_switchc2, self.port_c1 = hnw.get_connected_ports("switch_c", "node_c", label="quantum_4AC")

            hnw.add_quantumconnection("node_c", "switch_c", label="quantum_4CC",channel_to=self.MyQfiber9, bidirectional="", port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
            self.port_c2,self.port_switchc3= hnw.get_connected_ports("node_c","switch_c",  label="quantum_4CC")

        hnw.add_connection("switch_b", "node_a", delay=(1,4), label="classical_1AB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchbC2,self.port_Ca  = hnw.get_connected_ports("switch_b","node_a", label="classical_1AB")

        hnw.add_connection("node_b","switch_b",  delay=(1,4), label="classical_2AB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Cb,self.port_switchbC1  = hnw.get_connected_ports("node_b","switch_b", label="classical_2AB")

        hnw.add_connection("node_f", "switch_e", delay=(1,4), label="classical_1", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_fC1, self.port_eC3 = hnw.get_connected_ports("node_f", "switch_e", label="classical_1")

        hnw.add_connection("switch_e","switch_c", delay=(1,4), label="classical_2", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_eC1, self.port_switchcC3 = hnw.get_connected_ports("switch_e", "switch_c", label="classical_2")

        hnw.add_connection("switch_c", "switch_b", delay=(1,4), label="classical_3", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchcC1, self.port_switchbC3= hnw.get_connected_ports("switch_c", "switch_b", label="classical_3")

        hnw.add_connection("switch_b", "node_a", delay=(1,4), label="classical_4", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchbC2, self.port_Ca = hnw.get_connected_ports("switch_b", "node_a", label="classical_4")

        hnw.add_connection("node_d", "switch_d", delay=(1,4), label="classical_3DD", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Cd, self.port_switchdC2= hnw.get_connected_ports("node_d", "switch_d", label="classical_3DD")

        hnw.add_connection("switch_e","switch_d", delay=(1,4), label="classical_2ED", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_eC2, self.port_switchdC3 = hnw.get_connected_ports("switch_e", "switch_d", label="classical_2ED")

        hnw.add_connection("switch_d", "switch_b", delay=(1,4), label="classical_3DB", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_switchdC1, self.port_switchbC4= hnw.get_connected_ports("switch_d", "switch_b", label="classical_3DB")

        hnw.add_connection("node_c", "switch_c", delay=(1,4), label="classical_1AC", connection="", channel_to=(""), channel_from=(""), bidirectional=True, port_name_node1="", port_name_node2="", ip="127.0.0.1", port="7070")
        self.port_Cc, self.port_switchcC2 = hnw.get_connected_ports("node_c", "switch_c", label="classical_1AC")
        
       
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
        self.switch_b.ports[self.port_switchb4].bind_input_handler(handler_b2q)
        
        handler_c2q = lambda qlist: self.switch_c.ports[self.port_switchc4].tx_output(qlist)
        self.switch_c.ports[self.port_switchc4].bind_input_handler(handler_c2q)

        handler_e2q = lambda qlist: self.switch_e.ports[self.port_e3].tx_output(qlist)
        self.switch_e.ports[self.port_e3].bind_input_handler(handler_e2q)
        
        handler_b2qAB = lambda qlist: self.switch_b.ports[self.port_switchb2].tx_output(qlist)
        self.switch_b.ports[self.port_switchb2].bind_input_handler(handler_b2qAB)

        handler_b2q = lambda qlist: self.switch_b.ports[self.port_switchb5].tx_output(qlist)
        self.switch_b.ports[self.port_switchb5].bind_input_handler(handler_b2q)


        handler_d2q = lambda qlist: self.switch_d.ports[self.port_switchd4].tx_output(qlist)
        self.switch_d.ports[self.port_switchd4].bind_input_handler(handler_d2q)

        handler_e2q = lambda qlist: self.switch_e.ports[self.port_e3].tx_output(qlist)
        self.switch_e.ports[self.port_e3].bind_input_handler(handler_e2q)

##A TO C
        handler_c2qAC = lambda qlist: self.switch_c.ports[self.port_switchc2].tx_output(qlist)
        self.switch_c.ports[self.port_switchc2].bind_input_handler(handler_c2qAC)

###A TO D

        handler_d2qDD = lambda qlist: self.switch_d.ports[self.port_switchd2].tx_output(qlist)
        self.switch_d.ports[self.port_switchd2].bind_input_handler(handler_d2qDD)

        self.node_f.ports[self.port_f1].bind_input_handler(self.BB84_Bob_measure_send)## A TO F
        self.node_c.ports[self.port_c1].bind_input_handler(self.BB84_Bob_measure_send)## A TO C
        self.node_b.ports[self.port_b1].bind_input_handler(self.BB84_Bob_measure_send)##A TO B
        self.node_d.ports[self.port_d1].bind_input_handler(self.BB84_Bob_measure_send)##A TO D

        
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
            print("switchaf",BB84.switchaf)
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
        s=self.source
        d=self.destination
        switch_index = self.get_switch_index(self.switch_b)
        switch_index1 = self.get_switch_index(self.switch_c)
        switch_index2 = self.get_switch_index(self.switch_e)
        switch_index3 = self.get_switch_index(self.switch_d)

        if(s=="node_a" and d=="node_b"):

            port_index = self.get_port(switch_index, hnw.get_node(s))
            switch_index = self.get_switch_index(self.switch_b)
            port_index1 = self.get_port(switch_index, hnw.get_node(d))
            handler_1 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index[0])].tx_output(Bobbasis)
            self.switch_b.ports[self.port_switchbC1].bind_input_handler(handler_1)
            handler_2 = lambda matchList: self.switch_b.ports[self.get_port_name(switch_index,port_index1[0])].tx_output(matchList)
            self.switch_b.ports[self.port_switchbC2].bind_input_handler(handler_2)
   
        elif(s=="node_a" and d=="node_c"):
            
            port_index2 = self.get_port(switch_index1, hnw.get_node(s))
            handler_3 = lambda Bobbasis: self.switch_c.ports[self.get_port_name(switch_index1,port_index2[0])].tx_output(Bobbasis)
            self.switch_c.ports[self.port_switchcC2].bind_input_handler(handler_3)
            
            port_index3 = self.get_port(switch_index, hnw.get_node(s))
            print("<<< START >>>> Port index3 : ", port_index3)
            handler_4 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index3[0])].tx_output(Bobbasis)
            self.switch_b.ports[self.port_switchbC3].bind_input_handler(handler_4)
            

            port_index4=self.get_port(switch_index,hnw.get_node(d))
            print("port_index4",port_index4)

            handler_5=lambda matchList:self.switch_b.ports[self.get_port_name(switch_index,port_index4[0])].tx_output(matchList)

            self.switch_b.ports[self.port_switchbC2].bind_input_handler(handler_5)
            
            port_index5=self.get_port(switch_index1,hnw.get_node(d))
            
            handler_6=lambda matchList:self.switch_c.ports[self.get_port_name(switch_index1,port_index5[0])].tx_output(matchList)
            self.switch_c.ports[self.port_switchcC1].bind_input_handler(handler_6)


        elif(s=="node_a" and d=="node_f"):
            
            port_index6 = self.get_port(switch_index2, hnw.get_node(s))
            handler_7 = lambda Bobbasis: self.switch_e.ports[self.get_port_name(switch_index2,port_index6[0])].tx_output(Bobbasis)
            self.switch_e.ports[self.port_eC3].bind_input_handler(handler_7)
            port_index2 = self.get_port(switch_index1, hnw.get_node(s))
            handler_3 = lambda Bobbasis: self.switch_c.ports[self.get_port_name(switch_index1,port_index2[0])].tx_output(Bobbasis)

            self.switch_c.ports[self.port_switchcC3].bind_input_handler(handler_3)
            port_index3 = self.get_port(switch_index, hnw.get_node(s))
            handler_4 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index3[0])].tx_output(Bobbasis)
            self.switch_b.ports[self.port_switchbC3].bind_input_handler(handler_4)

            port_index8=self.get_port(switch_index,hnw.get_node(d))
            handler_5=lambda matchList:self.switch_b.ports[self.get_port_name(switch_index,port_index8[0])].tx_output(matchList)
            
            self.switch_b.ports[self.port_switchbC2].bind_input_handler(handler_5)

            port_index7 = self.get_port(switch_index1, hnw.get_node(d))
            handler_8=lambda matchList:self.switch_c.ports[self.get_port_name(switch_index1,port_index7[0])].tx_output(matchList)
            self.switch_c.ports[self.port_switchcC1].bind_input_handler(handler_8)

            port_index8 = self.get_port(switch_index2, hnw.get_node(d))
            handler_9=lambda matchList:self.switch_e.ports[self.get_port_name(switch_index2,port_index8[0])].tx_output(matchList)
            self.switch_e.ports[self.port_eC1].bind_input_handler(handler_9)

        elif(s=="node_a" and d=="node_d"):
            
            port_index8 = self.get_port(switch_index3, hnw.get_node(s))
            handler_10 = lambda Bobbasis: self.switch_d.ports[self.get_port_name(switch_index3,port_index8[0])].tx_output(Bobbasis)
            self.switch_d.ports[self.port_switchdC2].bind_input_handler(handler_10)

            port_index9 = self.get_port(switch_index, hnw.get_node(s))
            handler_11 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index9[0])].tx_output(Bobbasis)
            self.switch_b.ports[self.port_switchbC4].bind_input_handler(handler_11)

            port_index10 = self.get_port(switch_index, hnw.get_node(d))
            handler_11 = lambda matchList: self.switch_b.ports[self.get_port_name(switch_index,port_index10[0])].tx_output(matchList)
            self.switch_b.ports[self.port_switchbC2].bind_input_handler(handler_11)

            port_index11 = self.get_port(switch_index3, hnw.get_node(d))
            handler_12 = lambda matchList: self.switch_d.ports[self.get_port_name(switch_index3,port_index11[0])].tx_output(matchList)
            self.switch_d.ports[self.port_switchdC1].bind_input_handler(handler_12)

        elif(s=="node_b" and d=="node_d"):
            
            port_index12 = self.get_port(switch_index3, hnw.get_node(s))
            handler_13 = lambda Bobbasis: self.switch_d.ports[self.get_port_name(switch_index3,port_index12[0])].tx_output(Bobbasis)
            
            self.switch_d.ports[self.port_switchdC2].bind_input_handler(handler_13)

            port_index13 = self.get_port(switch_index, hnw.get_node(s))
            handler_14 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index13[0])].tx_output(Bobbasis)
            
            self.switch_b.ports[self.port_switchbC4].bind_input_handler(handler_14)
            
            port_index10 = self.get_port(switch_index, hnw.get_node(d))
            handler_15 = lambda matchList: self.switch_b.ports[self.get_port_name(switch_index,port_index10[0])].tx_output(matchList)
            
            self.switch_b.ports[self.port_switchbC1].bind_input_handler(handler_15)

            port_index11 = self.get_port(switch_index3, hnw.get_node(d))
            handler_12 = lambda matchList: self.switch_d.ports[self.get_port_name(switch_index3,port_index11[0])].tx_output(matchList)
            self.switch_d.ports[self.port_switchdC1].bind_input_handler(handler_12)

        elif(s=="node_b" and d=="node_c"):
            
            port_index2 = self.get_port(switch_index1, hnw.get_node(s))
            handler_3 = lambda Bobbasis: self.switch_c.ports[self.get_port_name(switch_index1,port_index2[0])].tx_output(Bobbasis)
            
            self.switch_c.ports[self.port_switchcC2].bind_input_handler(handler_3)
            port_index1 = self.get_port(switch_index, hnw.get_node(s))
            handler_4 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index1[0])].tx_output(Bobbasis)

            self.switch_b.ports[self.port_switchbC3].bind_input_handler(handler_4)
            port_index3 = self.get_port(switch_index, hnw.get_node(d))
            handler_5 = lambda matchList: self.switch_b.ports[self.get_port_name(switch_index,port_index3[0])].tx_output(matchList)

            self.switch_b.ports[self.port_switchbC1].bind_input_handler(handler_5)
            port_index4 = self.get_port(switch_index1, hnw.get_node(d))
            handler_6 = lambda matchList: self.switch_c.ports[self.get_port_name(switch_index1,port_index4[0])].tx_output(matchList)

            self.switch_c.ports[self.port_switchcC1].bind_input_handler(handler_6)

        elif(s=="node_b" and d=="node_f"):
            
            port_index6 = self.get_port(switch_index2, hnw.get_node(s))
            
            handler_2 = lambda Bobbasis: self.switch_e.ports[self.get_port_name(switch_index2,port_index6[0])].tx_output(Bobbasis)
            self.switch_e.ports[self.port_eC3].bind_input_handler(handler_2)

            port_index2 = self.get_port(switch_index1, hnw.get_node(s))
            handler_3 = lambda Bobbasis: self.switch_c.ports[self.get_port_name(switch_index1,port_index2[0])].tx_output(Bobbasis)
            
            self.switch_c.ports[self.port_switchcC3].bind_input_handler(handler_3)
            port_index1 = self.get_port(switch_index, hnw.get_node(s))
            handler_4 = lambda Bobbasis: self.switch_b.ports[self.get_port_name(switch_index,port_index1[0])].tx_output(Bobbasis)

            self.switch_b.ports[self.port_switchbC3].bind_input_handler(handler_4)
            port_index3 = self.get_port(switch_index, hnw.get_node(d))
            handler_5 = lambda matchList: self.switch_b.ports[self.get_port_name(switch_index,port_index3[0])].tx_output(matchList)

            self.switch_b.ports[self.port_switchbC1].bind_input_handler(handler_5)
            port_index4 = self.get_port(switch_index1, hnw.get_node(d))
            handler_6 = lambda matchList: self.switch_c.ports[self.get_port_name(switch_index1,port_index4[0])].tx_output(matchList)

            self.switch_c.ports[self.port_switchcC1].bind_input_handler(handler_6)

            port_index8 = self.get_port(switch_index2, hnw.get_node(d))
            handler_7 = lambda matchList: self.switch_e.ports[self.get_port_name(switch_index2,port_index8[0])].tx_output(matchList)

            self.switch_e.ports[self.port_eC1].bind_input_handler(handler_7)




        elif(s=="node_c" and d=="node_f"):
            
            port_index1=self.get_port(switch_index1,hnw.get_node(s))
            handler_1=lambda Bobbasis:self.switch_c.ports[self.get_port_name(switch_index1,port_index1[0])].tx_output(Bobbasis)
            self.switch_c.ports[self.port_switchcC3].bind_input_handler(handler_1)

            port_index2=self.get_port(switch_index2,hnw.get_node(s))
            handler_2=lambda Bobbasis:self.switch_e.ports[self.get_port_name(switch_index2,port_index2[0])].tx_output(Bobbasis)
            self.switch_e.ports[self.port_eC3].bind_input_handler(handler_2)

            port_index3=self.get_port(switch_index1,hnw.get_node(d))
            handler_3=lambda matchList:self.switch_c.ports[self.get_port_name(switch_index1,port_index3[0])].tx_output(matchList)
            self.switch_c.ports[self.port_switchcC2].bind_input_handler(handler_3)

            port_index4=self.get_port(switch_index2,hnw.get_node(d))
            handler_4=lambda matchList:self.switch_e.ports[self.get_port_name(switch_index2,port_index4[0])].tx_output(matchList)
            self.switch_e.ports[self.port_eC1].bind_input_handler(handler_4)

        elif(s=="node_d" and d=="node_f"):
           
            port_index1=self.get_port(switch_index3,hnw.get_node(s))
            handler_1= lambda Bobbasis: self.switch_d.ports[self.get_port_name(switch_index3,port_index1[0])].tx_output(Bobbasis)
            self.switch_d.ports[self.port_switchdC3].bind_input_handler(handler_1)
            port_index2=self.get_port(switch_index2,hnw.get_node(s))
            handler_2= lambda Bobbasis: self.switch_e.ports[self.get_port_name(switch_index2,port_index2[0])].tx_output(Bobbasis)
            self.switch_e.ports[self.port_eC3].bind_input_handler(handler_2)

            port_index3=self.get_port(switch_index3,hnw.get_node(d))
            handler_3= lambda matchList:self.switch_d.ports[self.get_port_name(switch_index3,port_index3[0])].tx_output(matchList)
            self.switch_d.ports[self.port_switchdC2].bind_input_handler(handler_3)

            port_index4=self.get_port(switch_index2,hnw.get_node(d))
            handler_4=lambda matchList: self.switch_e.ports[self.get_port_name(switch_index2,port_index4[0])].tx_output(matchList)
            self.switch_e.ports[self.port_eC2].bind_input_handler(handler_4)
    
    def sendqubits(self):
        self.BB84_Alice_sendQubits(sor)
        
         
def startsimulation(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name):
    print("TOPOLOGY SIMULATED ")
    b=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name)
    getnodes=b.get_nodes()
    b.setup_connection()

def startquantumsimulation(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name,incominglinks,outgoinglinks,mode,command,nodeid):
    print("RECEIVING QUANTUM CHANNEL PROVISION MESSAGES ")
    global incoming_links,outgoing_links,modeofincomingnode,commandtype,node_id
 
    modeofincomingnode=mode
    commandtype=command
    node_id=nodeid
    
    b2=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name)
    b2.incoming_links.append(incominglinks)
    b2.outgoing_links.append(outgoinglinks)
    b2.get_nodes()
    b2.port_a1, b2.port_switchb1 = hnw.get_connected_ports("node_a", "switch_b", label="quantum_1")
    b2.port_switchb4, b2.port_switchc1 = hnw.get_connected_ports("switch_b", "switch_c", label="quantum_2")
    b2.port_switchc4, b2.port_e1 = hnw.get_connected_ports("switch_c", "switch_e", label="quantum_3") 
    b2.port_switchb2, b2.port_b1 = hnw.get_connected_ports("switch_b", "node_b", label="quantum_2AB")
    b2.port_b2,b2.port_switchb3  = hnw.get_connected_ports("node_b", "switch_b", label="quantum_3AB")
    b2.port_switchd2, b2.port_d1 = hnw.get_connected_ports("switch_d", "node_d", label="quantum_3AD")
    b2.port_d2,b2.port_switchd3  = hnw.get_connected_ports("node_d", "switch_d", label="quantum_3cDD")
    b2.port_switchb5, b2.port_switchd1 = hnw.get_connected_ports("switch_b", "switch_d", label="quantum_2AD")
    b2.port_switchd4, b2.port_e2 = hnw.get_connected_ports("switch_d", "switch_e", label="quantum_3DE")
    b2.port_e3, b2.port_f1 = hnw.get_connected_ports("switch_e", "node_f", label="quantum_4EF")
    b2.port_switchc2, b2.port_c1 = hnw.get_connected_ports("switch_c", "node_c", label="quantum_4AC")
    b2.port_c2,b2.port_switchc3= hnw.get_connected_ports("node_c","switch_c",  label="quantum_4CC")
    b2.port_switchbC2,b2.port_Ca  = hnw.get_connected_ports("switch_b","node_a", label="classical_1AB")
    b2.port_Cb,b2.port_switchbC1  = hnw.get_connected_ports("node_b","switch_b", label="classical_2AB")
    b2.port_fC1, b2.port_eC3 = hnw.get_connected_ports("node_f", "switch_e", label="classical_1")
    b2.port_eC1, b2.port_switchcC3 = hnw.get_connected_ports("switch_e", "switch_c", label="classical_2")
    b2.port_switchcC1, b2.port_switchbC3= hnw.get_connected_ports("switch_c", "switch_b", label="classical_3")
    b2.port_switchbC2, b2.port_Ca = hnw.get_connected_ports("switch_b", "node_a", label="classical_4")
    b2.port_Cd, b2.port_switchdC2= hnw.get_connected_ports("node_d", "switch_d", label="classical_3DD")
    b2.port_eC2, b2.port_switchdC3 = hnw.get_connected_ports("switch_e", "switch_d", label="classical_2ED")
    b2.port_switchdC1, b2.port_switchbC4= hnw.get_connected_ports("switch_d", "switch_b", label="classical_3DB")
    b2.port_Cc, b2.port_switchcC2 = hnw.get_connected_ports("node_c", "switch_c", label="classical_1AC")


def startprovision(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name,all_merged_link_ids):
    print("SIMULATION STARTED ")
    global linkinfo,link_path
    link_path=[]

    unique_lists = set(map(tuple, all_merged_link_ids if len(all_merged_link_ids) > 1 else [all_merged_link_ids]))
    if len(unique_lists)==1:
        unique_lists = list(unique_lists)
        unique_lists=unique_lists[0]
    else:
        unique_lists=all_merged_link_ids

    link_path = sorted(unique_lists)
    
    b2=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name)
    b2.get_nodes()
    
    b2.port_a1, b2.port_switchb1 = hnw.get_connected_ports("node_a", "switch_b", label="quantum_1")
    b2.port_switchb4, b2.port_switchc1 = hnw.get_connected_ports("switch_b", "switch_c", label="quantum_2")
    b2.port_switchc4, b2.port_e1 = hnw.get_connected_ports("switch_c", "switch_e", label="quantum_3") 
    b2.port_switchb2, b2.port_b1 = hnw.get_connected_ports("switch_b", "node_b", label="quantum_2AB")
    b2.port_b2,b2.port_switchb3  = hnw.get_connected_ports("node_b", "switch_b", label="quantum_3AB")
    b2.port_switchd2, b2.port_d1 = hnw.get_connected_ports("switch_d", "node_d", label="quantum_3AD")
    b2.port_d2,b2.port_switchd3  = hnw.get_connected_ports("node_d", "switch_d", label="quantum_3cDD")
    b2.port_switchb5, b2.port_switchd1 = hnw.get_connected_ports("switch_b", "switch_d", label="quantum_2AD")
    b2.port_switchd4, b2.port_e2 = hnw.get_connected_ports("switch_d", "switch_e", label="quantum_3DE")
    b2.port_e3, b2.port_f1 = hnw.get_connected_ports("switch_e", "node_f", label="quantum_4EF")
    b2.port_switchc2, b2.port_c1 = hnw.get_connected_ports("switch_c", "node_c", label="quantum_4AC")
    b2.port_c2,b2.port_switchc3= hnw.get_connected_ports("node_c","switch_c",  label="quantum_4CC")
    b2.port_switchbC2,b2.port_Ca  = hnw.get_connected_ports("switch_b","node_a", label="classical_1AB")
    b2.port_Cb,b2.port_switchbC1  = hnw.get_connected_ports("node_b","switch_b", label="classical_2AB")
    b2.port_fC1, b2.port_eC3 = hnw.get_connected_ports("node_f", "switch_e", label="classical_1")
    b2.port_eC1, b2.port_switchcC3 = hnw.get_connected_ports("switch_e", "switch_c", label="classical_2")
    b2.port_switchcC1, b2.port_switchbC3= hnw.get_connected_ports("switch_c", "switch_b", label="classical_3")
    b2.port_switchbC2, b2.port_Ca = hnw.get_connected_ports("switch_b", "node_a", label="classical_4")
    b2.port_Cd, b2.port_switchdC2= hnw.get_connected_ports("node_d", "switch_d", label="classical_3DD")
    b2.port_eC2, b2.port_switchdC3 = hnw.get_connected_ports("switch_e", "switch_d", label="classical_2ED")
    b2.port_switchdC1, b2.port_switchbC4= hnw.get_connected_ports("switch_d", "switch_b", label="classical_3DB")
    b2.port_Cc, b2.port_switchcC2 = hnw.get_connected_ports("node_c", "switch_c", label="classical_1AC")
    b2.switches_connected()
    b2.configure()
    
    b2.setTxPorts()
    b2.setDestnode()
    b2.handler_x()
    b2.sendqubits()
    b2.handlers()
    



def startreprovision(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name,all_merged_link_ids):
    print("SIMULATION STARTED ")
    global linkinfo,link_path
    link_path=[]
    unique_lists = set(map(tuple, all_merged_link_ids if len(all_merged_link_ids) > 1 else [all_merged_link_ids]))
    if len(unique_lists)==1:
        unique_lists = list(unique_lists)
        unique_lists=unique_lists[0]
    else:
        unique_lists=all_merged_link_ids

    link_path = sorted(unique_lists)
    
    b2=BB84(num_bits,fibre_len,fibre_loss_init,fibre_loss_length,fibre_lossmodel,source,destination,topology_id,topology_name)
    b2.get_nodes()
    
    b2.port_a1, b2.port_switchb1 = hnw.get_connected_ports("node_a", "switch_b", label="quantum_1")
    b2.port_switchb4, b2.port_switchc1 = hnw.get_connected_ports("switch_b", "switch_c", label="quantum_2")
    b2.port_switchc4, b2.port_e1 = hnw.get_connected_ports("switch_c", "switch_e", label="quantum_3") 
    b2.port_switchb2, b2.port_b1 = hnw.get_connected_ports("switch_b", "node_b", label="quantum_2AB")
    b2.port_b2,b2.port_switchb3  = hnw.get_connected_ports("node_b", "switch_b", label="quantum_3AB")
    b2.port_switchd2, b2.port_d1 = hnw.get_connected_ports("switch_d", "node_d", label="quantum_3AD")
    b2.port_d2,b2.port_switchd3  = hnw.get_connected_ports("node_d", "switch_d", label="quantum_3cDD")
    b2.port_switchb5, b2.port_switchd1 = hnw.get_connected_ports("switch_b", "switch_d", label="quantum_2AD")
    b2.port_switchd4, b2.port_e2 = hnw.get_connected_ports("switch_d", "switch_e", label="quantum_3DE")
    b2.port_e3, b2.port_f1 = hnw.get_connected_ports("switch_e", "node_f", label="quantum_4EF")
    b2.port_switchc2, b2.port_c1 = hnw.get_connected_ports("switch_c", "node_c", label="quantum_4AC")
    b2.port_c2,b2.port_switchc3= hnw.get_connected_ports("node_c","switch_c",  label="quantum_4CC")
    b2.port_switchbC2,b2.port_Ca  = hnw.get_connected_ports("switch_b","node_a", label="classical_1AB")
    b2.port_Cb,b2.port_switchbC1  = hnw.get_connected_ports("node_b","switch_b", label="classical_2AB")
    b2.port_fC1, b2.port_eC3 = hnw.get_connected_ports("node_f", "switch_e", label="classical_1")
    b2.port_eC1, b2.port_switchcC3 = hnw.get_connected_ports("switch_e", "switch_c", label="classical_2")
    b2.port_switchcC1, b2.port_switchbC3= hnw.get_connected_ports("switch_c", "switch_b", label="classical_3")
    b2.port_switchbC2, b2.port_Ca = hnw.get_connected_ports("switch_b", "node_a", label="classical_4")
    b2.port_Cd, b2.port_switchdC2= hnw.get_connected_ports("node_d", "switch_d", label="classical_3DD")
    b2.port_eC2, b2.port_switchdC3 = hnw.get_connected_ports("switch_e", "switch_d", label="classical_2ED")
    b2.port_switchdC1, b2.port_switchbC4= hnw.get_connected_ports("switch_d", "switch_b", label="classical_3DB")
    b2.port_Cc, b2.port_switchcC2 = hnw.get_connected_ports("node_c", "switch_c", label="classical_1AC")
    b2.switches_connected()
    b2.configure()
    
    b2.setTxPorts()
    b2.setDestnode()
    b2.handler_x()
    b2.sendqubits()
    b2.handlers()
    
# if there's a qubit loss, both opList and loc_res_measure will have value 2 in the such slot in the list
def Random_ZX_measure(num_bits,qlist):
    opList = [2]*num_bits
    loc_res_measure=[2]*num_bits
    for q in qlist:
        rbit = randint(0,1)
        num=int(q.name[1:]) 
        opList[num] = rbit
        if rbit==0:
            loc_res_measure[num]=ns.qubits.qubitapi.measure(q,observable=Z) #measure in standard basis
        elif rbit==1:
            loc_res_measure[num]=ns.qubits.qubitapi.measure(q,observable=X) #measure in Hadamard basis
        else:
            print("Measuring - ERROR\n")
    return opList,loc_res_measure

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





