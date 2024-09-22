# run the 1D_ME_Explore.py for all four layers using a current and ref run
import os
for i in range(1,5):
    command = f"python 1D_ME_Explore.py PixelPhase1/Tracks/PXBarrel/charge_PXLayer_{i} 384032 383948"
    print(command)  
    os.system(command)
