class Linkinfo():
    def __init__(self,incoming_link_details,outgoing_link_details,mode,command,node_id):
        self.incoming_link_details=incoming_link_details
        self.outgoing_link_details=outgoing_link_details
        self.mode=mode
        self.command=command
        self.node_id=node_id  

    def __str__(self):
        return f"Incoming Links: {self.incoming_link_details}, Outgoing Links: {self.outgoing_link_details}"
    def reset(self):
        self.incoming_link_details=[]
        self.outgoing_link_details=[]