#!/usr/bin/env python3
import argparse
import grpc
import os
import sys
from time import sleep

from scapy.all import Ether

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper


def writeIpv4_lpmRules(p4info_helper, sw, match_fields, action_params):

    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ipv4_lpm",
        match_fields={
            "hdr.ipv4.dstAddr": match_fields
        },
        action_name="MyIngress.ipv4_forward",
        action_params=action_params
        )
    sw.WriteTableEntry(table_entry)

def writeCheck_ecnRules(p4info_helper, sw, action_params):

    table_entry = p4info_helper.buildTableEntry(
        table_name="MyEgress.check_ecn",
        action_name="MyEgress.mark_ecn",
        action_params=action_params,
        default_action=True
        )
    sw.WriteTableEntry(table_entry)
    
def writeCloneRules(p4info_helper, sw, clone_session_id, replicas): 
    
    SessionEntry = p4info_helper.buildCloneSessionEntry(
        clone_session_id = clone_session_id,
        replicas = replicas
        )
    sw.WritePREEntry(SessionEntry)

import struct
eth_header_format = "!6s6sH"  
cpu_header_format = "!B"  

eth_header_length = struct.calcsize(eth_header_format)  
cpu_header_offset = eth_header_length  

def print_bytes_hex(byte_data):
    hex_str_list = [f'\\x{b:02x}' for b in byte_data]
    hex_str = ''.join(hex_str_list)
    print(hex_str)
    
def fetch_responses(connection):
    try:
        for response in connection.stream_msg_resp:
            # handle the response
            print("Received response-----")
            if response.WhichOneof("update") == "packet":
                packet = response.packet.payload
                #print(len(packet))
                #print_bytes_hex(packet);
                #print(eth_header_length)
                #print(cpu_header_offset)
                
                cpu_header = packet[cpu_header_offset:cpu_header_offset+1]
                ecn = struct.unpack(cpu_header_format, cpu_header)[0]
                
                print("ECN value:", ecn)
                if ecn == 3:
                    print('Congestion happens!!')
    except grpc.RpcError as e:
        pass

def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create a switch connection object for s1, s2 and s3;
        # this is backed by a P4Runtime gRPC connection.
        # Also, dump all P4Runtime messages sent to switch to given txt files.
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
            proto_dump_file='logs/s1-p4runtime-requests.txt')
        s2 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s2',
            address='127.0.0.1:50052',
            device_id=1,
            proto_dump_file='logs/s2-p4runtime-requests.txt')
        s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s3',
            address='127.0.0.1:50053',
            device_id=2,
            proto_dump_file='logs/s3-p4runtime-requests.txt')
        
        threshold = input("Please input the threshold of the queue: ")
        threshold = eval(threshold)
        
        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        s1.MasterArbitrationUpdate()
        s2.MasterArbitrationUpdate()
        s3.MasterArbitrationUpdate()

        # Install the P4 program on the switches
        s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)
        s2.SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)
        s3.SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)
       

        # Write ipv4_lpm table entries to s1,s2,s3
        writeIpv4_lpmRules(p4info_helper, s1, ["10.0.1.1", 32], {"dstAddr": "08:00:00:00:01:01", "port": 2})
        writeIpv4_lpmRules(p4info_helper, s1, ["10.0.1.11", 32], {"dstAddr": "08:00:00:00:01:11", "port": 1})
        writeIpv4_lpmRules(p4info_helper, s1, ["10.0.2.0", 24], {"dstAddr": "08:00:00:00:02:00", "port": 3})
        writeIpv4_lpmRules(p4info_helper, s1, ["10.0.3.0", 24], {"dstAddr": "08:00:00:00:03:00", "port": 4})
        
        writeIpv4_lpmRules(p4info_helper, s2, ["10.0.2.2", 32], {"dstAddr": "08:00:00:00:02:02", "port": 2})
        writeIpv4_lpmRules(p4info_helper, s2, ["10.0.2.22", 32], {"dstAddr": "08:00:00:00:02:22", "port": 1})
        writeIpv4_lpmRules(p4info_helper, s2, ["10.0.1.0", 24], {"dstAddr": "08:00:00:00:01:00", "port": 3})
        writeIpv4_lpmRules(p4info_helper, s2, ["10.0.3.0", 24], {"dstAddr": "08:00:00:00:03:00", "port": 4})
        
        writeIpv4_lpmRules(p4info_helper, s3, ["10.0.3.3", 32], {"dstAddr": "08:00:00:00:03:03", "port": 1})
        writeIpv4_lpmRules(p4info_helper, s3, ["10.0.1.0", 24], {"dstAddr": "08:00:00:00:01:00", "port": 2})
        writeIpv4_lpmRules(p4info_helper, s3, ["10.0.2.0", 24], {"dstAddr": "08:00:00:00:02:00", "port": 3})

        # Write swtrace table entries to s1,s2,s3
        writeCheck_ecnRules(p4info_helper, s1, {"ecn_threshold": threshold})
        writeCheck_ecnRules(p4info_helper, s2, {"ecn_threshold": threshold})
        writeCheck_ecnRules(p4info_helper, s3, {"ecn_threshold": threshold})
        
        writeCloneRules(p4info_helper, s1, 100, [{"egress_port": 252, "instance": 1}])
        writeCloneRules(p4info_helper, s2, 100, [{"egress_port": 252, "instance": 1}])
        writeCloneRules(p4info_helper, s3, 100, [{"egress_port": 252, "instance": 1}])
        
        print('\n Monitoring network congestion ...') 
        while True:
            sleep(1)
            print('.')
            fetch_responses(s1)
            fetch_responses(s2)
            fetch_responses(s3)
            

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/ecn.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/ecn.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)
    main(args.p4info, args.bmv2_json)
