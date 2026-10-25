#ifndef CONFIG_H
#define CONFIG_H
#include <string>
#include "../Simulator_Service/utility.h"
using namespace std;

#define GUI_SERVER	"gui"
#define QCC_SERVER	"classical_simulator"
#define SDN_SERVER	"sd_qkdn_controller"
#define QQC_SERVER	"quantum_simulator"
#define SERVER_CONFIG_FILE	"/conf/server.conf"

class Config
{
	string guiip;
	string guiport;
	string simulatorip;
	string simulatorport;
	string sdncontrollerip;
	string sdncontrollerport;
	string quantumchannelip;
	string quantumchannelport;
	public:
	bool LoadConfiguration(string filename);
	bool SetServerAddress(string server, string ip, string port);
	string GetServerIP(string server);
	string GetServerPort(string server);
	int GetServerPortNumber(string server);
	string GetServerURL(string server);

	Config();
	
}static QConfig;
#endif
