# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import math
import numpy as np
import numpy.random as nprand
import matplotlib.pyplot as plt

# <codecell>

def error_heatmap(P):
    fail = np.arange(P+1)
    test = np.arange(P+1)
    data = np.zeros((P+1,P+1))
    for k in fail:
        for m in test:
            if (k < m):
                data[k,m] = 0.0
            else:
                data[k,m] = math.factorial(k)/float(math.factorial(k - m)) * math.factorial(P-m)/float(math.factorial(P))
    return data

# <codecell>

fig = plt.figure(figsize=(6,1.5), dpi=300, tight_layout=True)
n = [5, 10, 20, 40]
plt.title("Probabilty of undetected error")
rows = 1
cols = 4
for row in range(rows):
    for col in range(cols):
        nij = n[row*cols + col]
        ax = plt.subplot(rows,cols,row*cols + col + 1)
        plt.pcolor(error_heatmap(nij), cmap="gray", edgecolor="face")
        plt.title("%d redundant paths" % nij)
        plt.xlabel("Message copies")
        plt.ylabel("Compromised paths")
        ax.set_xlim([0,nij+1])
        ax.set_ylim([0,nij+1])
        for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
             ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(7)
fig.subplots_adjust(right=0.5)
cbar_ax = fig.add_axes([1, 0.28, 0.03, 0.55])
plt.colorbar(cax=cbar_ax, ticks=[0.0,0.5,1.0])
plt.savefig("output/fig-perror.pdf", dpi=300)
plt.savefig("output/fig-perror.eps", dpi=300)

# <codecell>


