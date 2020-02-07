#!/usr/bin/env python3
""" PEA simulateur """

# Standard library imports
from datetime import datetime
from os.path import exists
import pickle
import sys

# Third party library imports
from dateutil.relativedelta import relativedelta
from tabulate import tabulate

# Debug
# from pdb import set_trace as st

VERSION = '1.1.0'

## VARS
START_DATE = '2019/01/01'
START_MONEY = 10000
BANK_TAX = {
    500: 1.95,
    2000: 3.9,
    3250: '0.2%',
    10000: '0.2%',
    100000: '0.2%',
    150000: '0.2%',
}

def compute_tax(price):
    """
    Fonction retournant la taxe associée au price d'achat d'actions
    """
    for limit in BANK_TAX:
        if price < limit:
            if isinstance(BANK_TAX[limit], str):
                return price*float(BANK_TAX[limit].split('%')[0])/100
            return float(BANK_TAX[limit])
    return 0

def get_ref_data(ref):
    """
    Fonction retournant les données d'une référence d'action
    Nom, Secteur, Industrie
    """
    cac40_filename = 'references/cac40.txt'
    if not exists(cac40_filename):
        print('Fichier manquant: {}'.format(cac40_filename))
        return 'Unknown', 'Unknown', 'Unknown'
    with open(cac40_filename, 'r') as ref_file:
        for line in ref_file.readlines():
            if line.split(';')[0] == ref:
                return line.split(';')[1].split('\n')[0], \
                    line.split(';')[2].split('\n')[0], \
                    line.split(';')[3].split('\n')[0]
    return 'Unknown', 'Unknown', 'Unknown'

def get_var(ref, price, context, var):
    """
    Fonction retournant la variance des mois précédants
    """
    dernier_mois = context['date'] + relativedelta(months=var)
    cotations_filename = 'cotations/Cotations{}{:02d}.txt'.format(
        dernier_mois.year,
        dernier_mois.month)
    if not exists(cotations_filename):
        print('Fichier manquant: {}'.format(cotations_filename))
        return 0
    with open(cotations_filename, 'r') as cotations_file:
        for line in cotations_file.readlines():
            if ref == line.split(';')[0]:
                return round(float(price) - float(line.split(';')[5]), 2)
    return 0

def display_help():
    """
    Fonction affichant l'aide
    """
    print("[a]chat <ref> <nombre>")
    print("[v]ente <ref> <nombre>")
    print("[l]iste [<filtre>]")
    print("[d]ashboard")
    print("[s]uivant: passe au prochain mois")
    print("[c]lôture du PEA")
    print("[e]xit")
    print("[sauvegarder]")
    print("[*]: affiche l'aide")

def list_shares(context, filter_str):
    """
    Fonction listant les actions disponibles
    https://www.abcbourse.com/download/historiques.aspx
    """
    listing = list()
    cotations_filename = 'cotations/Cotations{}{:02d}.txt'.format(
        context['date'].year,
        context['date'].month)
    if not exists(cotations_filename):
        print('Fichier manquant: {}'.format(cotations_filename))
        return None
    with open(cotations_filename, 'r') as cotations_file:
        for line in cotations_file.readlines():
            ref = line.split(';')[0]
            price = line.split(';')[5]
            name, area, industry = get_ref_data(ref)
            result = [
                name,
                ref,
                price,
                get_var(ref, price, context, -1),
                get_var(ref, price, context, -6),
                get_var(ref, price, context, -12),
                area,
                industry,
            ]
            if True in [filter_str.lower() in str(value).lower() for value in result]:
                listing.append(result)
        print(tabulate(listing, [
            'Nom',
            'Reference',
            'Prix',
            'Variation 1 mois',
            'Variation 6 mois',
            'Variation 1 an',
            'Secteur',
            'Industrie']))

def list_my_shares(context):
    """
    Fonction listant les actions détenues
    """
    listing = list()
    total_balance = context['balance']
    for share in context['shares']:
        share_price = get_share_price(share['ref'], context)
        share_value = share['num'] * share_price
        total_balance += share_value
        month_passed = int(round((share['date'] - context['date']).days/30, 0))
        var_1_month = 'N.A'
        var_6_month = 'N.A'
        if month_passed <= -1:
            var_1_month = share['num'] * get_var(share['ref'], share_price, context, -1)
        if month_passed <= -6:
            var_6_month = share['num'] * get_var(share['ref'], share_price, context, -6)
        listing.append([
            share['date'],
            get_ref_data(share['ref'])[0],
            share['ref'],
            share['num'],
            round(share_value, 2),
            var_1_month,
            var_6_month,
            share['num'] * get_var(share['ref'], share_price, context, month_passed)
        ])
    print(tabulate(listing, [
        "Date d'achat",
        'Nom',
        'Reference',
        'Nombre',
        'Valeur actuelle',
        'Variation 1 mois',
        'Variation 6 mois',
        'Plus-value totale']))
    return total_balance

def get_share_price(ref, context):
    """
    Fonction retournant le price courant d'une référence d'action
    """
    cotations_filename = 'cotations/Cotations{}{:02d}.txt'.format(
        context['date'].year,
        context['date'].month)
    if not exists(cotations_filename):
        print('Fichier manquant: {}'.format(cotations_filename))
        return 0
    with open(cotations_filename, 'r') as cotations_file:
        for line in cotations_file.readlines():
            if line.split(';')[0] == ref:
                return float(line.split(';')[5])
    return 0

def buy_share(commande, context):
    """
    Fonction d'achat d'action
    """
    try:
        ref = commande.split(' ')[1]
        num = int(commande.split(' ')[2])
    except IndexError:
        print('Erreur saisie')
        display_help()
        return context
    price = num * get_share_price(ref, context)
    price += compute_tax(price)
    context['balance'] -= price
    context['shares'].append({'ref': ref, 'date': context['date'], 'num': num})
    return context

def sell_share(commande, context):
    """
    Fonction de vente d'action
    """
    try:
        ref = commande.split(' ')[1]
        num = int(commande.split(' ')[2])
    except IndexError:
        print('Erreur saisie')
        display_help()
        return context
    price = num * get_share_price(ref, context)
    price -= compute_tax(price)
    for share in context['shares']:
        if share['ref'] == ref and share['num'] >= num:
            context['balance'] += price
            share['num'] -= num
    return context

def dashboard(context):
    """
    Fonction affichant le dashboard d'actions
    """
    print('Solde: {}€'.format(round(context['balance'], 2)))
    print('Actions')
    print('=======')
    total_balance = list_my_shares(context)
    print('Solde total: {}€'.format(round(total_balance, 2)))

def next_month(context):
    """
    Fonction permettant de passer au mois suivant
    """
    dividendes_filename = 'dividendes/Dividendes{}{:02d}.txt'.format(
        context['date'].year,
        context['date'].month)
    if exists(dividendes_filename):
        dividendes_file = open(dividendes_filename, 'r')
        for line in dividendes_file.readlines():
            ref = line.split(';')[0]
            dividende = line.split(';')[2]
            for share in context['shares']:
                if share['ref'] == ref:
                    amount = float(dividende) * float(share['num'])
                    percent = 100 * float(dividende) / get_share_price(share['ref'], context)
                    print('Versement de dividendes de {}: {}€, {}%'.format(
                        get_ref_data(ref)[0],
                        amount,
                        round(percent, 2)))
                    context['balance'] += amount
        dividendes_file.close()

    context['date'] += relativedelta(months=+1)
    print('nouvelle date: {}'.format(context['date']))

    return context['date']

def closing(context):
    """
    Fonction de clôture du PEA
    """
    list_my_shares(context)
    print("[c]loture <années ancienneté>")
    print("[r]etour")
    while True:
        text = input('[{date}][{balance}€] > [cloture] > '.format(
            date=context['date'],
            balance=round(context['balance'], 2)))
        if text.startswith('c'):
            # TODO
            list_my_shares(context)
        else:
            break

def save(context):
    """
    Fonction sauvegardant la partie
    """
    filename = input('Comment nommer la sauvegarde ? [save.txt] ')
    if not filename:
        filename = 'save.txt'
    afile = open(filename, 'wb')
    pickle.dump(context, afile)
    afile.close()
    print('Partie sauvegardée !')

def load(filename):
    """
    Fonction chargeant la partie
    """
    afile = open(filename, 'rb')
    context = pickle.load(afile)
    afile.close()
    print('Partie chargée !')
    return context

def main():
    """
    Fonction principale
    """
    if sys.argv and exists(sys.argv[1]):
        context = load(sys.argv[1])
    else:
        context = {
            'date': datetime.strptime(START_DATE, '%Y/%m/%d'),
            'balance': START_MONEY,
            'shares': list()
        }
    display_help()
    while True:
        text = input('[{date}][{balance}€] > '.format(
            date=context['date'],
            balance=round(context['balance'], 2)))
        if text.startswith('a'):
            context = buy_share(text, context)
        elif text.startswith('v'):
            context = sell_share(text, context)
        elif text.startswith('l'):
            filter_str = ''
            if len(text.split(' ')) > 1:
                filter_str = text.split(' ')[1]
            list_shares(context, filter_str)
        elif text.startswith('d'):
            dashboard(context)
        elif text.startswith('sa'):
            text = input('Êtes-vous sûr de vouloir sauvegarder ? [y/N] ')
            if text.lower() == 'y':
                save(context)
        elif text.startswith('s'):
            context['date'] = next_month(context)
        elif text.startswith('c'):
            closing(context)
        elif text.startswith('e'):
            text = input('Êtes-vous sûr de vouloir quitter ? [y/N] ')
            if text.lower() == 'y':
                sys.exit(0)
        else:
            display_help()
    return True


if __name__ == '__main__':
    main()
