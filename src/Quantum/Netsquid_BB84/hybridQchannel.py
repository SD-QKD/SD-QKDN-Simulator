import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.nodes.connections import DirectConnection
from netsquid.components import QuantumChannel
from netsquid.qubits import create_qubits
from netsquid.qubits.operators import *
from random import randint

class QLinkparameter():
    def __init__(self,length,numbits,lossmodel,ploss_init,ploss_length):
      
        self.length=length
        self.numbits=numbits
        self.lossmodel=lossmodel
        self.ploss_init=ploss_init
        self.ploss_length=ploss_length
        