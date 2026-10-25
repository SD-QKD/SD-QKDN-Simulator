import array as arr
import requests
import json
import random as rand
import time
import os
from flask import Flask, json, url_for, request, abort, jsonify
from json import JSONEncoder

# =============================================================================
# SEQUENCE IMPORTS (REPLACING NETSQUID)
# =============================================================================

from sequence.kernel.timeline import Timeline
from sequence.topology.node import Node as SeqNode
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.topology.topology import Topology as SeqTopology

# =============================================================================
# HYBRID NETWORK CLASS (SEQUENCE-BASED)
# =============================================================================

class HybridNode:
    """
    Wrapper class for SeQUeNCe nodes in hybrid network
    Replaces NetSquid Node functionality
    """
    
    def __init__(self, name: str, timeline: Timeline = None):
        self.name = name
        self.timeline = timeline
        self.qkd_node = None
        self.connections = {}
        self.quantum_memory = None
        self.classical_channels = {}
        self.quantum_channels = {}
        
        if timeline:
            self.qkd_node = QKDNode(name, timeline, stack_size=2)
    
    def add_connection(self, other_node_name: str, channel):
        """Add connection to another node"""
        self.connections[other_node_name] = channel
    
    def get_qkd_node(self) -> QKDNode:
        """Get underlying SeQUeNCe QKD node"""
        return self.qkd_node


class HybridConnection:
    """
    Wrapper class for connections in hybrid network
    Replaces NetSquid Connection functionality
    """
    
    def __init__(self, name: str, node1: str, node2: str, 
                 channel_type: str = "classical", timeline: Timeline = None):
        self.name = name
        self.node1 = node1
        self.node2 = node2
        self.channel_type = channel_type
        self.timeline = timeline
        self.channel = None
        
    def setup_channel(self, distance: float = 1000, attenuation: float = 0.0002):
        """Setup the underlying channel"""
        if self.timeline is None:
            return
            
        if self.channel_type == "quantum":
            self.channel = QuantumChannel(
                self.name, 
                self.timeline,
                distance=distance,
                attenuation=attenuation
            )
        else:
            self.channel = ClassicalChannel(
                self.name,
                self.timeline,
                distance=distance
            )


class Hybridnetwork:
    """
    Hybrid Network class using SeQUeNCe
    Replaces NetSquid Network functionality
    
    Manages nodes, connections, and communication with NS3/SDN controller
    """
    
    def __init__(self, port, name, nodes):
        self.port = port
        self.name = name
        self.nodes_param = nodes
        self.data_sent = False
        
        # SeQUeNCe components
        self.timeline = None
        self.nodes = {}  # Dict of HybridNode objects
        self.connections = {}  # Dict of HybridConnection objects
        self.quantum_connections = {}
        self.classical_connections = {}
        
    def init_timeline(self, runtime_ns: float = 1e12):
        """Initialize SeQUeNCe timeline"""
        self.timeline = Timeline(runtime_ns)
        self.timeline.show_progress = False
        
    def add_node(self, node):
        """
        Add a node to the network
        
        Args:
            node: Can be string name or HybridNode object
        """
        if isinstance(node, str):
            if self.timeline is None:
                self.init_timeline()
            hybrid_node = HybridNode(node, self.timeline)
            self.nodes[node] = hybrid_node
            print(f"[HybridNetwork] Added node: {node}")
        elif isinstance(node, HybridNode):
            self.nodes[node.name] = node
            print(f"[HybridNetwork] Added node: {node.name}")
        else:
            # Try to get name attribute
            node_name = getattr(node, 'name', str(node))
            if self.timeline is None:
                self.init_timeline()
            hybrid_node = HybridNode(node_name, self.timeline)
            self.nodes[node_name] = hybrid_node
            print(f"[HybridNetwork] Added node: {node_name}")
    
    def add_ns3_node(self, node):
        """Add NS3 node reference"""
        print(f"[HybridNetwork] New NS3 node: {node}")
        # Store NS3 node reference
        if isinstance(node, str):
            self.nodes[node] = {"type": "ns3", "name": node}
        else:
            node_name = getattr(node, 'name', str(node))
            self.nodes[node_name] = {"type": "ns3", "name": node_name}
    
    def add_connection(self, node1, node2, connection=None, channel_to=None, 
                       channel_from=None, delay=0, bidirectional=True, 
                       label="", port_name_node1="", port_name_node2="", 
                       ip="", port=""):
        """
        Add classical connection between nodes
        
        Args:
            node1: First node name
            node2: Second node name
            connection: Connection object (optional)
            channel_to: Channel to node2 (optional)
            channel_from: Channel from node2 (optional)
            delay: Channel delay
            bidirectional: Whether connection is bidirectional
            label: Connection label
            port_name_node1: Port name on node1
            port_name_node2: Port name on node2
            ip: IP address for NS3
            port: Port for NS3
        """
        print(f"QQC:: add_connection():: {node1} : {node2} ip: {ip} port: {port}")
        
        try:
            if self.timeline is None:
                self.init_timeline()
            
            # Create connection
            conn_name = label if label else f"conn_{node1}_{node2}"
            hybrid_conn = HybridConnection(
                conn_name, node1, node2, 
                channel_type="classical",
                timeline=self.timeline
            )
            hybrid_conn.setup_channel()
            
            self.connections[conn_name] = hybrid_conn
            self.classical_connections[conn_name] = hybrid_conn
            
            # Update node connections
            if node1 in self.nodes and isinstance(self.nodes[node1], HybridNode):
                self.nodes[node1].add_connection(node2, hybrid_conn)
            if node2 in self.nodes and isinstance(self.nodes[node2], HybridNode):
                self.nodes[node2].add_connection(node1, hybrid_conn)
                
            print(f"[HybridNetwork] Added connection: {node1} <-> {node2}")
            
        except Exception as e:
            print(f"[HybridNetwork] Connection error: {e}")
    
    def add_connection1(self, node1, node2, delay, connection, channel_to, 
                        channel_from, label, bidirectional, port_name_node1, 
                        port_name_node2, ip, port):
        """Alternative connection method"""
        print(f"QQC:: add_connection1():: {node1} : {node2} ip: {ip} port: {port}")
        self.add_connection(
            node1, node2, connection, channel_to, channel_from,
            delay, bidirectional, label, port_name_node1, port_name_node2, ip, port
        )
    
    def add_quantumconnection(self, node1, node2, channel_to, bidirectional, 
                               label, port_name_node1, port_name_node2, ip, port):
        """
        Add quantum connection between nodes
        
        Args:
            node1: First node name
            node2: Second node name
            channel_to: Quantum channel
            bidirectional: Whether connection is bidirectional
            label: Connection label
            port_name_node1: Port name on node1
            port_name_node2: Port name on node2
            ip: IP address
            port: Port number
        """
        print(f"QQC:: add_quantumconnection():: {node1} : {node2} ip: {ip} port: {port}")
        
        try:
            if self.timeline is None:
                self.init_timeline()
            
            # Create quantum connection
            conn_name = label if label else f"qconn_{node1}_{node2}"
            hybrid_conn = HybridConnection(
                conn_name, node1, node2,
                channel_type="quantum",
                timeline=self.timeline
            )
            hybrid_conn.setup_channel()
            
            self.connections[conn_name] = hybrid_conn
            self.quantum_connections[conn_name] = hybrid_conn
            
            print(f"[HybridNetwork] Added quantum connection: {node1} <-> {node2}")
            
        except Exception as e:
            print(f"[HybridNetwork] Quantum connection error: {e}")
    
    def add_ns3_connection(self, node1, node2, delay, connection, channel_to,
                           channel_from, label, bidirectional, port_name_node1,
                           port_name_node2, ip, port):
        """
        Add NS3 connection - sends request to NS3 simulator
        
        Args:
            node1: First node name
            node2: Second node name
            delay: Connection delay
            connection: Connection object
            channel_to: Channel to node2
            channel_from: Channel from node2
            label: Connection label
            bidirectional: Whether bidirectional
            port_name_node1: Port on node1
            port_name_node2: Port on node2
            ip: NS3 server IP
            port: NS3 server port
        """
        print(f"QQC:: add_ns3_connection():: {node1} : {node2} ip: {ip} port: {port}")
        
        url = f"http://{ip}:{port}/qns"
        print(f"QQC:: add_ns3_connection(): URL: {url}")
        
        try:
            ns3_data = [node1, node2, ip, port]
            response = requests.post(url, json=ns3_data, timeout=10)
            print(json.dumps(response.json(), indent=4))
        except requests.exceptions.RequestException as e:
            print(f"[HybridNetwork] NS3 connection error: {e}")
    
    def send(self, source, destination, sourcebit, res_measure, stateList,
             B_basis, qber, keyA, keyB, sourceip, destinationip, port,
             message, commandtype, message_id, command_id, command, node_id, all_link):
        """
        Send BB84 results to nodes and SDN controller
        
        Args:
            source: Source node ID
            destination: Destination node ID
            sourcebit: Source bits
            res_measure: Measurement results
            stateList: Alice's basis (state list)
            B_basis: Bob's basis
            qber: Quantum bit error rate
            keyA: Key at node A
            keyB: Key at node B
            sourceip: Source IP
            destinationip: Destination IP
            port: Port number
            message: Response message
            commandtype: Command type
            message_id: Message ID
            command_id: Command ID
            command: Command
            node_id: Node ID
            all_link: All link information
        """
        desturl = f"http://{destinationip}:{port}/SDN/response"
        print(f"CSG:: send(): Destination URL: {desturl}")
        
        sourceurl = f"http://{sourceip}:{port}/SDN/response"
        print(f"QQC:: send(): Source URL: {sourceurl}")
        
        # Send to NS3 only if data_sent is False
        if not self.data_sent:
            data = {
                "response": message,
                "Type": commandtype,
                "message_id": message_id,
                "command_id": command_id,
                "command": command,
                "node_id": node_id
            }
            
            try:
                senddata = requests.post(sourceurl, json=data, timeout=10)
                print(json.dumps(senddata.json(), indent=4))
                self.data_sent = True
            except requests.exceptions.RequestException as e:
                print(f"[HybridNetwork] Send error: {e}")
        
        # Prepare receiver data
        receiverdata = {
            "NODE_ID": destination,
            "source": source,
            "destination": destination,
            "port": port,
            "ip": destinationip,
            "basis": stateList,
            "bits": res_measure,
            "key": keyB,
            "qber": qber,
            "all_link": all_link
        }
        print(f"TO RECEIVER NODE: {receiverdata}")
        
        # Prepare transmitter data
        transmitterdata = {
            "NODE_ID": source,
            "source": source,
            "destination": destination,
            "port": port,
            "ip": sourceip,
            "basis": stateList,
            "bits": res_measure,
            "key": keyA,
            "qber": qber,
            "all_link": all_link
        }
        print(f"TO TRANSMITTER NODE: {transmitterdata}")
        
        # Send to receiver
        try:
            receiverresponse = requests.post(desturl, json=receiverdata, timeout=10)
            print(json.dumps(receiverresponse.json(), indent=4))
            print("")
        except requests.exceptions.RequestException as e:
            print(f"[HybridNetwork] Receiver send error: {e}")
        
        # Send to transmitter
        try:
            transmitterresponse = requests.post(sourceurl, json=transmitterdata, timeout=10)
            print(json.dumps(transmitterresponse.json(), indent=4))
        except requests.exceptions.RequestException as e:
            print(f"[HybridNetwork] Transmitter send error: {e}")
    
    def sendresponse(self, ip, port, message, commandtype, message_id,
                     command_id, command, node_id, all_links):
        """
        Send response to SDN controller
        
        Args:
            ip: Controller IP
            port: Controller port
            message: Response message
            commandtype: Command type
            message_id: Message ID
            command_id: Command ID
            command: Command
            node_id: Node ID
            all_links: All links information
        """
        url = f"http://{ip}:{port}/SDN/response"
        
        data = {
            "response": message,
            "Type": commandtype,
            "message_id": message_id,
            "command_id": command_id,
            "command": command,
            "node_id": node_id,
            "all_links": all_links
        }
        print(f"[HybridNetwork] Sending response: {data}")
        
        try:
            senddata = requests.post(url, json=data, timeout=10)
            print(json.dumps(senddata.json(), indent=4))
        except requests.exceptions.RequestException as e:
            print(f"[HybridNetwork] Response send error: {e}")
    
    def logsend(self, source, destination, step1="", noqubittransmitted="",
                res_measure="", stateList="", B_basis="", matchlist="",
                qber="", keyA="", keyB="", sourceip="", destinationip="", port=""):
        """
        Send log data and upload log file
        
        Args:
            source: Source node
            destination: Destination node
            step1: Step 1 info
            noqubittransmitted: Number of qubits transmitted
            res_measure: Measurement results
            stateList: State list (Alice's basis)
            B_basis: Bob's basis
            matchlist: Match list
            qber: QBER
            keyA: Key A
            keyB: Key B
            sourceip: Source IP
            destinationip: Destination IP
            port: Port
        """
        timestamp = time.time()
        
        sourcedata = {
            "timestamp": timestamp,
            "noqubittransmitted": noqubittransmitted,
            "stateList": stateList,
            "matchlist": matchlist
        }
        
        destinationdata = {
            "timestamp": timestamp,
            "res_measure": res_measure,
            "B_basis": B_basis
        }
        
        sourcefilename = f"{source}.txt"
        destinationfilename = f"{destination}.txt"
        
        # Write source log
        try:
            with open(sourcefilename, 'a') as file:
                json.dump(sourcedata, file, ensure_ascii=False)
                file.write('\n')
        except IOError as e:
            print(f"[HybridNetwork] Source log write error: {e}")
        
        # Write destination log
        try:
            with open(destinationfilename, 'a') as file:
                json.dump(destinationdata, file)
                file.write('\n')
        except IOError as e:
            print(f"[HybridNetwork] Destination log write error: {e}")
        
        # Upload log file
        try:
            url = f"http://{destinationip}:{port}/log"
            print(f"CSG:: logsend(): URL: {url}")
            
            file_path = "../conf/log.txt"
            
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    response = requests.post(url, files={"file": file}, timeout=10)
                
                if response.status_code == 200:
                    print("[HybridNetwork] File uploaded successfully.")
                else:
                    print(f"[HybridNetwork] Error uploading file. Status: {response.status_code}")
            else:
                print(f"[HybridNetwork] File path does not exist: {file_path}")
                
        except requests.exceptions.RequestException as e:
            print(f"[HybridNetwork] Log send error: {e}")
    
    def get_node(self, name: str):
        """Get node by name"""
        return self.nodes.get(name)
    
    def get_connection(self, label: str):
        """Get connection by label"""
        return self.connections.get(label)
    
    def get_all_nodes(self):
        """Get all nodes"""
        return list(self.nodes.keys())
    
    def get_all_connections(self):
        """Get all connections"""
        return list(self.connections.keys())
    
    def reset_data_sent(self):
        """Reset data_sent flag"""
        self.data_sent = False
    
    def run_simulation(self):
        """Run the SeQUeNCe simulation"""
        if self.timeline:
            self.timeline.init()
            self.timeline.run()
    
    def stop_simulation(self):
        """Stop the simulation"""
        if self.timeline:
            self.timeline.stop()
    
    def reset(self):
        """Reset the network"""
        self.nodes = {}
        self.connections = {}
        self.quantum_connections = {}
        self.classical_connections = {}
        self.data_sent = False
        if self.timeline:
            self.timeline = None


# =============================================================================
# HELPER CLASSES FOR COMPATIBILITY
# =============================================================================

class QuantumMemory:
    """
    Simple Quantum Memory class for compatibility
    SeQUeNCe handles memory internally in QKDNode
    """
    
    def __init__(self, name: str, num_positions: int = 1):
        self.name = name
        self.num_positions = num_positions
        self.qubits = [None] * num_positions
    
    def put(self, qubit, position: int = 0):
        """Store qubit at position"""
        if 0 <= position < self.num_positions:
            self.qubits[position] = qubit
    
    def get(self, position: int = 0):
        """Get qubit from position"""
        if 0 <= position < self.num_positions:
            return self.qubits[position]
        return None
    
    def pop(self, position: int = 0):
        """Pop qubit from position"""
        qubit = self.get(position)
        if qubit:
            self.qubits[position] = None
        return qubit


class QuantumProcessor:
    """
    Simple Quantum Processor class for compatibility
    SeQUeNCe handles processing internally
    """
    
    def __init__(self, name: str, num_positions: int = 1):
        self.name = name
        self.num_positions = num_positions
        self.memory = QuantumMemory(f"{name}_mem", num_positions)
    
    def execute(self, operation, positions):
        """Execute quantum operation"""
        print(f"[QuantumProcessor] Executing {operation} on positions {positions}")
        # SeQUeNCe handles actual quantum operations
        pass


class Channel:
    """
    Base Channel class for compatibility
    """
    
    def __init__(self, name: str, delay: float = 0):
        self.name = name
        self.delay = delay
        self.source = None
        self.destination = None
    
    def send(self, data):
        """Send data through channel"""
        print(f"[Channel] Sending data through {self.name}")
        # Actual sending handled by SeQUeNCe or HTTP requests


class Connection:
    """
    Connection class for compatibility
    """
    
    def __init__(self, name: str, channel_to=None, channel_from=None):
        self.name = name
        self.channel_to = channel_to
        self.channel_from = channel_from
    
    def send(self, data, direction="to"):
        """Send data through connection"""
        if direction == "to" and self.channel_to:
            self.channel_to.send(data)
        elif direction == "from" and self.channel_from:
            self.channel_from.send(data)


# =============================================================================
# NETWORK CLASS ALIAS FOR COMPATIBILITY
# =============================================================================

Network = Hybridnetwork


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Hybrid Network Module Test (SeQUeNCe-based)")
    print("=" * 60)
    
    # Create network
    network = Hybridnetwork(port="5071", name="test_network", nodes="5")
    
    # Initialize timeline
    network.init_timeline()
    
    # Add nodes
    network.add_node("A")
    network.add_node("B")
    network.add_node("C")
    network.add_node("D")
    network.add_node("F")
    
    # Add connections
    network.add_connection("A", "B", label="AB", ip="127.0.0.1", port="5071")
    network.add_connection("B", "C", label="BC", ip="127.0.0.1", port="5071")
    network.add_connection("B", "D", label="BD", ip="127.0.0.1", port="5071")
    network.add_connection("C", "F", label="CF", ip="127.0.0.1", port="5071")
    network.add_connection("D", "F", label="DF", ip="127.0.0.1", port="5071")
    
    # Add quantum connections
    network.add_quantumconnection("A", "B", None, True, "QAB", "", "", "127.0.0.1", "5071")
    
    print("\nNodes:", network.get_all_nodes())
    print("Connections:", network.get_all_connections())
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
