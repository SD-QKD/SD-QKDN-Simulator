/*######################################################################
#
# File Name: server.cc
#
########################################################################
#
# Project Name : MAQAN
#
# Project Code : CGS030D
#
# Created : 10-2022
#
# Purpose : Simulation
#
# Description :
#
# Author(s) : Sajimon P C(pcsaji@cdac.in)
#
# Version No : v1.0
#
# Revisions :
#
# Remarks : Simulation server
#
# Copyright : Cyber Security Group, CDAC Thiruvanthapuram
######################################################################*/
#include <fstream>
#include <sstream>
#include <cctype>
#include <string>
#include <boost/algorithm/string.hpp>
#include "server.h"
#include "config.h"
#include "rest-api.h"
#include "../Simulator_Service/utility.h"
#include "../Simulator_Service/qcc-simulate.h"
#include "../SDN_Agent/post-processing.h"

#ifndef VERSION
#define VERSION "0.0.0"
#endif

#ifndef GIT_COMMIT
#define GIT_COMMIT "unknown"
#endif

#ifndef GIT_REVISION
#define GIT_REVISION 0
#endif

pthread_t thread_id_simulation;

void *RESTServerThread(void *vargp)
{
	RESTServer();
	return 0;
}

int RESTServer(void)
{
	struct _u_instance instance;
	json_int_t id_servertest = 0;
	json_int_t id_simstatus = 0, id_simprobetopology = 0, id_simstackcapability = 0, id_simulatetopology = 0;
	json_int_t id_stoptopology, id_statustopology,id_nodelinkdetails;

	if (ulfius_init_instance(&instance, QConfig.GetServerPortNumber(QCC_SERVER), NULL, NULL) != U_OK)
	{
		cout << "QNE: Server Start - FAILURE(abort)" << endl;
		return (-1);
	}

	setSimulatorStatus(true);

	setNetSquidIP(const_cast<char *>(QConfig.GetServerIP(QCC_SERVER).c_str()));
	setNetSquidPort(QConfig.GetServerPortNumber(QQC_SERVER));

	u_map_put(instance.default_headers, "Content-Type", "application/json");

	ulfius_add_endpoint_by_val(&instance, "GET", "", "*", 0, &callback_ServerTest, &id_servertest);
	ulfius_add_endpoint_by_val(&instance, "GET", URL_SIMULATOR_STATUS, "*", 0, &callback_SimulatorStatus, &id_simstatus);
	ulfius_add_endpoint_by_val(&instance, "GET", URL_PROBE_TOPOLOGY, "*", 0, &callback_SimulatorProbeTopology, &id_simprobetopology);
	ulfius_add_endpoint_by_val(&instance, "GET", URL_PROBE_STACK_CAPABILITY, "*", 0, &callback_SimulatorProbeStackCapability, &id_simstackcapability);
	ulfius_add_endpoint_by_val(&instance, "POST", URL_SIMULATE_TOPOLOGY, "*", 0, &callback_SimulateTopology, &id_simulatetopology);
	ulfius_add_endpoint_by_val(&instance, "POST", URL_STOP_TOPOLOGY, "*", 0, &callback_StopTopology, &id_stoptopology);
	ulfius_add_endpoint_by_val(&instance, "POST", URL_STATUS_TOPOLOGY, "*", 0, &callback_StatusTopology, &id_statustopology);
	ulfius_add_endpoint_by_val(&instance, "POST", URL_NODE_LINK_DETAILS, "*", 0, &callback_nodelinkdetails, &id_nodelinkdetails);
	if (ulfius_start_framework(&instance) == U_OK)
	{
		cout << "QNE Server [ "<<QConfig.GetServerIP(QCC_SERVER)<<" : "<< instance.port << " ] - STARTED" << endl<<endl;
		while (1)
		{
			sleep(0);
		}
	}
	else
	{
		cout << "QNE Server on Port " << instance.port << " - FAILED" << endl<<endl;
	}

	ulfius_stop_framework(&instance);
	ulfius_clean_instance(&instance);

	return 0;
}

int callback_ServerTest(const struct _u_request *request,
                        struct _u_response *response,
                        void *user_data)
{
    json_t *json_body = json_object();
    cout << "\n<<<< Server Test\n";

    json_object_set_new(json_body, "QKD Network Emulation  Platform (QNEP)",
                                   json_string("Running"));
    json_object_set_new(json_body, "Version",
                                   json_string(VERSION));
    json_object_set_new(json_body, "Commit",
                                   json_string(GIT_COMMIT));
    json_object_set_new(json_body, "Build No",
                                   json_integer(GIT_REVISION));
    json_object_set_new(json_body, "Date",
                                   json_string(__DATE__ ", " __TIME__));

    ulfius_set_json_body_response(response, 200, json_body);
    cout << "QNE Server - Running\n";
    return U_CALLBACK_CONTINUE;
}

int callback_SimulatorStatus(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();

	json_t *json_key[3];
	json_t *json_arrays = json_array();
	json_key[0] = json_object();
	json_key[1] = json_object();
	json_key[2] = json_object();
	cout << "\n<<<< Simulator Status\n";

	int ret = RestSend("QNS", QConfig.GetServerURL(QQC_SERVER).c_str(), URL_SIMULATOR_STATUS, json_body);
	if (ret == 0)
	{
		cout << "QQC Sequence - Running " << endl;
	}
	else
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	bool qsimstatus = getSimulatorStatus();
	if (qsimstatus == true)
	{
		json_object_set_new(json_body, "status", json_string("Running"));
	}
	else
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	json_object_set_new(json_body, "uptime", json_string(""));

	json_object_set_new(json_key[0], "id", json_string("1"));
	json_object_set_new(json_key[0], "name", json_string("MAQAN"));
	string str_topo_status = getTopologyStatus() ? "Yes" : "No";
	json_object_set_new(json_key[0], "running", json_string(getTopologyStatus(1) ? "Yes" : "No"));

	json_array_append_new(json_arrays, json_key[0]);

	json_object_set_new(json_body, "list-topologies", json_arrays);

	ulfius_set_json_body_response(response, 200, json_body);
	cout << "QNS Server - Running\n";
	return U_CALLBACK_CONTINUE;
}

int callback_SimulatorProbeTopology(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();

	json_t *json_key[3];
	json_t *json_arrays = json_array();
	json_key[0] = json_object();
	json_key[1] = json_object();
	json_key[2] = json_object();

	int ret = RestSend("QNS", QConfig.GetServerURL(QQC_SERVER).c_str(), URL_PROBE_TOPOLOGY, json_body);
	if (ret == 0)
	{
		cout << "QQC (Sequence) - Probe Topology " << endl;
	}
	else
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	cout << "\n<<<< Simulator ProbeTopology\n";

	json_object_set_new(json_key[0], "id", json_string("1"));
	json_object_set_new(json_key[0], "name", json_string("MAQAN 5-Node"));
	json_object_set_new(json_key[0], "running", json_string(getTopologyStatus(1) ? "Yes" : "No"));

	json_array_append_new(json_arrays, json_key[0]);

	json_object_set_new(json_body, "list-topologies", json_arrays);

	ulfius_set_json_body_response(response, 200, json_body);
	cout << "QNS Server - Probe Topology\n";
	return U_CALLBACK_CONTINUE;
}

int callback_SimulatorProbeStackCapability(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();

	json_t *json_key[2];
	json_t *json_arrays = json_array();
	json_key[0] = json_object();
	json_key[1] = json_object();

	cout << "\n<<<< Simulator Stack Capability\n";

	json_object_set_new(json_key[0], "id", json_string("1"));
	json_object_set_new(json_key[0], "protocol", json_string("BB84"));
	json_array_append_new(json_arrays, json_key[0]);
	json_object_set_new(json_body, "qkd-protocol", json_arrays);

	json_t *json_sift[2];
	json_t *json_arrays_sift = json_array();
	json_sift[0] = json_object();
	json_sift[1] = json_object();
	json_arrays_sift = json_array();

	json_object_set_new(json_sift[0], "id", json_string("1"));
	json_object_set_new(json_sift[0], "protocol", json_string("DEFAULT"));
	json_array_append_new(json_arrays_sift, json_sift[0]);

	if(getPostProcessingAlgorithms(ALGORITHM_SIFTING))
	{
		json_object_set_new(json_sift[1], "id", json_string("2"));
		json_object_set_new(json_sift[1], "protocol", json_string("CUSTOM"));
		json_array_append_new(json_arrays_sift, json_sift[1]);
	}
	json_object_set_new(json_body, "sifting", json_arrays_sift);

	json_t *json_errorestimation[2];
	json_t *json_arrays_errorestimation = json_array();
	json_errorestimation[0] = json_object();
	json_errorestimation[1] = json_object();
	json_arrays_errorestimation = json_array();
	json_object_set_new(json_errorestimation[0], "id", json_string("1"));
	json_object_set_new(json_errorestimation[0], "protocol", json_string("DEFAULT"));
	json_array_append_new(json_arrays_errorestimation, json_errorestimation[0]);

	if(getPostProcessingAlgorithms(ALGORITHM_ERROR_ESTIMATION))
	{
		json_object_set_new(json_errorestimation[1], "id", json_string("2"));
		json_object_set_new(json_errorestimation[1], "protocol", json_string("CUSTOM"));
		json_array_append_new(json_arrays_errorestimation, json_errorestimation[1]);
	}
	json_object_set_new(json_body, "error-estimation", json_arrays_errorestimation);

	json_t *json_errorcorrection[2];
	json_t *json_arrays_errorcorrection = json_array();
	json_errorcorrection[0] = json_object();
	json_errorcorrection[1] = json_object();
	json_arrays_errorcorrection = json_array();
	json_object_set_new(json_errorcorrection[0], "id", json_string("1"));
	json_object_set_new(json_errorcorrection[0], "protocol", json_string("DEFAULT"));
	json_array_append_new(json_arrays_errorcorrection, json_errorcorrection[0]);

	if(getPostProcessingAlgorithms(ALGORITHM_ERROR_CORRECTION))
	{
		json_object_set_new(json_errorcorrection[1], "id", json_string("2"));
		json_object_set_new(json_errorcorrection[1], "protocol", json_string("CUSTOM"));
		json_array_append_new(json_arrays_errorcorrection, json_errorcorrection[1]);
	}
	json_object_set_new(json_body, "error-correction", json_arrays_errorcorrection);

	json_t *json_privacyamplification[2];
	json_t *json_arrays_privacyamplification = json_array();
	json_privacyamplification[0] = json_object();
	json_privacyamplification[1] = json_object();
	json_arrays_privacyamplification = json_array();
	json_object_set_new(json_privacyamplification[0], "id", json_string("1"));
	json_object_set_new(json_privacyamplification[0], "protocol", json_string("DEFULT"));
	json_array_append_new(json_arrays_privacyamplification, json_privacyamplification[0]);
	if(getPostProcessingAlgorithms(ALGORITHM_PRIVACY_AMPLIFICATION))
	{
		json_object_set_new(json_privacyamplification[1], "id", json_string("2"));
		json_object_set_new(json_privacyamplification[1], "protocol", json_string("CUSTOM"));
		json_array_append_new(json_arrays_privacyamplification, json_privacyamplification[1]);
	}
	json_object_set_new(json_body, "privacy-amplification", json_arrays_privacyamplification);

	json_object_set_new(json_body, "status", json_string("success"));
	ulfius_set_json_body_response(response, 200, json_body);
	cout << "QNS Server - Stack Capability\n";
	return U_CALLBACK_CONTINUE;
}

int callback_SimulateTopology(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();
	json_t *json_sim_data = ulfius_get_json_body_request(request, NULL);

	bool topostatus = getTopologyStatus();
	if (topostatus == true)
	{
		json_object_set_new(json_body, "status", json_string("running"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL \n");
		return U_CALLBACK_CONTINUE;
	}

	char *topoid = NULL, *toponame = NULL, *controllerip = NULL, *controllerport = NULL;
	char *networkbase = NULL, *networkmask = NULL;
	char *agentupdation = NULL;

	topoid = (char *)json_string_value(json_object_get(json_sim_data, "topology-id"));
	toponame = (char *)json_string_value(json_object_get(json_sim_data, "topology-name"));
	controllerip = (char *)json_string_value(json_object_get(json_sim_data, "controller-ip"));
	controllerport = (char *)json_string_value(json_object_get(json_sim_data, "controller-port"));
	cout << " [ topo id  : " << topoid << ", name  : " << toponame << "  Controller : " << controllerip << " Port " << controllerport << " ]" << endl;

	int nwb_stat = json_is_string(json_object_get(json_sim_data, "network-base"));
	int nwm_stat = json_is_string(json_object_get(json_sim_data, "network-mask"));

	if ((nwb_stat == 0) || (nwm_stat == 0))
	{
		cout << "Network Base/Mask - Not valid (" << nwb_stat << ", " << nwm_stat << ")" << endl;
		cout << "Network Base/Mask - NULL (defaults to 10.1.10.0/255.255.255.0)" << endl;
	}
	else
	{
		networkbase = (char *)json_string_value(json_object_get(json_sim_data, "network-base"));
		networkmask = (char *)json_string_value(json_object_get(json_sim_data, "network-mask"));
		cout << " [ Network Base  : " << networkbase << ", Network Mask  : " << networkmask << " ] " << endl;

		string strnwb(networkbase);
		string strnwm(networkmask);

		int validip = isValidIP(strnwb);   
		int validmask = isValidIP(strnwm); 

		if (validip != 0)
		{
			setNetworkBase(networkbase);
		}
		if (validmask != 0)
		{
			setNetworkMask(networkmask);
		}
	}

	int agentupdation_stat = json_is_string(json_object_get(json_sim_data, "agent-updation"));
	if (agentupdation_stat == 0)
	{
		cout << "Agent Upation Interval - Not valid (" << agentupdation_stat << ")" << endl;
	}
	else
	{
		agentupdation = (char *)json_string_value(json_object_get(json_sim_data, "agent-updation"));
		setAgentUpdationInterval(stoi(agentupdation));
	}
	if (topoid == NULL || controllerip == NULL || controllerport == NULL)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	setControllerIP(controllerip);
	setControllerPort(stoi(controllerport));

	setTopologyID(stoi(topoid));

	int maxnodes = getNodesInTopology(stoi(topoid));
	if (maxnodes <= 1)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	int ret = RestSend("QNS", QConfig.GetServerURL(QQC_SERVER).c_str(), URL_SIMULATE_TOPOLOGY, json_sim_data);
	if (ret == 0)
	{
		json_object_set_new(json_body, "status", json_string("success"));
	}
	else
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL \n");
		return U_CALLBACK_CONTINUE;
	}

	json_t *nodes_topo = json_object_get(json_sim_data, "nodes");
    if (!json_is_array(nodes_topo)) {
        printf("JSON Data Posted - Status : FAIL (Node info)\n");
        return U_CALLBACK_CONTINUE;
    }

	json_t *links_topo = json_object_get(json_sim_data, "links");
    if (!json_is_array(links_topo)) {
        printf("JSON Data Posted - Status : FAIL (QC Links info)\n");
        return U_CALLBACK_CONTINUE;
    }

	json_t *cclinks_topo = json_object_get(json_sim_data, "cclinks");
    if (!json_is_array(cclinks_topo)) {
        printf("JSON Data Posted - Status : FAIL (CC Links info) - Continues \n");
       ;
    }

	setNodesDetails(nodes_topo);
	setLinksDetails(links_topo);
	setCCLinksDetails(cclinks_topo);

	pthread_create(&thread_id_simulation, NULL, QCCSimulationServerThread, NULL);
	setTopologyStatus(true);

	json_object_set_new(json_body, "status", json_string("success"));
	ulfius_set_json_body_response(response, 200, json_body);
	printf("JSON Data Posted - Status : SUCCESS \n");
	return 0;
}


int callback_StopTopology(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();
	json_t *json_sim_data = ulfius_get_json_body_request(request, NULL);

	if (getTopologyStatus() == false)
	{
		json_object_set_new(json_body, "status", json_string("not running"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL \n");
		return U_CALLBACK_CONTINUE;
	}

	char *topoid = NULL, *toponame = NULL;
	topoid = (char *)json_string_value(json_object_get(json_sim_data, "topology-id"));
	toponame = (char *)json_string_value(json_object_get(json_sim_data, "topology-name"));

	cout << " [ topo id  : " << topoid << ", name  : " << toponame << " ]" << endl;

	if (topoid == NULL)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	if (getTopologyStatus(atoi(topoid)) != true)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	

	bool simstat = stopSimulation();
	if (simstat == false)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("STOP Simualtion - FAILED \n");
		return U_CALLBACK_CONTINUE;
	}

	int ret = RestSend("QNS", QConfig.GetServerURL(QQC_SERVER).c_str(), URL_STOP_TOPOLOGY, json_sim_data);
	if (ret == 0)
	{
		json_object_set_new(json_body, "status", json_string("success"));
	}
	else
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL \n");
		return U_CALLBACK_CONTINUE;
	}

	setTopologyStatus(false);
	ulfius_set_json_body_response(response, 200, json_body);
	return 0;
}


int callback_StatusTopology(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();
	json_t *json_sim_data = ulfius_get_json_body_request(request, NULL);

	int ret = RestSend("QNS", QConfig.GetServerURL(QQC_SERVER).c_str(), URL_STATUS_TOPOLOGY, json_body);
	if (ret == 0)
	{
		cout << "QQC (Sequence) - Status Topology " << endl;
	}
	else
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	bool simstat = getTopologyStatus();

	switch (simstat)
	{
	case true:
		json_object_set_new(json_body, "status", json_string("running"));
		printf("JSON Data Posted - Status : RUNNING\n");
		break;
	case false:
		json_object_set_new(json_body, "status", json_string("not running"));
		printf("JSON Data Posted - Status : NOT RUNNING\n");
		break;
	}
	ulfius_set_json_body_response(response, 200, json_body);
	return U_CALLBACK_CONTINUE;
}


int callback_nodelinkdetails(const struct _u_request *request, struct _u_response *response, void *user_data)
{
	json_t *json_body = json_object();
	json_t *json_sim_data = ulfius_get_json_body_request(request, NULL);
	char *topoid = NULL, *toponame = NULL;
	topoid = (char *)json_string_value(json_object_get(json_sim_data, "topology-id"));
	toponame = (char *)json_string_value(json_object_get(json_sim_data, "topology-name"));
	if (topoid == NULL)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}

	if (getTopologyStatus(atoi(topoid)) != true)
	{
		json_object_set_new(json_body, "status", json_string("fail"));
		ulfius_set_json_body_response(response, 200, json_body);
		printf("JSON Data Posted - Status : FAIL\n");
		return U_CALLBACK_CONTINUE;
	}
	
	json_object_set_new(json_body, "nodes", getNodesDetails());
	json_object_set_new(json_body, "links",getLinksDetails());
	ulfius_set_json_body_response(response, 200, json_body);
	return U_CALLBACK_CONTINUE;
}
