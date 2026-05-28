import sys
import time
import logging
from sllurp.llrp import LLRPReaderConfig, LLRPReaderClient

# Mute sllurp internal debug logging to keep the output clean
logging.getLogger('sllurp').setLevel(logging.ERROR)

READER_IP = '169.254.104.152'
READER_PORT = 5084

# --- Race Timing Settings ---
RSSI_THRESHOLD = -55  
unique_runners = set()

def handle_tags(reader, tag_reports):
    global unique_runners
    for report in tag_reports:
        epc = report.get('EPC-96') or report.get('EPC')
        if not epc:
            continue

        # Fetch telemetry parameters
        rssi = report.get('PeakRSSI')
        antenna = report.get('AntennaID', 1)
        epc_str = epc.hex().upper() if isinstance(epc, bytes) else str(epc).upper()

        # RSSI Filtering logic
        if rssi is not None and rssi < RSSI_THRESHOLD:
            continue

        # Live timestamp generation
        timestamp = time.strftime('%H:%M:%S', time.localtime())
        ms = int((time.time() % 1) * 1000)
        real_time_str = f"{timestamp}.{ms:03d}"

        # Write directly to system standard output (unbuffered terminal print)
        sys.stdout.write(f"[{real_time_str}] TAG: {epc_str} | RSSI: {rssi} dBm | Ant: {antenna}\n")
        sys.stdout.flush()

        if epc_str not in unique_runners:
            unique_runners.add(epc_str)

def main():
    sys.stdout.write(f"Configuring sllurp connection params for R1000...\n")
    sys.stdout.flush()

    # Pass configuration elements inside a single dictionary object
    config_args = {
        'start_inventory': True,
        'reset_on_connect': True,
        
        # This tells the R1000 to push reports instantly on every single tag read
        'report_every_n_tags': 1,
        
        # Tell the reader to populate telemetry data packets
        'tag_content_selector': {
            'EnableAntennaID': True,
            'EnablePeakRSSI': True,
            'EnableFirstSeenTimestamp': False,
            'EnableLastSeenTimestamp': False,
            'EnableTagSeenCount': False
        }
    }
    
    config = LLRPReaderConfig(config_args)
    reader = LLRPReaderClient(READER_IP, READER_PORT, config)
    reader.add_tag_report_callback(handle_tags)

    sys.stdout.write(f"Connecting to reader... Filter: >= {RSSI_THRESHOLD} dBm\n")
    sys.stdout.flush()
    
    reader.connect()

    sys.stdout.write("Live pipeline active. Wave tags across antenna now...\n")
    sys.stdout.flush()
    
    try:
        # Hand processing loop cleanly over to the sllurp worker thread
        reader.join(None)
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("\nDisconnecting reader session...\n")
        sys.stdout.flush()
    finally:
        reader.disconnect()
        
        # Display aggregated race counts on exit
        sys.stdout.write("\n" + "="*45 + "\n")
        sys.stdout.write(f"SESSION ENDED. Total Unique Tags Logged: {len(unique_runners)}\n")
        sys.stdout.write("="*45 + "\n")
        sys.stdout.flush()

if __name__ == '__main__':
    main()
