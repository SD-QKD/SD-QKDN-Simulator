"""
Quantum Network Simulator — SeQUENce + NS3  (fixed)

Logic:
  - QUANTUM_CHANNEL_PROVISION  : acknowledge each node (TX and RX separately),
                                  store their IPs keyed by node_id.
  - QUANTUM_CHANNEL_START      : if TX and RX are direct neighbours → run BB84,
                                  send generated key ONLY to those two nodes.
                                  if NOT neighbours → return Fail to GUI immediately.
  - All other nodes are never touched.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time, json, threading
import numpy as np
from flask import Flask, jsonify, request

from MAQAN import (
    attach_bb84_stack2, enable_bb84_metrics, reset_metrics,
    connect, xor_encrypt, InterceptResend,
)
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import BB84 as SeqBB84, pair_bb84_protocols
from sequence.kernel.event import Event
from sequence.kernel.process import Process
from Netsquid_BB84 import hybridnetwork

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ENV_QNE_HOME       = "QNE_HOME"
QNE_HOME           = "./"
SERVER_CONFIG_FILE = "/conf/server.conf"
QCC_SERVER         = "classical_simulator"
QQC_SERVER         = "quantum_simulator"

qconf = [0] * 10

class QnsConfig:
    def __init__(self, s, ip, p): self.servername=s; self.ip=ip; self.port=p

class QLinkparameter:
    def __init__(self, length, numbits, lossmodel, ploss_init, ploss_length):
        self.length=length; self.numbits=numbits; self.lossmodel=lossmodel
        self.ploss_init=ploss_init; self.ploss_length=ploss_length

class Topology:
    def __init__(self, tid, tname): self.topologyid=tid; self.topologyname=tname

class Eveparameter:
    def __init__(self, atype, apct): self.attacktype=atype; self.attackpercentage=apct

class Provisionmessage:
    def __init__(self, mid, cid, cmd, nid):
        self.message_id=mid; self.command_id=cid; self.command=cmd; self.node_id=nid

class Nodeprovision:
    def __init__(self, ip, port): self.ip=ip; self.port=port

# ---------------------------------------------------------------------------
# BB84 result (written by simulation, read by send)
# ---------------------------------------------------------------------------
class BB84Result:
    measurement=[];  Bobbasis=[]; Alicebasis=[]
    KeyA=[];  KeyB=[];  Qber=0.0
    photons_sent=0;  photons_recv=0

BB84     = BB84Result()
measuredsourcebit = []
current_keys      = {}

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
Qlink                  = None
topologyobj            = None
nodeprovisionobj       = None
provisionmessageobject = None
eve                    = None

stop_simulation = False
link_status     = "Down"
jsoncommand     = ""

# -- Persistent IP store: node_id → ip
#    Populated on PROVISION, cleared on STOP.
#    Never cleared on TX so RX data survives.
node_ip_store: dict = {}

# -- Link IDs accumulated during PROVISION phase, sent back with START acks
all_link_ids: list = []

# -- Track current TX/RX pair for status endpoint
current_tx_id = ""
current_rx_id = ""

# ---------------------------------------------------------------------------
# MAQAN direct-link neighbour table
# Only these pairs may exchange QKD keys directly.
# ---------------------------------------------------------------------------
NEIGHBOURS = {
    ("node_a","node_b"),("node_b","node_a"),
    ("node_b","node_c"),("node_c","node_b"),
    ("node_b","node_d"),("node_d","node_b"),
    ("node_c","node_f"),("node_f","node_c"),
    ("node_d","node_f"),("node_f","node_d"),
}

NODE_MAP = {
    "node_a":"A","node_b":"B","node_c":"C",
    "node_d":"D","node_f":"F",
    "a":"A","b":"B","c":"C","d":"D","f":"F",
}

def are_neighbours(tx, rx):
    return (tx.lower().strip(), rx.lower().strip()) in NEIGHBOURS

def resolve_node(nid):
    return NODE_MAP.get(nid.lower().strip(), nid.upper())

# ---------------------------------------------------------------------------
# Server helpers
# ---------------------------------------------------------------------------
def get_ip(server):
    for i in range(4):
        if qconf[i].servername == server: return qconf[i].ip
    return None

def get_port(server):
    for i in range(4):
        if qconf[i].servername == server: return qconf[i].port
    return None

def load_default_configuration():
    qconf[0]=QnsConfig("gui",                "127.0.0.1","5050")
    qconf[1]=QnsConfig("classical_simulator","127.0.0.1","5071")
    qconf[2]=QnsConfig("quantum_simulator",  "127.0.0.1","5072")
    qconf[3]=QnsConfig("sd_qkdn_controller", "127.0.0.1","8080")

def load_configuration():
    try: home = os.environ[ENV_QNE_HOME]
    except KeyError: home = QNE_HOME; print("QNE_HOME not set, using default")
    try:
        with open(home + SERVER_CONFIG_FILE) as f:
            for i, line in enumerate(f):
                x=line.split("=",1); y=x[1].split(":",1)
                qconf[i]=QnsConfig(x[0].strip(),y[0].strip(),y[1].strip())
    except Exception: load_default_configuration()

load_configuration()

# ---------------------------------------------------------------------------
# SeQUENce BB84 — runs ONLY between the two selected adjacent nodes
# ---------------------------------------------------------------------------
def run_single_link_bb84(tx_name, rx_name, num_bits=128, runtime_ms=250,
                         distance=1000, attenuation=0.0002,
                         eve_enabled=False, eve_p_attack=0.5):
    """
    Run BB84 between tx_name and rx_name only.
    Returns (store, ok) and populates global BB84 result.
    """
    global BB84, measuredsourcebit, current_keys

    print(f"\n=== BB84: {tx_name} → {rx_name} ===")
    t0 = time.time()

    tl = Timeline(runtime_ms * 1e9)
    tl.show_progress = False

    TX = QKDNode(tx_name, tl, stack_size=2)
    RX = QKDNode(rx_name, tl, stack_size=2)
    connect(tl, TX, RX, f"{tx_name}{rx_name}",
            distance=distance, attenuation=attenuation)

    if eve_enabled:
        eo = InterceptResend(p_attack=eve_p_attack); eo.enabled=True
        qc = TX.qchannels[rx_name]; orig = qc.transmit
        def etx(photon,*a,**k): return orig(eo.intercept(photon),*a,**k)
        qc.transmit = etx

    bb84_tx = TX.protocol_stack[0]
    bb84_rx = RX.protocol_stack[0]
    enable_bb84_metrics(bb84_tx)
    enable_bb84_metrics(bb84_rx)
    pair_bb84_protocols(bb84_tx, bb84_rx)

    captured = {}
    for name, inst in [(tx_name, bb84_tx), (rx_name, bb84_rx)]:
        captured[name] = {"key": None}
        orig_sk = inst.set_key
        def make_hook(n, i, o):
            def hook(): o(); captured[n]["key"] = getattr(i,"key",None)
            return hook
        inst.set_key = make_hook(name, inst, orig_sk)

    class R:
        def __init__(self,fn): self.fn=fn
        def run(self): self.fn()

    def start(): reset_metrics(bb84_tx, bb84_rx); bb84_tx.push(num_bits, 1)

    tl.schedule(Event(0,         Process(R(start),        "run",[])))
    tl.schedule(Event(int(30e9), Process(R(lambda:None),  "run",[])))
    tl.init(); tl.run()

    key_tx = captured[tx_name]["key"]
    key_rx = captured[rx_name]["key"]
    ok     = (key_tx is not None) and (key_tx == key_rx)

    print(f"[{tx_name}→{rx_name}] ok={ok}  KeyTX={key_tx}  KeyRX={key_rx}"
          f"  QBER={bb84_tx.error_rates[-1] if getattr(bb84_tx,'error_rates',[]) else 'N/A'}"
          f"  ({time.time()-t0:.2f}s)")

    ki = key_tx if key_tx else 0
    key_bits = (np.array([int(b) for b in bin(ki)[2:].zfill(ki.bit_length())],dtype=int)
                if ki else np.array([],dtype=int))
    key_len = len(key_bits)

    def flatten_basis(inst):
        bl = getattr(inst,'basis_lists',None)
        return np.concatenate([np.array(b,dtype=int) for b in bl]) if bl else None

    tx_bf = flatten_basis(bb84_tx)
    rx_bf = flatten_basis(bb84_rx)

    if tx_bf is not None and rx_bf is not None and len(tx_bf)==len(rx_bf) and key_len>0:
        mi = np.where(tx_bf==rx_bf)[0]
        if len(mi)>=key_len:
            alice_basis_arr = tx_bf[mi[:key_len]]
            bob_basis_arr   = rx_bf[mi[:key_len]]
        else:
            alice_basis_arr = bob_basis_arr = np.zeros(key_len,dtype=int)
    else:
        alice_basis_arr = bob_basis_arr = np.zeros(key_len,dtype=int)

    BB84.Alicebasis   = alice_basis_arr
    BB84.Bobbasis     = bob_basis_arr
    BB84.measurement  = [key_bits]
    BB84.Qber         = bb84_tx.error_rates[-1] if getattr(bb84_tx,'error_rates',[]) else 0.0
    BB84.KeyA         = key_tx if key_tx else []
    BB84.KeyB         = key_rx if key_rx else []
    BB84.photons_sent = getattr(bb84_tx,'photons_sent',0)
    BB84.photons_recv = getattr(bb84_rx,'photons_received',0)

    measuredsourcebit = key_bits
    store = {"K_TX":key_tx,"K_RX":key_rx,
             f"K_{tx_name}{rx_name}_TX":key_tx,
             f"K_{tx_name}{rx_name}_RX":key_rx}
    current_keys = dict(store)
    return store, ok

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hn():
    return hybridnetwork.Hybridnetwork(
        name="hybrid_network", port=get_port(QCC_SERVER), nodes="0")

def BB84_start_topology(topology_id, topology_name):
    print(f"*** SIMULATOR UP — Topology {topology_id} ({topology_name})"
          f"  bits={Qlink.numbits if Qlink else 'N/A'}"
          f"  dist={Qlink.length  if Qlink else 'N/A'} ***")

def Hybrid_Log_Send(tx_id, rx_id):
    try:
        _hn().logsend(
            source=tx_id, destination=rx_id,
            sourcebit=str(measuredsourcebit),
            stateList=str(BB84.Alicebasis),
            sourceip=node_ip_store.get(tx_id,""),
            destinationip=node_ip_store.get(rx_id,""),
            res_measure=str(BB84.measurement),
            B_basis=str(BB84.Bobbasis),
            qber=str(BB84.Qber),
            keyA=str(BB84.KeyA),
            keyB=str(BB84.KeyB),
            port=get_port(QCC_SERVER),
        )
    except Exception as e:
        print(f"Log send failed: {e}")

# ---------------------------------------------------------------------------
# Background thread: send PROVISION ACK to ONE node
# ---------------------------------------------------------------------------
def _send_provision_ack(ip, port, mid, cid, cmd, nid, links):
    print(f"[ACK thread] → {ip}:{port}  links={links}")
    time.sleep(1.5)
    try:
        _hn().sendresponse(
            ip=ip, message="Success", port=port,
            commandtype="command",
            message_id=mid, command_id=cid,
            command=cmd, node_id=nid,
            all_links=links,
        )
        print(f"[ACK] sent to {ip}")
    except Exception as e:
        print(f"[ACK] failed to {ip}: {e}")

# ---------------------------------------------------------------------------
# Background thread: run BB84 and deliver keys ONLY to TX and RX nodes
# ---------------------------------------------------------------------------
def _run_provision(tx_id, rx_id, tx_ip, rx_ip, port,
                   mid, cid, cmd, nid, links,
                   topology_id, topology_name):
    global link_status

    num_bits    = Qlink.numbits      if Qlink else 128
    distance    = Qlink.length       if Qlink else 1000
    attenuation = Qlink.ploss_length if Qlink else 0.0002
    eve_enabled  = (topology_id == "3") and (eve is not None)
    eve_p_attack = eve.attackpercentage if (eve_enabled and eve) else 0.5

    tx_seq = resolve_node(tx_id)
    rx_seq = resolve_node(rx_id)

    print(f"[PROVISION thread] {tx_id}({tx_ip}) → {rx_id}({rx_ip})")
    print(f"  SeQUENce nodes: {tx_seq} → {rx_seq}")
    print(f"  bits={num_bits}  dist={distance}  att={attenuation}  eve={eve_enabled}")

    link_status = "Up"
    time.sleep(1.5)

    try:
        store, ok = run_single_link_bb84(
            tx_name=tx_seq, rx_name=rx_seq,
            num_bits=num_bits, distance=distance,
            attenuation=attenuation,
            eve_enabled=eve_enabled, eve_p_attack=eve_p_attack,
        )

        if ok:
            link_status = "Established"
            hn = _hn()
            hn.send(
                source        = tx_id,
                destination   = rx_id,
                sourcebit     = str(measuredsourcebit),
                res_measure   = str(BB84.measurement),
                B_basis       = str(BB84.Bobbasis),
                stateList     = str(BB84.Alicebasis),
                sourceip      = tx_ip,
                destinationip = rx_ip,
                keyA          = str(BB84.KeyA),
                keyB          = str(BB84.KeyB),
                port          = port,
                qber          = str(BB84.Qber),
                message       = "Success",
                commandtype   = "command",
                message_id    = mid,
                command_id    = cid,
                command       = cmd,
                node_id       = nid,
                all_link      = links,
            )
            print(f"[SUCCESS] Key delivered → {tx_id}({tx_ip})  {rx_id}({rx_ip})")
        else:
            link_status = "Failed"
            print("[ERROR] BB84 keys did not match — no key delivered.")

    except Exception as e:
        link_status = "Error"
        print(f"[EXCEPTION] {e}")
        import traceback; traceback.print_exc()

    time.sleep(3)

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
api = Flask(__name__)

@api.route('/sim/status', methods=['POST'])
def get_simulator_status():
    return json.dumps("Success/Fail"), 200

@api.route('/sim/probe/topology', methods=['GET','POST'])
def probe_topology():
    paths = {'file1_content':"../conf/maqan.json",
             'file2_content':"../conf/2node.json",
             'file3_content':"../conf/3node.json"}
    try:
        return jsonify({k: json.load(open(v)) for k,v in paths.items()})
    except FileNotFoundError:
        return jsonify(error='Topology file not found')
    except Exception as e:
        return jsonify(error=str(e))

@api.route('/sim/simulatetopology', methods=['POST'])
def get_simulator_simulate_topology():
    global Qlink, topologyobj, eve
    d = request.json
    print("Topology SIMULATE:", json.dumps(d))
    if d["topology-id"] == "3":
        eve = Eveparameter(d['nodes'][1]['attacktype'],
                           float(d['nodes'][1]['attackpercentage']))
    Qlink       = QLinkparameter(int(d["links"][0]["fiberlength"]),
                                 int(d["numbits"]),
                                 d["links"][0]["fiberlossmodel"],
                                 float(d["links"][0]["fiberlossinint"]),
                                 float(d["links"][0]["fiberlosslength"]))
    topologyobj = Topology(d["topology-id"], d["topology-name"])
    BB84_start_topology(d["topology-id"], d["topology-name"])
    return json.dumps("Success/Fail"), 200

@api.route('/sim/stoptopology', methods=['POST'])
def get_simulator_stop_topology():
    global stop_simulation
    stop_simulation = True
    return json.dumps("Success/Fail"), 200

@api.route('/sim/statustopology', methods=['POST'])
def get_simulator_status_topology():
    return json.dumps("Success/Fail"), 200


@api.route('/sim/link/provision', methods=['POST'])
def post_simulator_link_provision():
    """
    QUANTUM_CHANNEL_PROVISION (TX / RX)
        → store node IP in node_ip_store[node_id]
        → ACK that node immediately (background thread)

    QUANTUM_CHANNEL_START
        → adjacent?  YES → run BB84, deliver key to BOTH nodes only
                     NO  → return Fail JSON immediately to NS3/GUI

    QUANTUM_CHANNEL_STOP
        → clear all state

    QUANTUM_CHANNEL_REPROVISION
        → same adjacency check, then re-run BB84
    """
    global jsoncommand, nodeprovisionobj, provisionmessageobject
    global stop_simulation, node_ip_store, all_link_ids
    global current_tx_id, current_rx_id

    d          = request.json
    message_id = d["MESSAGE_ID"]
    command_id = d["COMMAND_ID"]
    command    = d["COMMAND"]
    tx_id      = d['COMMAND_PARAMS'][0]['TRANSMITTER']
    rx_id      = d['COMMAND_PARAMS'][0]['RECEIVER']
    nip        = d["IP"]
    nport      = d["PORT"]
    mode       = d['COMMAND_PARAMS'][0]['MODE']
    node_id    = d['NODE_ID']
    jsoncommand = command

    topology_id   = topologyobj.topologyid   if topologyobj else "1"
    topology_name = topologyobj.topologyname if topologyobj else "MAQAN"

    nodeprovisionobj       = Nodeprovision(nip, nport)
    provisionmessageobject = Provisionmessage(message_id, command_id, command, node_id)

    print(f"\n[CMD] {command}  TX={tx_id}  RX={rx_id}  MODE={mode}  IP={nip}:{nport}  CID={command_id}")

    # ── Collect link IDs ────────────────────────────────────────────────
    if command in ("QUANTUM_CHANNEL_PROVISION", "QUANTUM_CHANNEL_REPROVISION"):
        for p in d["COMMAND_PARAMS"]:
            for key in ("INCOMING_LINK", "OUTGOING_LINK"):
                lid = p[key]["LINK_ID"]
                if lid != "NA" and lid not in all_link_ids:
                    all_link_ids.append(lid)

    # ====================================================================
    #  QUANTUM_CHANNEL_PROVISION
    #  Store IP for this node, send ACK.
    # ====================================================================
    if command == "QUANTUM_CHANNEL_PROVISION":
        if mode == "TX":
            # New link starting — clear stale IP store and link IDs
            node_ip_store.clear()
            all_link_ids.clear()
            # Re-collect link IDs after clear
            for p in d["COMMAND_PARAMS"]:
                for key in ("INCOMING_LINK", "OUTGOING_LINK"):
                    lid = p[key]["LINK_ID"]
                    if lid != "NA" and lid not in all_link_ids:
                        all_link_ids.append(lid)

        # Store this node's IP — keyed by node_id (works for both TX and RX)
        node_ip_store[node_id] = nip
        print(f"[PROVISION {mode}] node_id={node_id}  ip={nip}  store={node_ip_store}")

        # ACK this node in background
        _links = list(all_link_ids)
        threading.Thread(
            target=_send_provision_ack,
            args=(nip, nport, message_id, command_id, command, node_id, _links),
            daemon=True
        ).start()

    # ====================================================================
    #  QUANTUM_CHANNEL_START
    # ====================================================================
    elif command == "QUANTUM_CHANNEL_START":
        stop_simulation = False
        current_tx_id = tx_id
        current_rx_id = rx_id

        # TX node always sends the START, so nip == tx_ip reliably.
        # RX ip is whatever was stored during its PROVISION message.
        tx_ip  = node_ip_store.get(tx_id, nip)
        rx_ip  = node_ip_store.get(rx_id, "")
        _links = list(all_link_ids)

        print(f"[START] TX={tx_id}({tx_ip})  RX={rx_id}({rx_ip})")
        print(f"[START] adjacent={are_neighbours(tx_id,rx_id)}  links={_links}")
        print(f"[START] node_ip_store={node_ip_store}")

        if not are_neighbours(tx_id, rx_id):
            print(f"[INVALID] {tx_id} <-> {rx_id} not adjacent — returning Fail to NS3")
            return jsonify({
                "response":   "Fail",
                "Type":       "command",
                "message_id": message_id,
                "command_id": command_id,
                "command":    command,
                "node_id":    node_id,
                "all_links":  _links,
            })

        # Valid adjacent link — run BB84 in background
        threading.Thread(
            target=_run_provision,
            args=(tx_id, rx_id, tx_ip, rx_ip, nport,
                  message_id, command_id, command, node_id, _links,
                  topology_id, topology_name),
            daemon=True
        ).start()
    # ====================================================================
    #  QUANTUM_CHANNEL_STOP
    # ====================================================================
    elif command == "QUANTUM_CHANNEL_STOP":
        stop_simulation   = True
        current_tx_id     = ""
        current_rx_id     = ""
        node_ip_store.clear()
        all_link_ids.clear()
        print("[STOP] Channel stopped, state cleared.")

    # ====================================================================
    #  QUANTUM_CHANNEL_REPROVISION
    # ====================================================================
    elif command == "QUANTUM_CHANNEL_REPROVISION":
        # Store IP
        node_ip_store[node_id] = nip
        print(f"[REPROVISION {mode}] node_id={node_id}  ip={nip}  store={node_ip_store}")

        if not are_neighbours(tx_id, rx_id):
            print(f"[REPROVISION INVALID] {tx_id} <-> {rx_id} not adjacent")
            _links = list(all_link_ids)
            # Notify GUI of failure via background thread using sendresponse
            def _fail_notify():
                time.sleep(1.5)
                try:
                    _hn().sendresponse(
                        ip=nip, message="Fail", port=nport,
                        commandtype="command",
                        message_id=message_id, command_id=command_id,
                        command=command, node_id=node_id,
                        all_links=_links,
                    )
                except Exception as e:
                    print(f"[REPROVISION FAIL notify] {e}")
            threading.Thread(target=_fail_notify, daemon=True).start()

        else:
            # Only start BB84 when both TX and RX have reported in
            # (both IPs are present in node_ip_store)
            tx_ip_known = node_ip_store.get(tx_id)
            rx_ip_known = node_ip_store.get(rx_id)

            if tx_ip_known and rx_ip_known:
                stop_simulation = False
                current_tx_id = tx_id
                current_rx_id = rx_id
                _links = list(all_link_ids)
                tx_ip  = tx_ip_known
                rx_ip  = rx_ip_known
                print(f"[REPROVISION START] {tx_id}({tx_ip}) → {rx_id}({rx_ip})")
                threading.Thread(
                    target=_run_provision,
                    args=(tx_id, rx_id, tx_ip, rx_ip, nport,
                          message_id, command_id, command, node_id, _links,
                          topology_id, topology_name),
                    daemon=True
                ).start()
            else:
                print(f"[REPROVISION] Waiting for both nodes — store={node_ip_store}")

    # Always return 200 immediately
    return jsonify({"status":"success","message":"Request processed."})


@api.route('/sim/link/status', methods=['POST'])
def get_simulator_link_status():
    d   = request.json
    src = d['COMMAND_PARAMS'][0]['TRANSMITTER']
    dst = d['COMMAND_PARAMS'][0]['RECEIVER']
    st  = "not provisioned"
    if d["COMMAND"] == "QUANTUM_CHANNEL_STATUS":
        if current_tx_id == src and current_rx_id == dst:
            st = "running"
        else:
            st = "stopped"
    print("Link status:", st)
    return jsonify(st)


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n" + "="*60)
    print("Quantum Network Simulator — SeQUENce + NS3")
    print("="*60)
    print(f"Classical : {get_ip(QCC_SERVER)}:{get_port(QCC_SERVER)}")
    print(f"Quantum   : {get_ip(QQC_SERVER)}:{get_port(QQC_SERVER)}")
    print("\nDirect QKD links allowed:")
    shown = set()
    api.run(
        host=get_ip(QQC_SERVER),
        port=get_port(QQC_SERVER),
        threaded=True,
    )
