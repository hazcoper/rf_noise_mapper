import numpy as np
import matplotlib
from scipy.interpolate import griddata
import json
import os
import argparse

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt


def load_data(file_name="results/data.txt"):
    """
    Load data from file and return it as a list of tuples in the format (azimuth, elevation, dbfs).
    This is a legacy method.
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


def get_global_color_scale(data_list):
    """
    Get the global minimum and maximum values of noise across all datasets for a fixed color scale.
    """
    all_noise_values = []
    for data in data_list:
        all_noise_values.extend([d[2] for d in data])  # Assuming the third element is 'noise' (dbfs)
    
    return min(all_noise_values), max(all_noise_values)


def plot_noise_data(metadata, data, plot_type='polar', vmin=None, vmax=None):
    """
    Plots noise data from a ground station as either a 2D polar heatmap or a 3D scatter plot.
    
    Parameters:
    - data: list of tuples (azimuth, elevation, noise)
    - plot_type: 'polar' for polar heatmap, '2d' for 2D heatmap, '3d' for 3D scatter plot
    - vmin, vmax: Fixed color scale limits
    
    Returns:
    - A matplotlib plot of the noise data.
    """
    # Convert data to numpy array for easier manipulation
    data = np.array(data)
    azimuth = data[:, 0]
    elevation = data[:, 1]
    noise = data[:, 2]
    
    # If no global vmin/vmax is provided, use the range from the data
    if vmin is None or vmax is None:
        vmin = noise.min()
        vmax = noise.max()

    if plot_type == '2d':
        # x_labels = list(range(10, 360, 5))   # Azimuth range (10° to 355° in 5° increments)
        # y_labels = list(range(10, 40, 10))   # Elevation range (10° to 30° in 10° increments)
        
        x_labels = list(range(metadata["start_azimuth"], metadata["end_azimuth"] + metadata["scan_azimuth_step"], metadata["scan_azimuth_step"]))
        y_labels = list(range(metadata["start_elevation"], metadata["end_elevation"], metadata["scan_elevation_step"]))
        
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
                continue

        # Plot the heatmap
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(image_array, aspect='auto', origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)

        ax.set_xticks(np.arange(len(x_labels)))
        ax.set_yticks(np.arange(len(y_labels)))
        
        ax.set_xticklabels(x_labels)
        ax.set_yticklabels(y_labels)
        ax.margins(x=0, y=0) 
        
        ax.set_xlabel("Azimuth (°)")
        ax.set_ylabel("Elevation (°)")
        ax.set_title(f"Antenna Noise Level (2D Heatmap) {metadata['start_time']}")
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Noise Level (dBfs)", rotation=-90, va="bottom")
        
        fig.set_size_inches(30, 5)

    elif plot_type == '2d-interp':
        # Create a grid for azimuth and elevation
        grid_azimuth, grid_elevation = np.meshgrid(
            np.linspace(azimuth.min(), azimuth.max(), 100),
            np.linspace(elevation.min(), elevation.max(), 100)
        )
        
        # Interpolate noise data to fill the grid
        grid_noise = griddata((azimuth, elevation), noise, (grid_azimuth, grid_elevation), method='cubic')
        
        plt.figure(figsize=(10, 8))
        plt.contourf(grid_azimuth, grid_elevation, grid_noise, 100, cmap='viridis', vmin=vmin, vmax=vmax)
        plt.colorbar(label="Noise Level (dB)")
        plt.xlabel("Azimuth (°)")
        plt.ylabel("Elevation (°)")
        plt.title(f"Antenna Noise Level (interpolated) (2D Heatmap) {metadata['start_time']}")

    elif plot_type == 'polar':
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(90 - elevation)  # Inverted for polar radius

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
        sc = ax.scatter(azimuth_rad, elevation_rad, c=noise, cmap='viridis', s=20, vmin=vmin, vmax=vmax)

        cbar = plt.colorbar(sc, ax=ax, label="Noise Level (dBfs)")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_yticklabels([])
        plt.title(f"Antenna Noise Level (Polar Plot) {metadata['start_time']}")
        
    elif plot_type == 'polar-interp':
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(90 - elevation)
        
        grid_azimuth, grid_elevation = np.meshgrid(
            np.linspace(0, 2 * np.pi, 100),
            np.linspace(elevation_rad.min(), elevation_rad.max(), 100)
        )
        
        grid_noise = griddata((azimuth_rad, elevation_rad), noise, (grid_azimuth, grid_elevation), method='cubic')

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
        c = ax.contourf(grid_azimuth, grid_elevation, grid_noise, 100, cmap='viridis', vmin=vmin, vmax=vmax)
        
        cbar = plt.colorbar(c, ax=ax, pad=0.1, label="Noise Level (dBfs)")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        plt.title(f"Antenna Noise Level (interpolated) (Polar Plot) {metadata['start_time']}")
        
        
    # Save the plot as an image with high resolution
    start_time = metadata["start_time"]
    plt.savefig(f"results/{start_time}_{plot_type}.png", dpi=300)


def main():


    parser = argparse.ArgumentParser(description="Plot noise data from a file.")
    parser.add_argument('--file', type=str, default="results/data.txt", help="Path to the data file.")
    args = parser.parse_args()

    # Load data from the specified file
    if args.file.endswith('.json'):
        print("Loading file: ", args.file)
        metadata = load_json_data(args.file)
    else:
        # find the latest json file
        files = os.listdir("results")
        files = [file for file in files if file.endswith(".json")]
        files.sort()
        print("Loading latest file: ", files[-1])
        metadata = load_json_data(f"results/{files[-1]}")
        

    vmin = -90
    vmax = -65
    
    data = metadata["result_list"]


    plot_noise_data(metadata, data, "2d", vmin, vmax)
    plot_noise_data(metadata, data, "polar", vmin, vmax)
    plot_noise_data(metadata, data, "2d-interp", vmin, vmax)
    plot_noise_data(metadata, data, "polar-interp", vmin, vmax)


if __name__ == "__main__":
    main()
