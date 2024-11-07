import socket

def create_rigctl_socket(host='127.0.0.1', port=4533):
    """ Connects to rigctld for rotator control using TCP socket. """
    try:
        # Create a socket connection
        rig_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rig_socket.connect((host, port))
        print("Connected to rigctld.")
        return rig_socket
    except socket.error as e:
        print(f"Connection error: {e}")
        return None
    
def close_rigctl_socket(rig_socket):
    """ Closes the socket connection to rigctld. """
    try:
        rig_socket.close()
        print("Closed connection to rigctld.")
    except socket.error as e:
        print(f"Error closing connection: {e}")

def set_azimuth_elevation(rig_socket, azimuth, elevation):
    """ Sends a command to set azimuth angle. """
    try:
        # Format the command for setting azimuth angle (use P command for rotctld)
        command = f"P {azimuth} {elevation}\n"
        rig_socket.sendall(command.encode())
        print(f"  Set azimuth to {azimuth} degrees.")
    except socket.error as e:
        print(f"  Error sending azimuth command: {e}")


def main():
    # Connect to the rigctld rotator control server
    host = "172.20.38.211"
    host = "localhost"
    port = 4534
    rig_socket = create_rigctl_socket(host, port)

    if rig_socket:
        # Set desired azimuth and elevation
        azimuth_angle = 180  # Example azimuth in degrees
        elevation_angle = 45  # Example elevation in degrees

        # Send the command to set the azimuth and elevation
        set_azimuth_elevation(rig_socket, azimuth_angle, elevation_angle)

        # Close the socket
        rig_socket.close()
        print("Disconnected from rigctld.")

if __name__ == "__main__":
    main()
