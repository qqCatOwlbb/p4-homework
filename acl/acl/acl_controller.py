#!/usr/bin/env python3
"""
P4Runtime ACL Controller

This script demonstrates how to use P4Runtime to dynamically install
ACL rules instead of using static JSON configuration files.
"""

import argparse
import os
import sys
from time import sleep
import grpc

# Import P4Runtime utils
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))
import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections


def writeACLRules(p4info_helper, sw):
    """
    Install ACL rules using P4Runtime
    """
    print("Installing ACL rules...")
    
    # Rule 1: Drop UDP packets with destination port 80
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.acl",
        match_fields={
            "hdr.udp.dstPort": (80, 0xFFFF)      # Match UDP port 80 exactly
        },
        action_name="MyIngress.drop",
        priority=1
    )
    sw.WriteTableEntry(table_entry)
    print("Installed rule: Drop UDP packets with destination port 80")
    
    # Rule 2: Drop all packets to IP address 10.0.1.4
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.acl",
        match_fields={
            "hdr.ipv4.dstAddr": ("10.0.1.4", 0xFFFFFFFF),  # Match IP 10.0.1.4 exactly
        },
        action_name="MyIngress.drop",
        priority=1
    )
    sw.WriteTableEntry(table_entry)
    print("Installed rule: Drop all packets to IP address 10.0.1.4")


def writeIPv4ForwardingRules(p4info_helper, sw):
    """
    Install IPv4 forwarding rules using P4Runtime
    """
    print("Installing IPv4 forwarding rules...")
    
    # Forwarding rules for each host
    hosts = [
        ("10.0.1.1", "00:00:00:00:01:01", 1),
        ("10.0.1.2", "00:00:00:00:01:02", 2),
        ("10.0.1.3", "00:00:00:00:01:03", 3),
        ("10.0.1.4", "00:00:00:00:01:04", 4)
    ]
    
    for ip, mac, port in hosts:
        table_entry = p4info_helper.buildTableEntry(
            table_name="MyIngress.ipv4_lpm",
            match_fields={
                "hdr.ipv4.dstAddr": (ip, 32)
            },
            action_name="MyIngress.ipv4_forward",
            action_params={
                "dstAddr": mac,
                "port": port
            }
        )
        sw.WriteTableEntry(table_entry)
        print(f"Installed forwarding rule: {ip} -> {mac} port {port}")


def printCounter(p4info_helper, sw, counter_name, index):
    """
    Read and print counter values
    """
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print(f"{counter_name}[{index}] = {counter.data.packet_count} packets, {counter.data.byte_count} bytes")


def printTableEntries(p4info_helper, sw):
    """
    Print all table entries
    """
    print("\n----- Reading tables rules for s1 -----")
    for response in sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            table_name = p4info_helper.get_tables_name(entry.table_id)
            print(f"Table: {table_name}")
            for m in entry.match:
                print(f"  Match: {p4info_helper.get_match_field_name(table_name, m.field_id)} = {p4info_helper.get_match_field_value(m)}")
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print(f"  Action: {action_name}")
            for p in action.params:
                print(f"    Param: {p4info_helper.get_action_param_name(action_name, p.param_id)} = {p.value}")
            print(f"  Priority: {entry.priority}")
            print()


def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create a switch connection object for s1
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
        )
        
        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        s1.MasterArbitrationUpdate()

        # Install the P4 program on the switch
        s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s1")

        # Write IPv4 forwarding rules
        writeIPv4ForwardingRules(p4info_helper, s1)

        # Write ACL rules
        writeACLRules(p4info_helper, s1)

        # Print the tunnel counters every 2 seconds
        while True:
            sleep(2)
            print("\n----- Reading table entries -----")
            printTableEntries(p4info_helper, s1)

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime ACL Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/acl.p4.p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/acl.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print(f"\np4info file not found: {args.p4info}")
        print("Have you run 'make build'?")
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print(f"\nBMv2 JSON file not found: {args.bmv2_json}")
        print("Have you run 'make build'?")
        parser.exit(1)

    main(args.p4info, args.bmv2_json)