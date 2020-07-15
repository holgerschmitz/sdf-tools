#!/usr/bin/python2

import sdf
import numpy as np
from matplotlib import pyplot as plt
import argparse
import math

parser = argparse.ArgumentParser(
    description='''
Create a photon intensity spectrum from EPOCH particle data.
''',
    formatter_class=argparse.RawDescriptionHelpFormatter)

#parser.add_argument('-p', '--pos', help='detector position in mm', type=float, default=100)
#parser.add_argument('-x', '--x_res', help='histogram resolution in the x direction', type=int, default=200)
#parser.add_argument('-y', '--y_res', help='histogram resolution in the y direction', type=int, default=1500)

parser.add_argument('-e', '--energy_min', help='minimum energy in eV', type=float, default=100)
parser.add_argument('-E', '--energy_max', help='maximum energy in eV', type=float, default=1e6)
parser.add_argument('-r', '--resolution', help='resolution of the spectrum', type=int, default=100)
parser.add_argument('-p', '--photon', help='The name of the photon species', default='Photon')
parser.add_argument('file_name', help='The path to the SDF file')

args = parser.parse_args()

e_min = args.energy_min
e_max = args.energy_max
file_name = args.file_name
particle_name = args.photon
resolution = args.resolution

# load EPOCH data
data = sdf.read(file_name, dict=True)

log_e_min = math.log(e_min)
log_e_max = math.log(e_max)

buckets = np.linspace(log_e_min, log_e_max, resolution)
energy_axis = np.exp(buckets)

# for key in data.iteritems():
#   print(key)

# Photon data
energies = data['Particles/QED energy/'+particle_name].data/1.602e-19
weights = data['Particles/Weight/'+particle_name].data

num_particles = energies.shape[0];

# binned proton energy
plt.subplot(1,1,1);

hist = np.histogram(
    np.log(energies),
    bins = resolution,
    range = (log_e_min, log_e_max),
    weights = weights
    )

print(hist)
print(log_e_min)
print(log_e_max)

plt.plot(energy_axis, hist[0], 'k--', linewidth = 2);
axes = plt.gca()
axes.set_xscale('log');
axes.set_yscale('log');

plt.show()
