import socket
import time

def create_gqrx_socket(gqrx_host, gqrx_port):
    """
    Creates a socket object that connects to the gqrx server
    """
    try:
        grqx_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        grqx_socket.connect((gqrx_host, gqrx_port))
        return grqx_socket
    except Exception as E:
        print("Error creating gqrx socket: ", E)
        return None
    
def close_gqrx_socket(grqx_socket):
    """
    Closes the socket object
    """
    try:
        grqx_socket.close()
    except Exception as E:
        print("Error closing gqrx socket: ", E)

def get_dfbs(grqx_socket):
    """
    Receives a socket object. send the message to that socket object and returns the dbfs value in float
    """
    
    try:
        grqx_socket.send("l STRENGTH\n".encode())
        data = grqx_socket.recv(1024)
        print("  Measure: ", data.decode())
        return float(data.decode())
    except Exception as E:
        print("  Error getting dbfs: ", E)
        return None
    
def get_frequency(grqx_socket):
    """
    Receives a socket object. send the message to that socket object and returns the frequency value in float
    """
    
    try:
        grqx_socket.send("f\n".encode())
        data = grqx_socket.recv(1024)
        print("  Frequency: ", data.decode())
        return float(data.decode())
    except Exception as E:
        print("  Error getting frequency: ", E)
        return None

def get_demodulator_mode(grqx_socket):
    """
    Receives a socket object. send the message to that socket object and returns the demodulator mode
    """
    
    try:
        grqx_socket.send("m\n".encode())
        data = grqx_socket.recv(1024)
        print("  Demodulator Mode: ", data.decode())
        return data.decode()
    except Exception as E:
        print("  Error getting demodulator mode: ", E)
        return None
    
def get_squelch_threshold(grqx_socket):
    """
    Receives a socket object. send the message to that socket object and returns the squelch threshold
    """
    try:
        grqx_socket.send("l SQL\n".encode())
        data = grqx_socket.recv(1024)
        print("  Squelch Threshold: ", data.decode())
        return float(data.decode())
    except Exception as E:
        print("  Error getting squelch threshold: ", E)
        return None
    
def get_gain(grqx_socket):
    """
    Receives a socket object. send the message to that socket object and returns the gain name
    """
    try:
        grqx_socket.send("l PGA_GAIN GAIN\n".encode())
        data = grqx_socket.recv(1024)
        print("  Gain Name: ", data.decode())
        return data.decode()
    except Exception as E:
        print("  Error getting gain name: ", E)
        return None
    
    
def get_radio_info(grqx_socket):
    """
    Receives a socket object representing a connection to gqrx
    it will query all the available data from gqrx and return it as a dictionary
    """
    
    # get a list of all the funcitons in this module
    functions = [f for f in globals() if callable(globals()[f]) and f.startswith("get_") and f != "get_radio_info"]

    
    try:
        response_dict = {}
        for f in functions:
            print(f"Getting {f}")
            response_dict[f] = globals()[f](grqx_socket)
        return response_dict
    except Exception as E:
        print("  Error getting radio info: ", E)
        return None
    
    
if __name__ == "__main__":
    
    # create connection 
    gqrx_socket = create_gqrx_socket("localhost", 7356)
    
    print(get_radio_info(gqrx_socket))