/*
* THIS FILE IS FOR IP FORWARD TEST
*/
#include "sysInclude.h"
#include <vector>
#include <algorithm>
using std::vector;

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students

/**set Route Node **/
struct RNode
{
	int dest;    //Destination network address
	int masklen; //Mask length
	int nexthop; //Next hop
	RNode(int d=0, int m=0, int n=0):
	    dest(d), masklen(m), nexthop(n){}
};

/** vector routeTable **/
vector<RNode> routeTable;

/** Initialize the routing table **/
void stud_Route_Init()
{
	routeTable.clear();
	return;
}

/** sort by hostip or mask length **/
bool cmp(const RNode & a, const RNode & b)
{
	if(htonl(a.dest) > htonl(b.dest))
	{
		return true;
	}
	else if(htonl(a.dest) == htonl(b.dest)) //According to the longest match
	{
		return htonl(a.masklen) > htonl(b.masklen);
	}
	else
	{
		return false;
	}
}

/** Add routing information to the routing table **/
void stud_route_add(stud_route_msg *proute)
{
	int dest;
	routeTable.push_back(RNode(ntohl(proute->dest), ntohl(proute->masklen), ntohl(proute->nexthop)));
	sort(routeTable.begin(), routeTable.end(), cmp);
	return;
}

/** Calculate the sent IPv4 packet checksum **/
short checksum0(unsigned short *buffer,int length)
{
    unsigned long checksum = 0;
    while(length > 1)
    {
        checksum += *buffer++;
        length -= sizeof(unsigned short);
    }
    if(length)
    {
        checksum += *(unsigned char *)buffer;
    }
    checksum = (checksum>>16) + (checksum & 0xffff);
    checksum += (checksum>>16);
    return (unsigned short)(~checksum);
}

/** Handling received IP packets **/
int stud_fwd_deal(char *pBuffer, int length)
{
	int version = pBuffer[0] >> 4; //get version
	int ihl = pBuffer[0] & 0xf; //get IP packet header length
	int ttl = (int)pBuffer[8]; //get TTL

	int dstIP = ntohl(*(unsigned int*)(pBuffer + 16)); //get Destination IP address
	if(dstIP == getIpv4Address()) //IP packet received by this machine
	{
		fwd_LocalRcv(pBuffer, length);
		return 0;
	}

	if(ttl <= 0)
	{
		fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
		return 1;
	}

    //Look up the routing table to get the next hop and calculate checksum
	for(vector<RNode>::iterator ii = routeTable.begin(); ii != routeTable.end(); ii++)
	{
		if(ii->dest == dstIP)
		{
			char *buffer = new char[length];
			memcpy(buffer, pBuffer, length);
			buffer[8]--; //TTL--
			buffer[10] = 0;
			buffer[11] = 0; //checksum=0
			unsigned short int localCheckSum = checksum0((unsigned short *)buffer,20);
			memcpy(buffer+10, &localCheckSum, sizeof(short unsigned int));
			fwd_SendtoLower(buffer, length, ii->nexthop);
			return 0;
		}
	}
	fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE); //Look for failure
	return 1;
}
