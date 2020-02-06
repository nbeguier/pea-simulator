#!/usr/bin/env python3
""" PEA simulateur """

# Standard library imports
import sys

# Third party library imports
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Debug
from pdb import set_trace as st

VERSION = '0.0.1'

## VARS
DATE_DEPART = '2019/01/01'
EURO_DEPART = 10000
TAXE_OPERATION = {
    500: 1.95,
    2000: 3.9,
    3250: '0.2%',
    10000: '0.2%',
    100000: '0.2%',
    150000: '0.2%',
}

def calcul_taxe(prix):
    for limit in TAXE_OPERATION:
        if prix < limit:
            if isinstance(TAXE_OPERATION[limit], str):
                return prix + prix*float(TAXE_OPERATION[limit].split('%')[0])/100
            return prix + float(TAXE_OPERATION[limit])
    return prix

def get_ref_name(ref):
    with open('references/cac40.txt', 'r') as ref_file:
        for line in ref_file.readlines():
            if line.split(';')[0] == ref:
                return line.split(';')[1].split('\n')[0]

def get_var(ref, prix, contexte, var):
    dernier_mois = contexte['date'] + relativedelta(months=var)
    with open('cotations/Cotations{}{:02d}.txt'.format(
            dernier_mois.year,
            dernier_mois.month), 'r') as cotations_file:
        for line in cotations_file.readlines():
            if ref == line.split(';')[0]:
                return round(float(prix) - float(line.split(';')[5]), 2)

def aide():
    print("[ai]de")
    print("[ac]hat d'actions")
    print("[v]ente d'actions")
    print("[d]ashboard")
    print("[s]uivant: passe au prochain mois")
    print("[e]xit")

def liste_actions(contexte):
    """
    https://www.abcbourse.com/download/historiques.aspx
    """
    print('Nom  Reference  Prix  |  Variation 1 mois  |  Variation 6 mois  |  Variation 1 an')
    with open('cotations/Cotations{}{:02d}.txt'.format(
            contexte['date'].year,
            contexte['date'].month), 'r') as cotations_file:
        for line in cotations_file.readlines():
            ref = line.split(';')[0]
            prix = line.split(';')[5]
            print('{} {} {}€ | {}€ | {}€ | {}€'.format(
                get_ref_name(ref),
                ref,
                prix,
                get_var(ref, prix, contexte, -1),
                get_var(ref, prix, contexte, -6),
                get_var(ref, prix, contexte, -12),
            ))

def get_action_prix(ref, contexte):
    with open('cotations/Cotations{}{:02d}.txt'.format(
            contexte['date'].year,
            contexte['date'].month), 'r') as cotations_file:
        for line in cotations_file.readlines():
            if line.split(';')[0] == ref:
                return float(line.split(';')[5])

def achat_actions(commande, contexte):
    ref = commande.split(' ')[1]
    num = int(commande.split(' ')[2])
    prix = num * get_action_prix(ref, contexte)
    prix = calcul_taxe(prix)
    contexte['solde'] -= prix
    contexte['actions'].append({'ref': ref, 'date': contexte['date'], 'num': num})
    return contexte

def achat(contexte):
    print("[l]iste des actions")
    print("[a]chat <ref action> <nombre>")
    print("[r]etour")
    while True:
        text = input('[{date}][{solde}€] > [achat] > '.format(
            date=contexte['date'],
            solde=contexte['solde']))
        if text.startswith('l'):
            liste_actions(contexte)
        elif text.startswith('a'):
            contexte = achat_actions(text, contexte)
        else:
            break
    return contexte

def vente():
    print("vente d'actions")

def dashboard(contexte):
    solde_total = contexte['solde']
    print('solde: {}€'.format(contexte['solde']))
    print('actions')
    for action in contexte['actions']:
        action_prix = action['num'] * get_action_prix(action['ref'], contexte)
        solde_total += action_prix
        print('[{}] {} {} {} = {}€'.format(
            action['date'],
            get_ref_name(action['ref']),
            action['ref'],
            action['num'],
            action_prix,
        ))
    print('solde total: {}€'.format(solde_total))

def suivant(contexte):
    with open('dividendes/Dividendes{}{:02d}.txt'.format(
            contexte['date'].year,
            contexte['date'].month), 'r') as dividendes_file:
        for line in dividendes_file.readlines():
            ref = line.split(';')[0]
            dividende = line.split(';')[2]
            for action in contexte['actions']:
                if action['ref'] == ref:
                    print('{} {}€'.format(get_ref_name(ref), dividende))
                    contexte['solde'] += float(dividende) * float(action['num'])

    contexte['date'] += relativedelta(months=+1)
    print("nouvelle date: {}".format(contexte['date']))

    return contexte['date']

def main():
    aide()
    contexte = {
        'date': datetime.strptime(DATE_DEPART, '%Y/%m/%d'),
        'solde': EURO_DEPART,
        'actions': list()
    }
    while True:
        text = input('[{date}][{solde}€] > '.format(
            date=contexte['date'],
            solde=contexte['solde']))
        if text.startswith('ai'):
            aide()
        elif text.startswith('ac'):
            contexte = achat(contexte)
        elif text.startswith('v'):
            vente()
        elif text.startswith('d'):
            dashboard(contexte)
        elif text.startswith('s'):
            contexte['date'] = suivant(contexte)
        elif text.startswith('e'):
            sys.exit(0)
        else:
            aide()
    return True


if __name__ == '__main__':
    main()
