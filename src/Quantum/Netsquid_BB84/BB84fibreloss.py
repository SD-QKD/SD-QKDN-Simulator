########################################################################
# 
# File Name: BB84fibreloss.py
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 30/12/2022
# 
# Purpose : Introducing error in quantum channel
# 
# Description : Customized fibreloss error model 
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
import netsquid as ns
import math
import netsquid.qubits.qubitapi as qapi
import netsquid.util.simtools as simtools
from netsquid.util.simlog import warn_deprecated
import numpy as np
from netsquid.components.models.errormodels import ErrorModel
from netsquid.qubits.operators import *
from netsquid.components.models.qerrormodels import QuantumErrorModel
from netsquid.qubits.qubit import Qubit
from random import randint, random, sample
from netsquid.components.models.qerrormodels import FibreLossModel

class BB84FibreLossModel(FibreLossModel):

    def __init__(self, p_loss_init, p_loss_length, rng=None):
        super().__init__()
        self.p_loss_init = p_loss_init
        self.p_loss_length = p_loss_length
        self.rng = rng if rng else simtools.get_random_state()
        self.required_properties = ["length"]
      
    @property
    def rng(self):
        super.rng()
        return self.properties['rng']

    @rng.setter
    def rng(self, value):
        #super.rng(value)
        if not isinstance(value, np.random.RandomState):
            raise TypeError("{} is not a valid numpy RandomState".format(value))
        self.properties['rng'] = value

    @property
    def p_loss_init(self):
        #super.p_loss_init()
        return self.properties['p_loss_init']

    @p_loss_init.setter
    def p_loss_init(self, value):
        #super.p_loss_init()
        if not 0 <= value <= 1:
            raise ValueError
        self.properties['p_loss_init'] = value

    @property
    def p_loss_length(self):
        #super.p_loss_length()
        return self.properties['p_loss_length']

    @p_loss_length.setter
    def p_loss_length(self, value):
        #super.p_loss_length()
        if value < 0:
            raise ValueError
        self.properties['p_loss_length'] = value
    

    def error_operation(self, qubits, delta_time=0, **kwargs):

        if 'channel' in kwargs:
            warn_deprecated("channel parameter is deprecated. "
                            "Pass length parameter directly instead.",
                            key="FibreLossModel.compute_model.channel")
            kwargs['length'] = kwargs['channel'].properties["length"]
            del kwargs['channel']
        for idx, qubit in enumerate(qubits):
            if qubit is None:
                continue
            
            prob_loss = 1 - (1 - self.p_loss_init) * np.power(10, - kwargs['length'] * self.p_loss_length / 10)
            
            ns.qubits.amplitude_dampen(qubit,gamma=prob_loss,prob=0.5)
            
            self.lose_qubit(qubits, idx, prob_loss, rng=self.properties['rng'])

    def prob_item_lost(self, item, delta_time=0, **kwargs):
        super.prob_item_lost(self, item, delta_time=0, **kwargs)
        return 1 - (1 - self.p_loss_init) * np.power(10, - kwargs['length'] * self.p_loss_length / 10)

    
