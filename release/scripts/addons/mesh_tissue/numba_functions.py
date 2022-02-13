# SPDX-License-Identifier: GPL-2.0-or-later

import numpy as np
try:
    from numba import jit

    @jit
    def numba_reaction_diffusion(n_verts, n_edges, edge_verts, a, b, diff_a, diff_b, f, k, dt, time_steps):
        arr = np.arange(n_edges)*2
        id0 = edge_verts[arr]     # first vertex indices for each edge
        id1 = edge_verts[arr+1]   # second vertex indices for each edge
        for i in range(time_steps):
            lap_a = np.zeros(n_verts)
            lap_b = np.zeros(n_verts)
            lap_a0 =  a[id1] -  a[id0]   # laplacian increment for first vertex of each edge
            lap_b0 =  b[id1] -  b[id0]   # laplacian increment for first vertex of each edge

            for i, j, la0, lb0 in zip(id0,id1,lap_a0,lap_b0):
                lap_a[i] += la0
                lap_b[i] += lb0
                lap_a[j] -= la0
                lap_b[j] -= lb0
            ab2 = a*b**2
            #a += eval("(diff_a*lap_a - ab2 + f*(1-a))*dt")
            #b += eval("(diff_b*lap_b + ab2 - (k+f)*b)*dt")
            a += (diff_a*lap_a - ab2 + f*(1-a))*dt
            b += (diff_b*lap_b + ab2 - (k+f)*b)*dt
        return a, b
except:
    pass
