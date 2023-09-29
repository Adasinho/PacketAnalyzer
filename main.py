import pyshark
from pyshark import FileCapture
import dpkt
import socket
from typing import Union

UNITY_SERVER_PORT = "50000"
UNREAL_SERVER_PORT = "7777"

class AddressStats:
    def __init__(self, address: str, port: str):
        self.address = address
        self.port = port
        self.startTime = None
        self.endTime = None
        self.numberOfInPackets = 0
        self.numberOfOutPackets = 0
    
    def addInPacket(self, time: int) -> None:
        self.numberOfInPackets += 1
        
        if self.startTime == None:
            self.startTime = time
        
        self.endTime = time
        
    def addOutPacket(self, time: int) -> None:
        self.numberOfOutPackets += 1
        
        if self.startTime == None:
            self.startTime = time
            
        self.endTime = time
        
    def getInPacketsNumber(self) -> int:
        return self.numberOfInPackets
    
    def getOutPacketsNumber(self) -> int:
        return self.numberOfOutPackets

class PacketCounter:
    def __init__(self):
        self.addresses = {}
        
    def addIncomming(self, address: str, port: str, time: int) -> None:
        ipAndPort = address + ":" + port
        addressStats: AddressStats = self.addresses.get(ipAndPort) if self.addresses.get(ipAndPort) else AddressStats(address, port)
        addressStats.addInPacket(time)

        self.addresses[ipAndPort] = addressStats
        
    def addOutcomming(self, address: str, port: str, time: int) -> None:
        ipAndPort = address + ":" + port
        addressStats: AddressStats = self.addresses.get(ipAndPort) if self.addresses.get(ipAndPort) else AddressStats(address, port)
        addressStats.addOutPacket(time)
        
        self.addresses[ipAndPort] = addressStats
        
    def getAddressesStats(self) -> Union[str, AddressStats]:
        return self.addresses.items()

class PacketStats:
    def __init__(self):
        self.statsInMinutes = {}
        self.generalStats = PacketCounter()
        self.startMinute = None
        self.allInPackets = 0
        self.allOutPackets = 0
        self.biggestPacketSize = None
        self.smallestPacketSize = None
        self.totalInPacketsSize = 0
        self.totalOutPacketsSize = 0
        self.lastInPacketTime = None
        self.lastOutPacketTime = None
        self.timeDistributionInPackets = 0
        self.timeDistributionOutPackets = 0
        self.lastInPacketSize = None
        self.lastOutPacketSize = None
        self.sizeDistributionInPackets = 0
        self.sizeDistributionOutPackets = 0
        
    def addInPacket(self, second: int, packetIp: str, packetPort: str, packetSize: int):
        if self.startMinute == None:
            # in minutes
            self.startMinute = second // 60
        
        if self.biggestPacketSize == None: self.biggestPacketSize = packetSize
        elif self.biggestPacketSize < packetSize: self.biggestPacketSize = packetSize
            
        if self.smallestPacketSize == None: self.smallestPacketSize = packetSize
        elif self.smallestPacketSize > packetSize: self.smallestPacketSize = packetSize
        
        self.totalInPacketsSize += packetSize
        
        if self.lastInPacketSize == None: self.lastInPacketSize = packetSize
        else: self.sizeDistributionInPackets += packetSize - self.lastInPacketSize
            
        fixedMinuteTime = second // 60 - self.startMinute + 1
        
        if self.lastInPacketTime == None: self.lastInPacketTime = second
        else: self.timeDistributionInPackets += second - self.lastInPacketTime
        
        if(self.statsInMinutes.get(str(fixedMinuteTime)) == None):
            self.statsInMinutes[str(fixedMinuteTime)] = PacketCounter()
            
        packetCounter: PacketCounter = self.statsInMinutes[str(fixedMinuteTime)]
        packetCounter.addIncomming(packetIp, packetPort, second)
        self.generalStats.addIncomming(packetIp, packetPort, second)
        
        self.allInPackets += 1
        
    def addOutPacket(self, second: int, packetIp: str, packetPort: str, packetSize: int):
        if self.startMinute == None:
            self.startMinute = second // 60
            
        if self.biggestPacketSize == None: self.biggestPacketSize = packetSize
        elif self.biggestPacketSize < packetSize: self.biggestPacketSize = packetSize
            
        if self.smallestPacketSize == None: self.smallestPacketSize = packetSize
        elif self.smallestPacketSize > packetSize: self.smallestPacketSize = packetSize
        
        self.totalOutPacketsSize += packetSize
        
        if self.lastOutPacketSize == None: self.lastOutPacketSize = packetSize
        else: self.sizeDistributionOutPackets += packetSize - self.lastOutPacketSize
            
        fixedMinuteTime = second // 60 - self.startMinute + 1
        
        if self.lastOutPacketTime == None: self.lastOutPacketTime = second
        else: self.timeDistributionOutPackets += second - self.lastOutPacketTime
        
        if(self.statsInMinutes.get(str(fixedMinuteTime)) == None):
            self.statsInMinutes[str(fixedMinuteTime)] = PacketCounter()
            
        packetCounter: PacketCounter = self.statsInMinutes[str(fixedMinuteTime)]
        packetCounter.addOutcomming(packetIp, packetPort, second)
        self.generalStats.addOutcomming(packetIp, packetPort, second)
        self.allOutPackets += 1
        
    def getPacketsFromMinute(self, minute: int) -> PacketCounter:
        return self.statsInMinutes.get(str(minute))
        
    def printStats(self):
        for minute in self.statsInMinutes:
            print(f"\nPakiety w {minute} minucie działania")
            print(f"Wysłane pakiety")
            
            countedPackets: PacketCounter = self.statsInMinutes.get(str(minute))
            for dictionary in countedPackets.getAddressesStats():
                address: str = dictionary[0]
                addressStats: AddressStats = dictionary[1]
                
                print(f"{address}: {addressStats.getOutPacketsNumber()}")
                
            print(f"\nOdbierane pakiety")
            for dictionary in countedPackets.getAddressesStats():
                address: str = dictionary[0]
                addressStats: AddressStats = dictionary[1]
                
                print(f"{address}: {addressStats.getInPacketsNumber()}")
                
    def printCountOfAllPackets(self):            
        print(f"\nŁączna ilość pakietów")
        print(f"Wysłane pakiety: {self.allOutPackets}")
        print(f"Odebrane pakiety: {self.allInPackets}")
        
    def printServerAveragePacketsPerSecond(self, time: int):
        print(f"\nŚrednia ilość pakietów na sekundę przez server")
        print(f"Wysłane pakiety: {self.allOutPackets / time}")
        print(f"Odebrane pakiety: {self.allInPackets / time}")
        
    def printClientAveragePacketsPerSecond(self):
        print(f"\nŚrednia ilość pakietów na sekundę przez klienta")
        
        numberOfPacketsPerSecond = 0
        
        for dictionary in self.generalStats.getAddressesStats():
            addressStats: AddressStats = dictionary[1]
            numberOfPacketsPerSecond += addressStats.getOutPacketsNumber() / (addressStats.endTime - addressStats.startTime)
        
        print(f"Wysłane pakiety na sekunde: {numberOfPacketsPerSecond / len(self.generalStats.getAddressesStats())}")
        
        numberOfPacketsPerSecond = 0
        
        for dictionary in self.generalStats.getAddressesStats():
            addressStats: AddressStats = dictionary[1]
            numberOfPacketsPerSecond += addressStats.getInPacketsNumber() / (addressStats.endTime - addressStats.startTime)
        
        print(f"Odebrane pakiety na sekunde: {numberOfPacketsPerSecond / len(self.generalStats.getAddressesStats())}")

    def printPacketsSizes(self):
        print(f"\nRozmiary pakietów")
        print(f"Największy pakiet: {self.biggestPacketSize} bajtów")
        print(f"Najmniejszy pakiet: {self.smallestPacketSize} bajtów")
        
    def printTotalPacketsSize(self):
        print(f"\nSuma rozmiarów pakietów")
        print(f"Suma rozmiarów wysłanych pakietów: {self.totalOutPacketsSize} bajtów")
        print(f"Suma rozmiarów odebranych pakietów: {self.totalInPacketsSize} bajtów")

    def printAveragePacketSize(self):
        print(f"\nŚredni rozmiar pakietów")
        print(f"Wysyłanego pakietu: {self.totalOutPacketsSize / self.allOutPackets} bajtów")
        print(f"Odbieranego pakietu: {self.totalInPacketsSize / self.allInPackets} bajtów")

    def printTimeDistribution(self):
        print(f"\nRozkład czasu między pakietami")
        print(f"Wysyłanymi pakietami: {self.timeDistributionOutPackets / (self.totalOutPacketsSize - 1)} sekund")
        print(f"Odbieranymi pakietami: {self.timeDistributionInPackets / (self.totalInPacketsSize - 1)} sekund")

    def printSizeDistribution(self):
        print(f"\nRozdkład rozmiaru między pakietami")
        print(f"Wysyłanymi pakietami: {self.sizeDistributionOutPackets / (self.totalOutPacketsSize - 1)} bajtów")
        print(f"Odbieranymi pakietami: {self.sizeDistributionInPackets / (self.totalInPacketsSize - 1)} bajtów")

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
                packetSize = len(buf)
                eth = dpkt.ethernet.Ethernet(buf)
                if isinstance(eth.data, dpkt.ip.IP):
                    ip_data = eth.data
                    src_ip = socket.inet_ntoa(ip_data.src)
                    dst_ip = socket.inet_ntoa(ip_data.dst)
                    
                    udp_data = ip_data.data
                    
                    src_port = str(udp_data.sport)
                    dst_port = str(udp_data.dport)
                    
                    # Konwertowanie znacznika czasu na minutę (ignorujemy sekundy i frakcje sekundy)
                    second = int(ts)
                    
                    if not bannedPorts(dst_port):
                        packetsStats.addInPacket(second, dst_ip, dst_port, packetSize)
                    
                    if not bannedPorts(src_port):
                        packetsStats.addOutPacket(second, src_ip, src_port, packetSize)

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

path = "C:\\Users\\Adasinho\\Desktop\\TestyOnlineWyniki\\Server\\UnrealEngine\\output_2023-09-11_19-14-29.pcap"

durationTime = testDuration(path)
print(f"\nCzas trwania testu w sekundach: {durationTime}")

ipAddresses = getIPAddresses(path)
print("Adresy biorące udział w teście")
printAddresses(ipAddresses)

packetStats: PacketStats = countPackets(path)
packetStats.printCountOfAllPackets()
packetStats.printServerAveragePacketsPerSecond(durationTime)
packetStats.printClientAveragePacketsPerSecond()
#packetStats.printStats()

packetStats.printPacketsSizes()
packetStats.printTotalPacketsSize()
packetStats.printAveragePacketSize()
packetStats.printTimeDistribution()
packetStats.printSizeDistribution()