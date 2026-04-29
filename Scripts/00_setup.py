# -*- coding: utf-8 -*-

import os

# Run this once before anything else
# It creates all the folders the project needs
#%%
BASE_DIR = r"c:\users\laure\onedrive\documents\github\ny-farm-wind-diversification"

folders = [
    os.path.join(BASE_DIR, "data", "raw"),
    os.path.join(BASE_DIR, "data", "clean"),
    os.path.join(BASE_DIR, "output", "figures"),
    os.path.join(BASE_DIR, "scripts"),
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Created: {folder}")

print()
print("Setup complete. You can now run 01_download_data.py")