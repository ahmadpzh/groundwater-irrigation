"""This code solves 2D Unconfined problem using Implicit scheme

Important Note: The code employs Cell Vertex scheme"""

import numpy as np
import scipy
import matplotlib.pyplot as plt
import time
from functions import TDMAsolver
from scipy import linalg
import xlrd

t0 = time.time()

"Setting"
lx = 100
ly = 100
nx_max = 51
ny_max = 51
dx = lx / (nx_max - 1)
dy = ly / (ny_max - 1)

k = 0.001 / 60  # Saturated Hydraulic Conductivity
s_y = 0.002  # Specific Yield

"- - - - - - - - - - - - - - - - - - - - - - - - "
# # Dataset 1 --> only recharge (sensitive to recharge)
# k = 0.002 / 60
# s_y = 0.002

# Dataset 2 --> only recharge (insensitive to recharge)
k = 0.001/60    # Saturated Hydraulic Conductivity
s_y = 0.02

# # Dataset 3 --> Pumping
# k = 12/86400    # Mohamed and Rushton (2006)
# s_y = 0.033     # Mohamed and Rushton (2006)
"- - - - - - - - - - - - - - - - - - - - - - - - "
n_time = 0
nn = 0
n_save = 2

elapsed_time = 0
total_time = 86400.1
dt = 20

max_iter = 100
max_error = 0.0001
n_iter = np.arange(1, max_iter)

"Recharge & Pump + + + + + + + + + + + + + + + +"
R_data_workbook = xlrd.open_workbook('RData.xlsx')
R_data_sheet = R_data_workbook.sheet_by_index(0)
recharge = np.zeros([R_data_sheet.nrows - 2, 1])
m = 0
for i in range(2, R_data_sheet.nrows):
    recharge[m] = float(R_data_sheet.cell_value(i, 2))
    m += 1

pump = np.zeros([nx_max, ny_max])
# pump[40][25] = 1
P_data_workbook = xlrd.open_workbook('PData.xlsx')
P_data_sheet = P_data_workbook.sheet_by_index(0)
q_p1 = np.zeros([P_data_sheet.nrows - 2, 1])
m = 0
for i in range(2, P_data_sheet.nrows):
    q_p1[m] = float(P_data_sheet.cell_value(i, 2))
    m += 1

"Recharge & Pump - - - - - - - - - - - - - - - -"

"Mesh Generation"
x = np.zeros([nx_max, ny_max])
y = np.copy(x)
for i in range(1, nx_max):
    for j in range(ny_max):
        x[i][j] = x[i - 1][j] + dx

for j in range(1, ny_max):
    for i in range(nx_max):
        y[i][j] = y[i][j - 1] + dy

"Code Acceleration Part"
ATDMA = np.zeros([nx_max - 2, ny_max])
BTDMA = np.copy(ATDMA)
CTDMA = np.copy(ATDMA)
DTDMA = np.copy(ATDMA)

"Initial Condition"
h_n = np.reshape([float(10) for i in np.zeros(nx_max * ny_max)], [nx_max, ny_max])
h_n1 = np.copy(h_n)
h_n1_old = np.copy(h_n)

"Processing"
while elapsed_time < total_time:
    for n in n_iter:
        h_diff = 0

        # J-Sweep + + + + + + + + + + + + + + + +
        # for j in range(1, ny_max - 1):
            # West Boundary (Dirichlet)
        ATDMA[0] = 0
        BTDMA[0] = 1
        CTDMA[0] = 0
        DTDMA[0] = 12
            # i = 0
            # ATDMA[i] = 0
            # BTDMA[i] = 1
            # CTDMA[i] = 0
            # DTDMA[i] = 12

        """without loop"""
        hw = 0.5 * (h_n1[:-1][1:] + h_n1[1:][1:])
        he = 0.5 * (h_n1[1:][1:] + h_n1[:-1][1:])
        hs = 0.5 * (h_n1[1:][:-1] + h_n1[1:][1:])
        hn = 0.5 * (h_n1[1:][1:] + h_n1[1:][:-1])
            # for i in range(1, nx_max - 1):
            #     hw = 0.5 * (h_n1[i - 1][j] + h_n1[i][j])
            #     he = 0.5 * (h_n1[i + 1][j] + h_n1[i][j])
            #     hs = 0.5 * (h_n1[i][j - 1] + h_n1[i][j])
            #     hn = 0.5 * (h_n1[i][j + 1] + h_n1[i][j])
        ATDMA = -k * hw * dy / dx
        BTDMA = (s_y * dx * dy / dt) + (k * he * dy / dx) + (k * hw * dy / dx) + (k * hn * dx / dy) + \
                (k * hs * dx / dy)
        CTDMA = -k * he * dy / dx
        DTDMA = (s_y * dx * dy / dt) * h_n + (k * hs * dx / dy) * h_n1[:][:-1] + \
                (k * hn * dx / dy) * h_n1 +\
                recharge[int(np.floor(elapsed_time / 86400))] * dx * dy -\
                pump[:][:] * q_p1[int(np.floor(elapsed_time / 3600) + 1)]

            # ATDMA[i] = -k * hw * dy / dx
            # BTDMA[i] = (s_y * dx * dy / dt) + (k * he * dy / dx) + (k * hw * dy / dx) + (k * hn * dx / dy) + \
            #            (k * hs * dx / dy)
            # CTDMA[i] = -k * he * dy / dx
            # DTDMA[i] = (s_y * dx * dy / dt) * h_n[i][j] + (k * hs * dx / dy) * h_n1[i][j - 1] + \
            #            (k * hn * dx / dy) * h_n1[i][j + 1] +\
            #            recharge[int(np.floor(elapsed_time / 86400))] * dx * dy -\
            #            pump[i][j] * q_p1[int(np.floor(elapsed_time / 3600) + 1)]

            # East Boundary Condition
        ATDMA[-1] = 0
        BTDMA[-1] = 1
        CTDMA[-1] = 0
        DTDMA[-1] = 10
            # i = nx_max - 1
            # ATDMA[i] = 0
            # BTDMA[i] = 1
            # CTDMA[i] = 0
            # DTDMA[i] = 10
        z = TDMAsolver(ATDMA, BTDMA, CTDMA, DTDMA)
        h_n1 = z
            # for l in range(ny_max):
            #     h_n1[l][j] = z[l]
        # J-Sweep - - - - - - - - - - - - - - - -

        # I-Sweep + + + + + + + + + + + + + + + +
        for i in range(1, nx_max - 1):
            # # South Boundary (Dirichlet)
            # j = 0
            # ATDMA[j] = 0
            # BTDMA[j] = 1
            # CTDMA[j] = -1
            # DTDMA[j] = 10

            # South Boundary (no flow)
            j = 0
            ATDMA[j] = 0
            BTDMA[j] = 1
            CTDMA[j] = -1
            DTDMA[j] = 0

            for j in range(1, ny_max - 1):
                hw = 0.5 * (h_n1[i - 1][j] + h_n1[i][j])
                he = 0.5 * (h_n1[i + 1][j] + h_n1[i][j])
                hs = 0.5 * (h_n1[i][j - 1] + h_n1[i][j])
                hn = 0.5 * (h_n1[i][j + 1] + h_n1[i][j])

                ATDMA[j] = -k * hs * dx / dy
                BTDMA[j] = (s_y * dx * dy / dt) + (k * he * dy / dx) + (k * hw * dy / dx) + (k * hn * dx / dy) + \
                           (k * hs * dx / dy)
                CTDMA[j] = -k * hn * dx / dy
                DTDMA[j] = (s_y * dx * dy / dt) * h_n[i][j] + (k * hs * dx / dy) * h_n1[i][j - 1] + \
                           (k * hn * dx / dy) * h_n1[i][j + 1] + \
                           recharge[int(np.floor(elapsed_time / 86400))] * dx * dy - \
                           pump[i][j] * q_p1[int(np.floor(elapsed_time / 3600) + 1)]

            # # North Boundary(Dirichlet)
            # j = ny_max - 1
            # ATDMA[j] = 0
            # BTDMA[j] = 1
            # CTDMA[j] = 0
            # DTDMA[j] = 10

            # North Boundary (no-flow)
            j = ny_max - 1
            ATDMA[j] = -1
            BTDMA[j] = 1
            CTDMA[j] = 0
            DTDMA[j] = 0

            z = TDMAsolver(ATDMA, BTDMA, CTDMA, DTDMA)
            for l in range(nx_max):
                h_n1[i][l] = z[l]
        # I-Sweep - - - - - - - - - - - - - - - -

        for i in range(nx_max):
            for j in range(ny_max):
                h_diff = abs(h_n1_old[i][j] - h_n1[i][j]) + h_diff

        if h_diff < max_error:
            break

        h_n1_old = h_n1

    elapsed_time = elapsed_time + dt
    print('Elapsed Time =', (elapsed_time/86400), ', Iteration= ', n_iter[n])

    if elapsed_time + dt > total_time:
        dt = total_time - elapsed_time

    h_n = h_n1
    h_n1_old = h_n1

    # Graphic
    plt.contourf(x, y, h_n1)
    plt.axis('off')
    plt.grid()
    plt.colorbar().ax.set_ylabel('[m]')
    plt.pause(0.00000001)
    plt.show(block=False)
    plt.clf()

print('Elapsed Time= ', (elapsed_time/86400), ', Iteration= ', n_iter[n])

t1 = time.time()
print('time required: ', (t1 - t0) / 60)

"Post Processing"
plt.contourf(h_n1)
plt.axis('off')
plt.grid()
plt.colorbar().ax.set_ylabel('[m]')
plt.pause(0.0001)
plt.show(block=False)

print()
