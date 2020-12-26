#!/usr/bin/env python3
"""
PEA simulateur - Draw cotation

Copyright (c) 2020-2021 Nicolas Beguier
Licensed under the MIT License
Written by Nicolas BEGUIER (nicolas_beguier@hotmail.com)
"""
from pathlib import Path
import sys

import matplotlib.pyplot as plt

# Debug
# from pdb import set_trace as st

COTATION_DIR = sys.argv[1]

def main():
    """
    Main function
    """
    data = dict()

    cotation_path = Path(COTATION_DIR)
    count = 0
    for month_path in sorted(cotation_path.iterdir()):
        if not month_path.is_file():
            continue
        month_file = month_path.open()
        for isin_line in month_file.readlines():
            isin = isin_line.split(';')[0]
            date = count # isin_line.split(';')[1]
            # val = float(isin_line.split(';')[5])
            val = float(isin_line.split(';')[2])
            if isin not in data:
                data[isin] = [[], []]
            data[isin][0].append(date)
            data[isin][1].append(val)
        count += 1

    for isin in data:
        plt.plot(data[isin][0],data[isin][1], label=f'Generated isin {isin}')
    plt.xlabel('date')
    plt.ylabel('value')
    plt.title(f'Finance of {isin}')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main()
