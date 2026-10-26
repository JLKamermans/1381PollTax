# -*- coding: utf-8 -*-


import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from pylab import *

# Plot parameters
params = {
    "font.size": 12,
    "figure.figsize": (6.4, 4.8),
    "figure.subplot.left": 0.0,
    "figure.subplot.right": 1,
    "figure.subplot.bottom": 0,
    "figure.subplot.top": 1,
    "figure.subplot.wspace": 0,
    "figure.subplot.hspace": 0,
    "lines.markersize": 6,
    "lines.linewidth": 3.0,
    "figure.max_open_warning": 0,
    "mathtext.fontset": 'cm' 
}
rcParams.update(params)

# Make it so we can use the correct fonts
from matplotlib import font_manager

# Insert where the fonts are stored here!
font_dir = [r'your/font/library']
for font in font_manager.findSystemFonts(font_dir):
    try:
        font_manager.fontManager.addfont(font)
    except:
        continue
   
plt.rcParams["font.family"] = "Linux Libertine Display O"
plt.clf()

# This function calculates the Gini index of a set of assessments in a very quick manner
def Gini(x):
    rank = np.argsort(np.argsort(x))
    return 2*np.cov(rank, x, ddof=0)[1,0]/(np.sum(x))*len(x)/(len(x)-1)

# This function calculates a random Lomax distribution for the number of assessments required, "num"
# It is given by: p(x)= alpha/lamb(1+(x/lamb))^-(alpha + 1)
def Lomax(num):
    while(True):
        count = 0
        # Take a random value of alpha, somewhere between 1 and 5, to somewhat reflect "realistic" distributions
        alpha = np.random.uniform(1,5)
        # The below relation ensures that the average assessment is 1
        lamb = 2/3*(alpha - 1)
        # Because a random number of draws from a distribution might not have a proper average, we will try up to 50
        # times to draw a number of assessments and check the average. If we don't find a proper distribution, we 
        # redraw alpha and lambda
        while count < 50:
            y = np.random.uniform(0,1,num)
            inv_cdf = lamb*(-1+(1-y)**(-1/alpha)) + 1/3
            # If the average is within reason, we return the result times 12, to make it a number of pence
            if np.mean(inv_cdf) > 0.95 and np.mean(inv_cdf) < 1.05:
                if len(inv_cdf[inv_cdf > 20]) == 0:
                    return inv_cdf*12
                else:
                    count += 1
            else:
                count += 1
    
# This function calculates the maximum entropy for a distribution and binning (here, the binning is 2d in size between 0 and 4s)
def MaxPossibleEntropy(x):
    if x < 46:
        return -np.log(1/x)
    else:
        factor = divmod(x,46)[0]
        extra = divmod(x,46)[1]
        return -(46-extra)*factor/x*np.log(factor/x) - extra*(factor + 1)/x*np.log((factor + 1)/x)

# This function calculates the normalised Shannon entropy of a distibution
def NormalisedShannonEntropy(x):
    number_under_4s = len(x[x<48.01])
    xNew = np.histogram(x,bins=np.arange(2,49))[0]
    p_x = xNew/sum(xNew)
    p_x = p_x[p_x > 0] #since log(0) is not defined
    return -sum(p_x*np.log(p_x))/MaxPossibleEntropy(number_under_4s) #normalise it by the max obtainable entropy


# Define some lists to store things in
gini_true = []
gini_oftenOccurring = []
gini_8 = []
gini_4 = []
gini_2 = []
shannon_oftenOccurring = []
shannon_8 = []
shannon_4 = []
shannon_2 = []


# Define the binning
bins1 = np.linspace(4,240,num=237) -.5
centre1 = bins1[:-1] + (bins1[1]-bins1[0])/2
bins2 = np.linspace(4,240,num=119) - 1
centre2 = bins2[:-1] + (bins2[1]-bins2[0])/2
bins4 = np.linspace(4,240,num=60) -2
centre4 = bins4[:-1] + (bins4[1]-bins4[0])/2
bins6 = np.linspace(4,244,num=41) -3
centre6 = bins6[:-1] + (bins6[1]-bins6[0])/2
bins8 = np.linspace(4,244,num=31) - 4
centre8 = bins8[:-1] + (bins8[1]-bins8[0])/2

# The very specific binning of the most often Occurring assessments
centreOftenOccurring = np.append([4,6,12,15,18,24,30,36,40,48],np.linspace(60,240,num = 16))
binsOftenOccurring = np.append([4,5,9,13.5,16.5,21,27,33,38,44],np.linspace(60,240,num = 16)-6)
binsOftenOccurring = np.append(binsOftenOccurring,[240])

# Here, we define the number of simulated settlements
numberOfSimulations = 10000
minNumberOfInhabitants = 20
maxNumberOfInhabitants = 300

for i in tqdm(range(numberOfSimulations)):
    # Pick a random number of inhabitants between the minimum and maximum
    numberInhabitants = np.random.randint(minNumberOfInhabitants,maxNumberOfInhabitants)
    
    xTrue = Lomax(numberInhabitants)
    x2, _ = np.histogram(xTrue, bins=bins2)
    x4, _ = np.histogram(xTrue, bins=bins4)
    x8, _ = np.histogram(xTrue, bins=bins8)
    xOftenOccurring, _ = np.histogram(xTrue, bins=binsOftenOccurring)
    
    x2 = np.repeat(centre2,x2.astype('int64'))
    x4 = np.repeat(centre4,x4.astype('int64'))
    x8 = np.repeat(centre8,x8.astype('int64'))
    xOftenOccurring = np.repeat(centreOftenOccurring,xOftenOccurring.astype('int64'))
    
    
    gini_true.append(Gini(xTrue))
    gini_4.append(Gini(x4))
    gini_2.append(Gini(x2))
    gini_8.append(Gini(x8))
    gini_oftenOccurring.append(Gini(xOftenOccurring))
    
    shannon_4.append(NormalisedShannonEntropy(x4))
    shannon_2.append(NormalisedShannonEntropy(x2))
    shannon_8.append(NormalisedShannonEntropy(x8))
    shannon_oftenOccurring.append(NormalisedShannonEntropy(xOftenOccurring))

# Print the averages and uncertainties when we are done
print("Gini true: " + str(np.mean(gini_true))+ " +- " +str(2*np.std(gini_true)))
print("Gini 2: " + str(np.mean(gini_2)) + " +- " +str(2*np.std(gini_2)))
print("Gini 4: " + str(np.mean(gini_4)) + " +- " +str(2*np.std(gini_4)))
print("Gini 8: " + str(np.mean(gini_8)) + " +- " +str(2*np.std(gini_8)))
print("Gini most often Occurring: " + str(np.mean(gini_oftenOccurring)) + " +- " +str(2*np.std(gini_oftenOccurring)))

# Idem for the Shannon entropies
print("Shannon 2: " + str(np.mean(shannon_2)))
print("Shannon 4: " + str(np.mean(shannon_4)))
print("Shannon 8: " + str(np.mean(shannon_8)))
print("Shannon most often Occurring: " + str(np.mean(shannon_oftenOccurring)))


# Define the figure and its subfigures
fig = plt.figure(figsize = (13,15), constrained_layout=True)

gs = fig.add_gridspec(3,2, height_ratios=[1, 1, 0.5])
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
ax4 = fig.add_subplot(gs[1, 1])
# The bottom figure spans both virtual subfigures
ax5 = fig.add_subplot(gs[2, :])

listSubfigures = [ax1,ax2,ax3,ax4,ax5]

# We first create the true Gini figure at the bottom, so we can use its maximum to create
# a red-dashed line in the 2d histograms above
for i in [4,0,1,2,3]:
    if i == 0:
        h, xedges, yedges, im = listSubfigures[i].hist2d(shannon_2, gini_2, bins = 100, range = [[0,0.8],[0.2,0.65]], cmap = 'viridis_r', cmin = 0.1)
        listSubfigures[i].set_title("Binning interval 2d")
        listSubfigures[i].hlines(most_often_occ, 0, 0.8, 'red', linestyle = '--', zorder = -1)
    if i == 1:
        h, xedges, yedges, im = listSubfigures[i].hist2d(shannon_4, gini_4, bins = 100, range = [[0,0.8],[0.2,0.65]], cmap = 'viridis_r', cmin = 0.1)
        listSubfigures[i].set_title("Binning interval 4d")
        listSubfigures[i].hlines(most_often_occ, 0, 0.8, 'red', linestyle = '--', zorder = -1)
    if i == 2:
        h, xedges, yedges, im = listSubfigures[i].hist2d(shannon_8, gini_8, bins = 100, range = [[0,0.8],[0.2,0.65]], cmap = 'viridis_r', cmin = 0.1)
        listSubfigures[i].set_title("Binning interval 8d")
        listSubfigures[i].hlines(most_often_occ, 0, 0.8, 'red', linestyle = '--', zorder = -1)
    if i == 3:
        h, xedges, yedges, im = listSubfigures[i].hist2d(shannon_oftenOccurring, gini_oftenOccurring, bins = 100, range = [[0,0.8],[0.2,0.65]], cmap = 'viridis_r', cmin = 0.1)
        listSubfigures[i].set_title("Binning interval most Occurring")
        listSubfigures[i].hlines(most_often_occ, 0, 0.8, 'red', linestyle = '--', zorder = -1)
    if i == 4:
        uno, dos, _ = listSubfigures[i].hist(gini_true, bins = 100, range = [0.2,0.65])
        listSubfigures[i].set_title(r"True Gini Index $G$")
        most_often_occ = (dos[:-1])[uno == np.max(uno)] + (0.65 - 0.2)/100/2
    if i < 4:
        listSubfigures[i].set_xlabel(r"Normalised Shannon Entropy $\bar{H}$")
        listSubfigures[i].set_ylabel(r"Gini Index $G$")
    else:
        listSubfigures[i].set_xlabel(r"Gini Index $G$")
        listSubfigures[i].set_ylabel("Frequency")
    listSubfigures[i].grid(which = "major", axis="y",linestyle = "--", zorder = -1)
    listSubfigures[i].grid(which = "major", axis="x",linestyle = "--", zorder = -1)
    
    
    
# Last but not least, we create the colourbar that is shared for all 2d histograms
largest_value = np.max(h[h>1])
cbar = fig.colorbar(im, ax=listSubfigures, location="right", pad=0.02, ticks = [1,largest_value],aspect = 40)
cbar.ax.set_yticklabels(['0','1'])

# Save the figure
plt.savefig("Bigplot_simulations.pdf", bbox_inches = "tight")
plt.show()
