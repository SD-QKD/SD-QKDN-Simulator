QNE_HOME=/home/qns/Desktop/QNE2
ULFIUS_HOME=/home/qns/Downloads/ulfius-2.7.10
ORCANIA_HOME=/home/qns/Downloads/orcania-2.3.3
YDER_HOME=/home/qns/Downloads/yder-1.4.20
NS3_HOME=/home/qns/Downloads/ns-allinone-3.40/ns-3.40
CRYPTOPP_HOME=/home/qns/Desktop/QNE/Classical/cryptopp-CRYPTOPP_8_7_0
# VERSION=$$(svn info svn://csg-svn.tvm.cdac.in/CSG030D/Products/trunk/Software/Emulator/QNE -r 'HEAD'  | grep Revision  | egrep -o  "[0-9]+")
# VERSION=1.1
# CPPFLAGS = -DVERSION=$(VERSION)
# qne: qne.cc
# ── Git version info ──────────────────────────────────────────
GIT_COMMIT   := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_REVISION := $(shell git rev-list --count HEAD 2>/dev/null || echo "0")
GIT_TAG      := $(shell git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
# VERSION      := $(GIT_TAG)
VERSION      := 3.0.0
# ─────────────────────────────────────────────────────────────

CPPFLAGS = -DVERSION=\"$(VERSION)\" \
           -DGIT_COMMIT=\"$(GIT_COMMIT)\" \
           -DGIT_REVISION=$(GIT_REVISION)

qne: qne.cc
	g++ $(CPPFLAGS) -std=gnu++17 REST_Interface/server.cc REST_Interface/rest-api.cc REST_Interface/config.cc Simulator_Service/simulator.cc Simulator_Service/qcc-simulate.cc Simulator_Service/utility.cc SDN_Agent/SDNAgent.cc SDN_Agent/post-processing.cc SDN_Agent/crypto.cc Key_Store/KeyStore.cc QKD_Node/QKDNode.cc qne.cc -o qne -I$(ULFIUS_HOME)/include -I$(ULFIUS_HOME)/example_programs/include -I$(ORCANIA_HOME)/include -I$(YDER_HOME)/include -L$(ULFIUS_HOME)/src -L$(YDER_HOME)/build -L$(ORCANIA_HOME)/build -I$(NS3_HOME)/build/include  -lpthread -lulfius -lorcania -lyder -ljansson -ldl -L$(NS3_HOME)/build/lib -L$(CRYPTOPP_HOME) -lns3.40-aodv-default -lns3.40-dsr-default -lns3.40-mesh-default -lns3.40-netanim-default  -lns3.40-wifi-default -lns3.40-lr-wpan-default -lns3.40-lte-default -lns3.40-spectrum-default -lns3.40-antenna-default -lns3.40-applications-default -lns3.40-csma-layout-default -lns3.40-dsdv-default -lns3.40-flow-monitor-default -lns3.40-internet-apps-default -lns3.40-wimax-default -lns3.40-point-to-point-layout-default  -lns3.40-nix-vector-routing-default -lns3.40-olsr-default -lns3.40-sixlowpan-default -lns3.40-tap-bridge-default -lns3.40-internet-default -lns3.40-bridge-default -lns3.40-point-to-point-default -lns3.40-traffic-control-default -lns3.40-buildings-default -lns3.40-propagation-default -lns3.40-uan-default -lns3.40-mobility-default -lns3.40-energy-default -lns3.40-config-store-default -lns3.40-csma-default -lns3.40-fd-net-device-default -lns3.40-virtual-net-device-default -lns3.40-topology-read-default -lns3.40-network-default -lns3.40-stats-default -lns3.40-core-default -lrt -lcurl -ljsoncpp -lcryptopp -lboost_iostreams -lulfius -lorcania -lyder -luuid  

clean:
	@rm qne
