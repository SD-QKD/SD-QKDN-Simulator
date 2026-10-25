import numpy as np
import netsquid as ns
from netsquid.nodes.node import Node
from netsquid.nodes.connections import DirectConnection
from netsquid.components import QuantumChannel
from netsquid.qubits import create_qubits
from netsquid.qubits.operators import *
from random import randint

class Provision():
    def __init__(self,sourcep,destp):
        self.sourcep=sourcep
        self.destp=destp
        