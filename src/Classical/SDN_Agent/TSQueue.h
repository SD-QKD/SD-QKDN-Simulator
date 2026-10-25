#ifndef TSQUEUE_H
#define TSQUEUE_H
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/internet-module.h"
#include "ns3/csma-module.h"
#include "ns3/point-to-point-module.h"
#include <condition_variable> 
#include <iostream> 
#include <mutex> 
#include <queue> 
#include <ns3/socket.h>
#include <ns3/tcp-socket.h>
#include <ns3/tcp-socket-factory.h>
#include <ns3/inet-socket-address.h>
#include <ns3/inet6-socket-address.h>
#include <ns3/ptr.h>
#include <ns3/application.h>

using namespace std;

namespace ns3
{
template <typename T> 
class TSQueue { 
private: 
	std::queue<T> m_queue; 
	std::mutex m_mutex; 
	std::condition_variable m_cond; 

public: 
	void push(T item) 
	{ 
		std::unique_lock<std::mutex>  lck(m_mutex); 
		m_queue.push(item); 
		lck.unlock();
		m_cond.notify_one(); 
	} 

	T blocking_pop() 
	{ 
		std::unique_lock<std::mutex> lck(m_mutex); 
		
		m_cond.wait(lck, [this]() { return !m_queue.empty(); }); 
		T item = m_queue.front(); 
		m_queue.pop(); 
		lck.unlock();
		return item; 
	} 
	
	T non_blocking_pop() 
	{ 

		std::unique_lock<std::mutex> lck(m_mutex); 
		if(m_queue.size()<1)
		{
			lck.unlock();
			return NULL;
		}
		else
		{
			T item = m_queue.front(); 
			m_queue.pop(); 
			lck.unlock();
			return item; 
		}
	}

	T blocking_front() 
	{ 
		std::unique_lock<std::mutex> lck(m_mutex); 
		m_cond.wait(lck, [this]() { return !m_queue.empty(); }); 
		T item = m_queue.front(); 
		lck.unlock();
		return item; 
	}
	


	T non_blocking_front() 
	{ 
		std::unique_lock<std::mutex> lck(m_mutex); 
		if(m_queue.size()<1)
		{
			lck.unlock();
			return NULL;
		}
		else
		{
			T item = m_queue.front(); 
			lck.unlock();
			return item; 
		}
	} 

    bool empty()
    {
        return m_queue.empty();
    }
    int size()
    {
		std::unique_lock<std::mutex> lck(m_mutex); 
		int size = m_queue.size();
		lck.unlock();
        return size;
    }
}; 

}
#endif
