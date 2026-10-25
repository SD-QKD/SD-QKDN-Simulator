########################################################################
# 
# File Name: hybridGeneralparameter.py
# 
######################################################################## 
# 
# Project Name : MAQAN
# 
# Project Code : CGS030D
# 
# Created : 30/12/2022
# 
# Purpose : for sending general parameters from netsquid to ns3
# 
# Description : Contains list of general parameters 
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
class Generalparameters():
    def __init__(self,sourceip,destinationip):
        self.sourceip=sourceip
        self.destinationip=destinationip
