import pyshark
from pyshark import FileCapture
import dpkt
import socket

UNITY_SERVER_PORT = "50000"
UNREAL_SERVER_PORT = "7777"

# Otwieranie pliku pcap
cap = pyshark.FileCapture("C:\\Users\\adirm\\OneDrive\\Documents\\TestyOnlineWyniki\\Server\\UnrealEngine\\output_2023-09-11_19-14-29.pcap")

class PacketCounter:
    def __init__(self):
        self.incomming = {}
        self.outcomming = {}
        
    #def __init__(self, initAddresses: list):
    #    self.incomming = {}
    #    self.outcomming = {}
    #    
    #    for address in initAddresses:
    #        self.incomming[address] = 0
    #        self.outcomming[address] = 0
        
    def addIncomming(self, address: str, port: str):
        ipAndPort = address + ":" + port
        self.incomming[ipAndPort] = self.incomming.get(ipAndPort, 0) + 1
        
    def addOutcomming(self, address: str, port: str):
        ipAndPort = address + ":" + port
        self.outcomming[ipAndPort] = self.outcomming.get(ipAndPort, 0) + 1

class PacketStats:
    def __init__(self):
        self.statsInMinutes = {}
        self.startTime = None
        
    def addInPacket(self, minute: int, packetIp: str, packetPort: str):
        if self.startTime == None:
            self.startTime = minute
            
        fixedTime = minute - self.startTime + 1
        
        if(self.statsInMinutes.get(str(fixedTime)) == None):
            self.statsInMinutes[str(fixedTime)] = PacketCounter()
            
        packetCounter: PacketCounter = self.statsInMinutes[str(fixedTime)]
        packetCounter.addIncomming(packetIp, packetPort)
        
    def addOutPacket(self, minute: int, packetIp: str, packetPort: str):
        if self.startTime == None:
            self.startTime = minute
            
        fixedTime = minute - self.startTime + 1
        
        if(self.statsInMinutes.get(str(fixedTime)) == None):
            self.statsInMinutes[str(fixedTime)] = PacketCounter()
            
        packetCounter: PacketCounter = self.statsInMinutes[str(fixedTime)]
        packetCounter.addOutcomming(packetIp, packetPort)
        
    def printStats(self):
        for minute in self.statsInMinutes:
            print(f"\nPakiety w {minute} minucie działania")
            print(f"Wysłane pakiety")
            
            countedPackets: PacketCounter = self.statsInMinutes.get(str(minute))
            for address, counter in countedPackets.outcomming.items():
                print(f"{address}: {counter}")
                
            print(f"\nOdbierane pakiety")
            
            for address, counter in countedPackets.incomming.items():
                print(f"{address}: {counter}")

def bannedPorts(port: int) -> bool:
    return port == UNITY_SERVER_PORT or port == UNREAL_SERVER_PORT

def printAddresses(addresses: list):
    for address in addresses:
        print(f"{address}")

def getIPAddresses(filePath: str) -> list:
    with open(filePath, 'rb') as f:
        pcap = dpkt.pcap.Reader(f)
        ipAddresses = set()
        
        for _, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                if isinstance(eth.data, dpkt.ip.IP):
                    ip_data = eth.data
                    
                    src_data = socket.inet_ntoa(ip_data.src)
                    dst_data = socket.inet_ntoa(ip_data.dst)
                    
                    udp_data = ip_data.data
                    
                    src_port = str(udp_data.sport)
                    dst_port = str(udp_data.dport)
                    
                    if not bannedPorts(src_port):
                        ipAddresses.add(src_data + ":" + src_port)
                    
                    if not bannedPorts(dst_port):
                        ipAddresses.add(dst_data + ":" + dst_port)
            except:
                continue

    return list(ipAddresses)

def countPackets(filePath: str) -> PacketStats:
    #packetsCounter = PacketCounter(addresses)
    packetsStats = PacketStats()
    
    with open(filePath, 'rb') as f:
        pcap = dpkt.pcap.Reader(f)

        for ts, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                if isinstance(eth.data, dpkt.ip.IP):
                    ip_data = eth.data
                    src_ip = socket.inet_ntoa(ip_data.src)
                    dst_ip = socket.inet_ntoa(ip_data.dst)
                    
                    udp_data = ip_data.data
                    
                    src_port = str(udp_data.sport)
                    dst_port = str(udp_data.dport)
                    
                    # Konwertowanie znacznika czasu na minutę (ignorujemy sekundy i frakcje sekundy)
                    minute = int(ts) // 60
                    
                    # Aktualizacja słowników
                    #packetsCounter.addIncomming(dst_ip, dst_port)
                    #packetsCounter.addOutcomming(src_ip, src_port)
                    if not bannedPorts(dst_port):
                        packetsStats.addInPacket(minute, dst_ip, dst_port)
                    
                    if not bannedPorts(src_port):
                        packetsStats.addOutPacket(minute, src_ip, src_port)

            except Exception as e:
                print(f"Błąd przetwarzania pakietu: {e}")
                continue

    return packetsStats

def testDuration(filePath: str) -> int:
    with open(filePath, 'rb') as f:
        pcap = dpkt.pcap.Reader(f)
        
        # Ustalamy początkowe wartości na None
        startTime = None
        endTime = None

        for ts, _ in pcap:
            if startTime is None:
                startTime = ts
            endTime = ts

        # Obliczanie różnicy czasu
        if startTime is not None and endTime is not None:
            timeDifference = endTime - startTime
            return timeDifference
        else:
            return 0

path = 'C:\\Users\\adirm\\OneDrive\\Documents\\TestyOnlineWyniki\\Server\\UnrealEngine\\output_2023-09-11_19-14-29.pcap'
#wszystkie_adresy = getIPAddresses(sciezka)
#print(wszystkie_adresy)

ipAddresses = getIPAddresses(path)
print("Adresy biorące udział w teście")
printAddresses(ipAddresses)

packetStats: PacketStats = countPackets(path)
packetStats.printStats()

#print("\nPakiety wysłane:")
#for address, liczba in countedPackets.outcomming.items():
#    print(f"{address}: {liczba}")

#print("\nPakiety odebrane:")
#for address, liczba in countedPackets.incomming.items():
#    print(f"{address}: {liczba}")

czas_trwania = testDuration(path)
print(f"\nCzas trwania testu w sekundach: {czas_trwania}")

