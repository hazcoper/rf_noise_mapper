"""
This is a simple program that will be used to create a noise image of the surrounding area.
it will use and antena, a rotor and sdr to take the measurments

consists of two parts:
    generating the data
        recording iq, sending commands to the rotor
    generating the image
        using the recording, generate the image

things that I need to be able to do:
    1. interface with gqrx to control the recording
    2. interface with the rotor to control the direction
    3. process the data to generate the image
    
actually i cant start raw iq recording remotely, so i will just get the dfbs from from grqx and use that to generate the image
    l STRENGTH 
    
it will save all the aquired data to a json that can be later used to generate the desired images

"""

import time
import json
import datetime
import os

from gqrx_control import create_gqrx_socket, get_dfbs, close_gqrx_socket, get_radio_info
from rigctl_control import create_rigctl_socket, set_azimuth_elevation, close_rigctl_socket




def take_measurmnet(gqrx_socket, average_wait_time):
    """
    Takes a measurment of the signal strength and returns the average value
    """
    dfbs = 0
    for i in range(average_wait_time):
        dfbs += get_dfbs(gqrx_socket)
        time.sleep(1)
    return dfbs/average_wait_time



if __name__ == "__main__":
    
    # connect to gqrx and to rigtctl
    gqrx_port = 7356
    gqrx_host = "localhost"

    rigctl_port = 4533
    righost = "172.20.38.211"
        
    gqrx_socket = create_gqrx_socket(gqrx_host, gqrx_port)    
    rig_socket = create_rigctl_socket(righost, rigctl_port)
    
    # gather radio information
    radio_info_dict = get_radio_info(gqrx_socket)
    
    scan_azimuth_step = 5
    scan_elevation_step = 10
    
    start_azimuth = 10
    end_azimuth = 360
    
    start_elevation = 10
    end_elevation = 50
    
    average_wait_time = 3    # the time to wait to average the signal
    movement_wait_time = 10   # the time to wait for the rotor to move and stabilize
    
    # estimate the duration of the test
    azimuth_steps = (end_azimuth - start_azimuth) // scan_azimuth_step
    elevation_steps = (end_elevation - start_elevation) // scan_elevation_step
    
    total_steps = azimuth_steps * elevation_steps
    total_duration = total_steps * (average_wait_time + movement_wait_time)
    print(f"Total duration of the test: {total_duration} seconds")
    print(f"Total duration of the test: {total_duration/60} minutes")
    print(f"Total number of steps in the test: {total_steps}")
    
    result_list = []
    
    start_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # perform the test
    # start at the smallest azimuth and elevation
    # go from left to right to the azimuth
    # increase the elevation by one step
    # go from right to left in the azimuth
    elevation_counter = 0
    for elevation in range(start_elevation, end_elevation, scan_elevation_step):
        if elevation_counter % 2 == 0:
            for azimuth in range(start_azimuth, end_azimuth+scan_azimuth_step, scan_azimuth_step):
                print(f"Taking measurment at azimuth: {azimuth}, elevation: {elevation}")
                set_azimuth_elevation(rig_socket, azimuth, elevation)
                time.sleep(movement_wait_time)
                dfbs = take_measurmnet(gqrx_socket, average_wait_time)
                result_list.append((azimuth, elevation, dfbs))
        else:
            for azimuth in range(end_azimuth, start_azimuth-scan_azimuth_step, -scan_azimuth_step):
                print(f"Taking measurment at azimuth: {azimuth}, elevation: {elevation}")
                set_azimuth_elevation(rig_socket, azimuth, elevation)
                time.sleep(movement_wait_time)
                dfbs = take_measurmnet(gqrx_socket, average_wait_time)
                result_list.append((azimuth, elevation, dfbs))

        elevation_counter += 1
        print()
    
    end_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # close the connections
    close_gqrx_socket(gqrx_socket)
    close_rigctl_socket(rig_socket)
    
    # save data in json containing information about the test. add the time to the file name    
    result_dict = {
        "start_time": start_time_str,
        "end_time": end_time_str,
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
        "result_list": result_list
    }
    
    # add radio information to the result
    result_dict.update(radio_info_dict)
    
    # dump the result to a json file
    folder = "results"
    filename = os.path.join(f"{start_time_str}_{end_time_str}_{total_steps}.json")
    with open(filename, "w") as f:
        json.dump(result_dict, f)
    
    
    # generate a simple plot to show the data
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
    
