import numpy as np
import matplotlib
from scipy.interpolate import griddata
import json
import os


matplotlib.use('TkAgg')

import matplotlib.pyplot as plt


def load_data(file_name="results/data.txt"):
    """
    Load data from file and return it as a list of tuples in the format (azimuth, elevation, dbfs).
    this is a legacy method
    """
    with open(file_name, "r") as f:
        data = f.readlines()
    
    data = [tuple(map(float, line.strip().split(", "))) for line in data]
    return data

def load_json_data(filename="results/data.json"):
    """
    Load data from a JSON file and return it as a dictionary.
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data



def plot_noise_data(data, plot_type='polar'):
    """
    Plots noise data from a ground station as either a 2D polar heatmap or a 3D scatter plot.
    
    Parameters:
    - data: list of tuples (azimuth, elevation, noise)
    - plot_type: 'polar' for 2D polar heatmap, '3d' for 3D scatter plot
    
    Returns:
    - A matplotlib plot of the noise data.
    """
    # Convert data to numpy array for easier manipulation
    data = np.array(data)
    azimuth = data[:, 0]
    elevation = data[:, 1]
    noise = data[:, 2]
    
    if plot_type == '2d':
        # Define azimuth and elevation ranges
        
        x_labels = list(range(10, 360, 5))   # Azimuth range (10° to 355° in 5° increments)
        y_labels = list(range(10, 40, 10))   # Elevation range (10° to 30° in 10° increments)
        
        # Create an empty array for the image
        image_array = np.zeros((len(y_labels), len(x_labels)))

        # Populate the array with noise data based on azimuth and elevation indices
        for azimuth, elevation, noise in data:
            try:
                # Find the closest index in x_labels and y_labels
                x_pixel = x_labels.index(min(x_labels, key=lambda x: abs(x - azimuth)))
                y_pixel = y_labels.index(min(y_labels, key=lambda y: abs(y - elevation)))
                
                # Update the noise value at the calculated pixel
                image_array[y_pixel, x_pixel] = noise
            except ValueError:
                # If azimuth or elevation is out of range, skip this data point
                continue

        # Plot the heatmap
        fig, ax = plt.subplots(figsize=(8, 6))
        plt.subplots_adjust(left=0.05, right=0.99)  # Adjust as needed
        # plt.tight_layout()
        im = ax.imshow(image_array, aspect='auto', origin='lower', cmap='viridis')

        # Set tick labels
        ax.set_xticks(np.arange(len(x_labels)))
        ax.set_yticks(np.arange(len(y_labels)))
        
        ax.set_xticklabels(x_labels)
        ax.set_yticklabels(y_labels)
        ax.margins(x=0, y=0) 
        
        # Add labels and colorbar
        ax.set_xlabel("Azimuth (°)")
        ax.set_ylabel("Elevation (°)")
        ax.set_title("Antenna Noise Level (2D Heatmap)")
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Noise Level (dBfs)", rotation=-90, va="bottom")
        
        # change the window size
        fig.set_size_inches(30, 5)
            
            
    if plot_type == '2d-interp':
        # Create a grid for azimuth and elevation
        grid_azimuth, grid_elevation = np.meshgrid(
            np.linspace(azimuth.min(), azimuth.max(), 100),
            np.linspace(elevation.min(), elevation.max(), 100)
        )
        
        # Interpolate noise data to fill the grid
        grid_noise = griddata((azimuth, elevation), noise, (grid_azimuth, grid_elevation), method='cubic')
        
        # Create the heatmap plot
        plt.figure(figsize=(10, 8))
        plt.contourf(grid_azimuth, grid_elevation, grid_noise, 100, cmap='viridis')
        plt.colorbar(label="Noise Level (dB)")
        plt.xlabel("Azimuth (°)")
        plt.ylabel("Elevation (°)")
        plt.title("Antenna Noise Level (interpolated) (2D Heatmap)")
    
    if plot_type == 'polar':
        # Convert azimuth to radians and elevation to radial distance
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(90 - elevation)  # Inverted for polar radius

        # Create polar scatter plot
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
        sc = ax.scatter(azimuth_rad, elevation_rad, c=noise, cmap='viridis', s=20)

        # Add a color bar
        cbar = plt.colorbar(sc, ax=ax, label="Noise Level (dBfs)")
        ax.set_theta_zero_location("N")  # Set North on top
        ax.set_theta_direction(-1)  # Azimuth goes clockwise
        ax.set_yticklabels([])  # Optional: remove radial labels for a cleaner look
        plt.title("Antenna Noise Level (Polar Plot)")
        
    if plot_type == 'polar-interp':
        # Convert azimuth to radians and elevation to radial distance (inverted for polar plot)
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(90 - elevation)
        
        # Create a grid for azimuth and elevation in polar coordinates
        grid_azimuth, grid_elevation = np.meshgrid(
            np.linspace(0, 2 * np.pi, 100),  # Full 360-degree azimuth
            np.linspace(elevation_rad.min(), elevation_rad.max(), 100)
        )
        
        # Interpolate noise data onto the polar grid
        grid_noise = griddata((azimuth_rad, elevation_rad), noise, (grid_azimuth, grid_elevation), method='cubic')

        # Create polar plot
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
        # Fill the plot area with interpolated noise levels
        c = ax.contourf(grid_azimuth, grid_elevation, grid_noise, 100, cmap='viridis')
        
        # Add a color bar
        cbar = plt.colorbar(c, ax=ax, pad=0.1, label="Noise Level (dBfs)")
        ax.set_theta_zero_location("N")  # North at the top
        ax.set_theta_direction(-1)       # Clockwise azimuth
        plt.title("Antenna Noise Level (interpolated) (Polar Plot)")
        
        
    # Save the plot as an image
    # start time in file name   
    start_time = metadata["start_time"]
    plt.savefig(f"results/{start_time}_{plot_type}.png")


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot noise data from a file.")
    parser.add_argument('--file', type=str, default="results/data.txt", help="Path to the data file.")
    args = parser.parse_args()

    # Load data from the specified file
    if args.file.endswith('.json'):
        metadata = load_json_data(args.file)
    else:
        # find the latest json file
        files = os.listdir("results")
        files = [file for file in files if file.endswith(".json")]
        files.sort()
        metadata = load_json_data(f"results/{files[-1]}")
        
        
    # lets conver the data to be able to use with the plot_noise_data function
    data = metadata["result_list"]
       
    plot_noise_data(metadata, data, "2d")
    plot_noise_data(metadata, data, "polar")
    plot_noise_data(metadata, data, "2d-interp")
    plot_noise_data(metadata, data, "polar-interp")
    
    