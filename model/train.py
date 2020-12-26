#!/usr/bin/env python3
"""
PEA simulateur - Train model

Copyright (c) 2020-2021 Nicolas Beguier
Licensed under the MIT License
Written by Nicolas BEGUIER (nicolas_beguier@hotmail.com)
"""
from pathlib import Path
import sys

from sklearn.ensemble import RandomForestClassifier
import numpy

# Debug
# from pdb import set_trace as st

COTATION_DIR = sys.argv[1]
GEN_COTATION_DIR = sys.argv[2]

def main():
    """
    Main function
    """
    data = dict()

    cotation_path = Path(COTATION_DIR)
    for month_path in sorted(cotation_path.iterdir()):
        if not month_path.is_file():
            continue
        month_file = month_path.open()
        for isin_line in month_file.readlines():
            isin = isin_line.split(';')[0]
            date = isin_line.split(';')[1]
            val = float(isin_line.split(';')[5])
            if isin not in data:
                data[isin] = [[], []]
            data[isin][0].append(date)
            data[isin][1].append(val)

    models = []
    # Generate X, same for all model
    _x = []
    for isin in data:
        for i, val in enumerate(data[isin][1]):
            if i == 0:
                continue
            if len(_x) < i:
                _x.append([])
            _x[i-1].append(val - data[isin][1][i-1])
    for i, month in enumerate(data[isin][0]):
        if i == 0:
            continue
        _x[i-1].append(int(month.split('/')[1]) % 12 + 1)

    # Generate a specific y for each isin, 1 if >0, 0 if <= 0
    for isin in data:
        _y = []
        for i, val in enumerate(data[isin][1]):
            if i == 0:
                continue
            _y.append(int(data[isin][1][i] > data[isin][1][i-1]))
        clf = RandomForestClassifier(max_depth=100, random_state=0)
        clf.fit(_x, _y)
        models.append(clf)

    # Start prediction
    new_x = [_x[0]]
    month = _x[0][-1]
    year = 2018
    for k in range(48):
        new_x.append([])
        impact = numpy.random.normal()
        for i, isin in enumerate(data):
            prediction = models[i].predict_proba([new_x[k]])
            var = (prediction[0][1] - prediction[0][0]) + 0.1 * impact
            new_x[k+1].append(var)
        month = month % 12 + 1
        if month == 1:
            year += 1
        new_x[k+1].append(month)
        # Write in new files
        new_path = Path('{}/Cotations{}{:02d}.txt'.format(GEN_COTATION_DIR, year, month))
        with new_path.open('a') as new_file:
            for i, isin in enumerate(data):
                val = data[isin][1][k] * (1 + 0.01*new_x[k+1][i])
                if len(data[isin][1]) <= k + 1:
                    data[isin][1].append(val)
                else:
                    data[isin][1][k+1] = val
                new_file.write(f'{isin};;{new_x[k+1][i]};{val};{val};{val};\n')

if __name__ == '__main__':
    main()
