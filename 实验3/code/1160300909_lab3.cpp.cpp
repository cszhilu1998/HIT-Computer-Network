/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include "sysInclude.h"

extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

// implemented by students

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

/**
receive packet from MAC

pBuffer: pointer to IPv4 packet group header (char 8 bit/1 Byte)
length: IPv4 group length
**/
int stud_ip_recv(char *pBuffer,unsigned short length)
{
    if((pBuffer[0] & 0xf0) != 0x40) //check Version
    {
        ip_DiscardPkt(pBuffer,STUD_IP_TEST_VERSION_ERROR);
		return 1;
    }
    if((pBuffer[0] & 0x0f) != 0x05) //check IP Head length (4 Bytes/unit)
    {
        ip_DiscardPkt(pBuffer,STUD_IP_TEST_HEADLEN_ERROR);
		return 1;
    }
    if(pBuffer[8] == 0x00)  //check TTL
    {
        ip_DiscardPkt(pBuffer,STUD_IP_TEST_TTL_ERROR);
		return 1;
    }
    unsigned short checksum = checksum0((unsigned short *)pBuffer,20);
    if(checksum != 0)  //check Header checksum
    {
        ip_DiscardPkt(pBuffer,STUD_IP_TEST_CHECKSUM_ERROR);
		return 1;
    }
    //check destination ip
    unsigned int address = getIpv4Address(); //get local host ip
    char *tempAddress = pBuffer+16; //dest ip address in ipv4
    unsigned int *intAddress = (unsigned int *)tempAddress;
    if(address != ntohl(*intAddress)) //ntohl:network to host long
    {
        ip_DiscardPkt(pBuffer,STUD_IP_TEST_DESTINATION_ERROR);
		return 1;
    }
    ip_SendtoUp(pBuffer,length); //pay for up level
	return 0;
}

/**
send packet to lower level

pBuffer: Pointer to the send buffer, pointing to the IPv4 upper layer protocol data header
Len: IPv4 upper layer protocol data length
srcAddr: source IPv4 address
dstAddr: destination IPv4 address
Protocol: IPv4 upper layer protocol number
Ttl: Time To Live
**/
int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
                   unsigned int dstAddr,byte protocol,byte ttl)
{
    byte *datagram = new byte[20+len]; //acllocate memory (Byte/unit)

    datagram[0] = 0x45; //version=ipv4 IHL=5 (4Byte/unit)
    datagram[1] = 0x00; //Type of service = 0x00

    byte *total_length = datagram+2; //Total Length
    unsigned short int *length = (unsigned short int *)total_length;
    *length = htons(20+len); //host to network(short)

    datagram[4] = 0x00; //identification random num
	datagram[5] = 0x00; //identification random num

	datagram[6] = 0x00; //flag(3bits) and offset(13 offsets)
	datagram[7] = 0x00; //flag(3bits) and offset(13 offsets)

	datagram[8] = ttl; //ttl

	datagram[9] = protocol;  //up level protocol

	datagram[10] = 0x00; //checksum set 0x0000 initial
	datagram[11] = 0x00; //checksum set 0x0000 initial

    byte *datagram_srcAddr = datagram+12;  //src ip address
    unsigned int *srcAddrTemp = (unsigned int *)datagram_srcAddr;
    *srcAddrTemp = ntohl(srcAddr);

    byte *datagram_dstAddr = datagram+16; //dest ip address
    unsigned int *dstAddrTemp = (unsigned int *)datagram_dstAddr;
    *dstAddrTemp = ntohl(dstAddr);

    byte *datagram_cksum = datagram+10; //checksum
    short int *headerChecksum = (short int *)datagram_cksum;
    *headerChecksum = checksum0((unsigned short *)datagram,20);

    for(int i=0;i<len;i++)  //add header
    {
        datagram[i+20] = pBuffer[i];
    }

    ip_SendtoLower(datagram,20+len); //send to lower level
	return 0;
}
