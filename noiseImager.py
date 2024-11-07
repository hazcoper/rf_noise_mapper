import time
import json
import datetime
import os
import signal
import sys
from gqrx_control import create_gqrx_socket, get_dfbs, close_gqrx_socket, get_radio_info
from rotctl_control import create_rotctl_socket, set_azimuth_elevation, close_rotctl_socket


# Helper function to dump data to JSON
def dump_json(result_dict, result_list, incomplete=False):
    print("Sabing json data...")
    end_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_dict["end_time"] = end_time_str
    result_dict["results"] = result_list

    folder = "results"
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    name = f"{start_time_str}_{end_time_str}_{total_steps}"
    if incomplete:
        name += "_incomplete"
    
    filename = f"{folder}/{name}.json"

    with open(filename, "w") as f:
        json.dump(result_dict, f)


# Measurement function
def take_measurement(gqrx_socket, average_wait_time):
    dfbs = 0
    for i in range(average_wait_time):
        dfbs += get_dfbs(gqrx_socket)
        time.sleep(1)
    return dfbs / average_wait_time


# Signal handler to handle interruption and ensure data is saved
def handle_exit(signum, frame):
    print("\nProgram interrupted. Saving data...")
    dump_json(result_dict, result_list, incomplete=True)
    close_gqrx_socket(gqrx_socket)
    close_rotctl_socket(rig_socket)
    sys.exit(0)


# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, handle_exit)

if __name__ == "__main__":
    result_dict = {}
    
    # Set up connection details
    gqrx_port = 7356
    gqrx_host = "localhost"
    rotctl_port = 4533
    righost = "172.20.38.211"
    
    # Connect to gqrx and rotctl
    gqrx_socket = create_gqrx_socket(gqrx_host, gqrx_port)
    rig_socket = create_rotctl_socket(righost, rotctl_port)
    
    # Gather radio information
    radio_info_dict = get_radio_info(gqrx_socket)
    
    # Define scan parameters
    scan_azimuth_step = 5
    scan_elevation_step = 10
    start_azimuth = 10
    end_azimuth = 360
    start_elevation = 10
    end_elevation = 50
    average_wait_time = 3    # Time to average the signal
    movement_wait_time = 10  # Wait time for rotor stabilization
    
    # Estimate duration
    azimuth_steps = (end_azimuth - start_azimuth) // scan_azimuth_step
    elevation_steps = (end_elevation - start_elevation) // scan_elevation_step
    total_steps = azimuth_steps * elevation_steps
    total_duration = total_steps * (average_wait_time + movement_wait_time)
    print(f"Total duration of the test: {total_duration} seconds ({total_duration / 60} minutes)")
    print(f"Total number of steps in the test: {total_steps}")
    
    # Set start time for file naming
    start_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    result_dict = {
        "start_time": start_time_str,
        "total_steps": total_steps,
        "total_duration": total_duration,
        "scan_azimuth_step": scan_azimuth_step,
        "scan_elevation_step": scan_elevation_step,
        "start_azimuth": start_azimuth,
        "end_azimuth": end_azimuth,
        "start_elevation": start_elevation,
        "end_elevation": end_elevation,
        "average_wait_time": average_wait_time,
        "movement_wait_time": movement_wait_time,
    }
    
    # Add radio information to result
    result_dict.update(radio_info_dict)
    result_list = []
    
    # Begin test
    elevation_counter = 0
    for elevation in range(start_elevation, end_elevation, scan_elevation_step):
        if elevation_counter % 2 == 0:
            # Left to right azimuth scan
            for azimuth in range(start_azimuth, end_azimuth + scan_azimuth_step, scan_azimuth_step):
                print(f"Taking measurement at azimuth: {azimuth}, elevation: {elevation}")
                set_azimuth_elevation(rig_socket, azimuth, elevation)
                time.sleep(movement_wait_time)
                dfbs = take_measurement(gqrx_socket, average_wait_time)
                result_list.append((azimuth, elevation, dfbs))
        else:
            # Right to left azimuth scan
            for azimuth in range(end_azimuth, start_azimuth - scan_azimuth_step, -scan_azimuth_step):
                print(f"Taking measurement at azimuth: {azimuth}, elevation: {elevation}")
                set_azimuth_elevation(rig_socket, azimuth, elevation)
                time.sleep(movement_wait_time)
                dfbs = take_measurement(gqrx_socket, average_wait_time)
                result_list.append((azimuth, elevation, dfbs))

        elevation_counter += 1
        print()
    
    # Ensure data is dumped and connections are closed
    dump_json(result_dict, result_list)
    close_gqrx_socket(gqrx_socket)
    close_rotctl_socket(rig_socket)
    print("Data saved and connections closed.")
    
    # Generate plot
    import matplotlib.pyplot as plt
    import numpy as np
    
    azimuths = np.array([result[0] for result in result_list])
    elevations = np.array([result[1] for result in result_list])
    dfbs = np.array([result[2] for result in result_list])
    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(azimuths, elevations, dfbs)
    ax.set_xlabel('Azimuth')
    ax.set_ylabel('Elevation')
    ax.set_zlabel('dfbs')
    plt.show()
