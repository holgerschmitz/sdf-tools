import sdf
import numpy as np
from matplotlib import pyplot as plt
import argparse

parser = argparse.ArgumentParser(
    description='''
Create a synthetic radiograph from EPOCH particle dataself.

Histograms are generated by projecting the particles of a given species onto a
detector plane. On the detector plane, a histogram of the particles weighted by
the particle weights is used to create the synthetic radiograph. The particles
are assumed to propagate in the z-direction.

Multiple plots are generated (from left to right):
* a 2d histogram of particles at the location of the simulation (z=0) in the x-y
  plane.
* a side-on radiograph generated by a sequence of 1d histograms in the
  y-direction. The histograms are calculated at equally spaced locations between
  z=0 and z=<detector_position>.
  The number of slices is determined by <detector_res>.
3. a 2d histogram of particles at the detector plane (z=<detector_position>) in
   the x-y plane.
4. a 1d histogram of particles at the detector plane (z=<detector_position>) in
   the y direction, integrated over x.''',
    formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('-p', '--pos', help='detector position in mm', type=float, default=100)
parser.add_argument('-x', '--x_res', help='histogram resolution in the x direction', type=int, default=200)
parser.add_argument('-y', '--y_res', help='histogram resolution in the y direction', type=int, default=1500)
parser.add_argument('-d', '--detector_res', help='resolution of the side-on sweep', type=int, default=1000)

parser.add_argument('particle_name')
parser.add_argument('file_name')

args = parser.parse_args()

file_name = args.file_name
particle_name = args.particle_name

nx_hist_res = args.x_res
ny_hist_res = args.y_res
detector_res = args.detector_res

detector_position = 1e-3 * args.pos


# load EPOCH data
data = sdf.read(file_name, dict=True)

# simulation grid axes
x_grid = data['Grid/Grid'].data[0]
y_grid = data['Grid/Grid'].data[1]
dx = x_grid[1] - x_grid[0]
dy = y_grid[1] - y_grid[0]

# momenta of all particles
p_x = data['Particles/Px/'+particle_name].data
p_y = data['Particles/Py/'+particle_name].data
p_z = data['Particles/Pz/'+particle_name].data

# positions of all particles
x_pos = data['Grid/Particles/'+particle_name].data[0]
y_pos = data['Grid/Particles/'+particle_name].data[1]

# particle weights
weights = data['Particles/Weight/'+particle_name].data

num_particles = p_x.shape[0];

def project(distance):
    proj_pos = np.empty([2, num_particles])
    for i in range(num_particles):
        proj_pos[0, i] = x_pos[i] + distance * p_x[i] / p_z[i]
        proj_pos[1, i] = y_pos[i] + distance * p_y[i] / p_z[i]
    return proj_pos

# size of the simulation box
box_x_min = x_grid[0];
box_x_max = x_grid[-1];
box_y_min = y_grid[0];
box_y_max = y_grid[-1];
box_points_x = [box_x_min, box_x_max, box_x_max, box_x_min, box_x_min]
box_points_y = [box_y_min, box_y_min, box_y_max, box_y_max, box_y_min]

# size of the plot in the x-direction
x_pad = 0.1*(box_x_max - box_x_min)
y_pad = 0.1*(box_y_max - box_y_min)

# find the min and max y-coordinate at the target location
projected_zero = project(0)
x_lo_zero = min(projected_zero[0].min(), box_x_min)
x_hi_zero = max(projected_zero[0].max(), box_x_max)
y_lo_zero = min(projected_zero[1].min(), box_y_min)
y_hi_zero = max(projected_zero[1].max(), box_y_max)

# find the min and max y-coordinate at the detector location
projected_detector = project(detector_position)
x_lo_detector = min(projected_detector[0].min(), box_x_min)
x_hi_detector = max(projected_detector[0].max(), box_x_max)
y_lo_detector = min(projected_detector[1].min(), box_y_min)
y_hi_detector = max(projected_detector[1].max(), box_y_max)

# overall min and max y-coordinate
x_lo = min(x_lo_zero, x_lo_detector) - x_pad
x_hi = max(x_hi_zero, x_hi_detector) + x_pad
y_lo = min(y_lo_zero, y_lo_detector) - y_pad
y_hi = max(y_hi_zero, y_hi_detector) + y_pad

x_bins = np.linspace(x_lo, x_hi, nx_hist_res)
y_bins = np.linspace(y_lo, y_hi, ny_hist_res)

# binned proton density at rear of target (0 mm)
plt.subplot(1,6,1);

hist = plt.hist2d(
    x = projected_zero[0],
    y = projected_zero[1],
    bins = [nx_hist_res, ny_hist_res],
    range = [[x_lo, x_hi], [y_lo, y_hi]],
    weights = weights)
plt.plot(box_points_x, box_points_y, 'k--', linewidth = 2);
plt.colorbar()

# binned proton density on detector (X mm)
plt.subplot(1,6,5);

hist = plt.hist2d(
    x = projected_detector[0],
    y = projected_detector[1],
    bins = [nx_hist_res, ny_hist_res],
    range = [[x_lo, x_hi], [y_lo, y_hi]],
    weights = weights)
plt.plot(box_points_x, box_points_y, 'k--', linewidth = 2);
plt.colorbar()
axes = plt.gca()
axes.set_ylim([y_lo, y_hi])
axes.set_yticklabels([])

# side-on particle tracking
plt.subplot2grid((1, 6), (0, 1), colspan=3)

tracking_positions, tracking_step = np.linspace(0, detector_position, detector_res+1, retstep=True)
tracking_positions = tracking_positions[0:-1] + 0.5*tracking_step
hist_bins_y, hist_step_y = np.linspace(y_lo, y_hi, ny_hist_res+1, retstep=True)
hist_bins_y = hist_bins_y[0:-1] + 0.5*hist_step_y

side_on = np.zeros([detector_res, ny_hist_res])

print('creating side-on image')

for i in range(detector_res):
    print('   tracking '+str(tracking_positions[i]))
    projected = project(tracking_positions[i]);
    hist = np.histogram(
        a = projected[1],
        bins = ny_hist_res,
        range = [y_lo, y_hi],
        weights = weights)
    side_on[i] = hist[0]

X, Y = np.meshgrid(tracking_positions, hist_bins_y)

plt.hist2d(
    x = X.flatten(),
    y = Y.flatten(),
    bins = [detector_res, ny_hist_res],
    range = [[0, detector_position], [y_lo, y_hi]],
    weights = side_on.transpose().flatten())
plt.colorbar()
axes = plt.gca()
axes.set_ylim([y_lo, y_hi])
axes.set_yticklabels([])

# vertical lineout (integrated in transverse x-dir) in detector plane
plt.subplot(1,6,6);

projected = project(detector_position);
hist = np.histogram(
    a = projected[1],
    bins = ny_hist_res,
    range = [y_lo, y_hi],
    weights = weights)

plt.plot(hist[0], hist_bins_y)
axes = plt.gca()
axes.set_ylim([y_lo, y_hi])
axes.set_yticklabels([])

plt.show()