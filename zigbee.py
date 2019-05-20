import sys
import signal
import socket
from struct import *
import argparse
import os

from scapy.all import *
from killerbee import *
from killerbee.scapy_extensions import *

'''
Note because of killerbee this must be a python 2 module.
We'll relate events over UDP to our python3 processes
'''

def detect_encryption(pkt):
    '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
    if not pkt.haslayer(ZigbeeSecurityHeader) or not pkt.haslayer(ZigbeeNWK):
        return False
    return True

def detect_layer(pkt, layer):
    '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
    # if not pkt.haslayer(ZigbeeAppDataPayload):
    if not pkt.haslayer(layer):
        return False
    return True

def interrupt(signum, frame):
    global packetcount
    global kb
    kb.sniffer_off()
    kb.close()

    print ("{0} Zigbee packets captured".format(packetcount))
    sys.exit(0)

# Known devices
known_sources = {
    6623462419764822: "Living Room Sensor",
    6623462419746382: "Kitchen Sensor"
}

# UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 5005 # Ugh can't import from python3 land
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

# Global
packetcount = 0
network_key = "270aa9e33947363feea6e52167c107cf".decode('hex')
channel = 25

subghz_page = 0
device = None # Auto select?

kb = KillerBee(device=device)
signal.signal(signal.SIGINT, interrupt)
if not kb.is_valid_channel(channel, subghz_page):
    print >> sys.stderr, "ERROR: Must specify a valid IEEE 802.15.4 channel for the selected device."
    kb.close()
    sys.exit(1)
kb.set_channel(channel, subghz_page)
kb.sniffer_on()

rf_freq_mhz = kb.frequency(channel, subghz_page) / 1000.0
print (
    "Zigbee: listening on \'{0}\', channel {1}, page {2} ({3} MHz), link-type DLT_IEEE802_15_4, capture size 127 bytes".format(
        kb.get_dev_info()[0], channel, subghz_page, rf_freq_mhz))

# Unit conversion constants

LUMINANCE_TO_LUX = 0.0010171925257971555

def celsius_to_fahrenheit(celsius):
    return (celsius * 9 / 5.0) + 32

while True:
    packet = kb.pnext()
    # packet[1] is True if CRC is correct, check removed to have promiscous capture regardless of CRC
    # if PAN filter active, only process correct PAN or ACK
    scapy_packet = None
    if packet:
        scapy_packet = Dot15d4FCS(packet['bytes'])
    if scapy_packet is not None:  # and packet[1]:
        packetcount += 1
        # unbuffered.write("Packet " + packet['bytes'].encode('hex') + "\n")
        if detect_layer(scapy_packet, ZigbeeSecurityHeader):
            source = scapy_packet.getlayer(ZigbeeSecurityHeader).fields['source']
            if source in known_sources:
                # Data from motion sensor
                name = known_sources[source]
                if detect_encryption(scapy_packet):
                    enc_data = kbdecrypt(scapy_packet, network_key)
                    # First determine if this is an occupancy sensing
                    if detect_layer(enc_data, ZigbeeAppDataPayload) and detect_layer(enc_data,
                                                                                     ZigbeeClusterLibrary):
                        app_bytes = enc_data.getlayer(ZigbeeAppDataPayload).payload.__bytes__()
                        cluster_bytes = enc_data.getlayer(ZigbeeClusterLibrary).payload.__bytes__()
                        # Occupancy Sensing
                        if app_bytes[:4] == '\x06\x04\x04\x01':  # Cluster: Occupancy Sensing (0x0406), Profile: Home Automation (0x0104)
                            # print "\t"*3 + "enc cluster: " + str(cluster) + " raw: " + enc_data.getlayer(a).payload.__bytes__().encode('hex')
                            if cluster_bytes[-4:-1] == '\x00\x00\x18':  # Occupancy Sensing, 8-Bit bitmap
                                is_motion_start = cluster_bytes[-1] == '\x01'
                                print "%s motion %r" % (name, is_motion_start)
                                sock.sendto("motion-%d-%d" % (source, is_motion_start), (UDP_IP, UDP_PORT))
                            else:
                                print "Unknown Motion packet. Cluster: %s" % cluster_bytes.encode('hex')
                        elif app_bytes[:4] == '\x00\x04\x04\x01':  # Cluster: Illuminance Measurement (0x0400), Profile: Home Automation (0x0104)
                            if cluster_bytes[-5:-2] == '\x00\x00\x21':  # Measured Value, 16-Bit Unsigned Int
                                luminance_raw = unpack('<h', cluster_bytes[-2:])[0]
                                luminance_lux = luminance_raw * LUMINANCE_TO_LUX
                                print "Room %s luminance %f" % (name, luminance_lux)
                                sock.sendto("luminance-%d-%f" % (source, luminance_lux), (UDP_IP, UDP_PORT))
                            else:
                                print "Unknown Luminance packet. Cluster: %s" % cluster_bytes.encode('hex')
                        elif app_bytes[
                             :4] == '\x02\x04\x04\x01':  # Cluster: Temperature Measurement (0x0402), Profile: Home Automation (0x0104)
                            if cluster_bytes[-5:-2] == '\x00\x00\x29':  # Measured Value, 16-Bit Signed Int
                                temperature_raw = unpack('<h', cluster_bytes[-2:])[0]
                                temp_celsius = temperature_raw / 100.0
                                temp_fahrenheit = celsius_to_fahrenheit(temp_celsius)
                                print "Room %s Temperature %f Fahrenheit" % (name, temp_fahrenheit)
                                sock.sendto("temp-%d-%f" % (source, temp_fahrenheit), (UDP_IP, UDP_PORT))
                            else:
                                print "Unknown Temperature packet. Cluster: %s" % cluster_bytes.encode('hex')

kb.sniffer_off()
kb.close()

print "{0} packets captured".format(packetcount)