#!/usr/bin/env python3
"""
Simplified P4Runtime ACL Controller Runner

This script provides a simpler way to run the ACL controller with P4Runtime.
"""

import os
import sys
import subprocess
import time

def run_controller():
    """
    Run the P4Runtime ACL controller
    """
    print("Starting P4Runtime ACL Controller...")
    print("Make sure you have compiled the P4 program first with 'make build'")
    print("And started the mininet topology with 'make run' in another terminal")
    print()
    
    # Check if build files exist
    p4info_file = "./build/acl.p4.p4info.txt"
    bmv2_json_file = "./build/acl.json"
    
    if not os.path.exists(p4info_file):
        print(f"Error: {p4info_file} not found!")
        print("Please run 'make build' first to compile the P4 program.")
        return
        
    if not os.path.exists(bmv2_json_file):
        print(f"Error: {bmv2_json_file} not found!")
        print("Please run 'make build' first to compile the P4 program.")
        return
    
    print("Build files found. Starting controller...")
    
    try:
        # Run the controller
        subprocess.run([
            sys.executable, 
            "acl_controller.py",
            "--p4info", p4info_file,
            "--bmv2-json", bmv2_json_file
        ])
    except KeyboardInterrupt:
        print("\nController stopped by user.")
    except Exception as e:
        print(f"Error running controller: {e}")

if __name__ == "__main__":
    run_controller()