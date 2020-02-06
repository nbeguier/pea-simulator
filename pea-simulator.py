#!/usr/bin/env python3
""" PEA simulateur """

# Standard library imports
import sys

# Third party library imports
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Debug
# from pdb import set_trace as st

VERSION = '1.0.0'

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

def get_ref_name(ref):
    """
    Fonction retournant le nom d'une référence d'action
    """
    with open('references/cac40.txt', 'r') as ref_file:
        for line in ref_file.readlines():
            if line.split(';')[0] == ref:
                return line.split(';')[1].split('\n')[0]
    return 'Unknown'

def get_var(ref, price, context, var):
    """
    Fonction retournant la variance des mois précédants
    """
    dernier_mois = context['date'] + relativedelta(months=var)
    with open('cotations/Cotations{}{:02d}.txt'.format(
            dernier_mois.year,
            dernier_mois.month), 'r') as cotations_file:
        for line in cotations_file.readlines():
            if ref == line.split(';')[0]:
                return round(float(price) - float(line.split(';')[5]), 2)
    return 0

def display_help():
    """
    Fonction affichant l'aide
    """
    print("[a]chat d'actions")
    print("[v]ente d'actions")
    print("[d]ashboard")
    print("[s]uivant: passe au prochain mois")
    print("[c]lôture du PEA")
    print("[e]xit")
    print("[*]: affiche l'aide")

def list_shares(context):
    """
    Fonction listant les actions disponibles
    https://www.abcbourse.com/download/historiques.aspx
    """
    print('Nom  Reference  Prix  |  Variation 1 mois  |  Variation 6 mois  |  Variation 1 an')
    with open('cotations/Cotations{}{:02d}.txt'.format(
            context['date'].year,
            context['date'].month), 'r') as cotations_file:
        for line in cotations_file.readlines():
            ref = line.split(';')[0]
            price = line.split(';')[5]
            print('{} {} {}€ | {}€ | {}€ | {}€'.format(
                get_ref_name(ref),
                ref,
                price,
                get_var(ref, price, context, -1),
                get_var(ref, price, context, -6),
                get_var(ref, price, context, -12),
            ))

def list_my_shares(context):
    """
    Fonction listant les actions détenues
    """
    total_balance = context['balance']
    for action in context['shares']:
        action_price = action['num'] * get_action_price(action['ref'], context)
        total_balance += action_price
        print('[{}] {} {} {} = {}€'.format(
            action['date'],
            get_ref_name(action['ref']),
            action['ref'],
            action['num'],
            round(action_price, 2),
        ))
    return total_balance

def get_action_price(ref, context):
    """
    Fonction retournant le price courant d'une référence d'action
    """
    with open('cotations/Cotations{}{:02d}.txt'.format(
            context['date'].year,
            context['date'].month), 'r') as cotations_file:
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
        return context
    price = num * get_action_price(ref, context)
    price += compute_tax(price)
    context['balance'] -= price
    context['shares'].append({'ref': ref, 'date': context['date'], 'num': num})
    return context

def buy(context):
    """
    Fonction d'interface d'achat d'actions
    """
    print("[l]iste des actions")
    print("[a]chat <ref action> <nombre>")
    print("[r]etour")
    while True:
        text = input('[{date}][{balance}€] > [achat] > '.format(
            date=context['date'],
            balance=round(context['balance'], 2)))
        if text.startswith('l'):
            list_shares(context)
        elif text.startswith('a'):
            context = buy_share(text, context)
        else:
            break
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
        return context
    price = num * get_action_price(ref, context)
    price -= compute_tax(price)
    for action in context['shares']:
        if action['ref'] == ref and action['num'] >= num:
            context['balance'] += price
            action['num'] -= num
    return context

def sell(context):
    """
    Fonction d'interface de vente d'actions
    """
    list_my_shares(context)
    print("[v]ente <ref action> <nombre>")
    print("[r]etour")
    while True:
        text = input('[{date}][{balance}€] > [vente] > '.format(
            date=context['date'],
            balance=round(context['balance'], 2)))
        if text.startswith('v'):
            context = sell_share(text, context)
            list_my_shares(context)
        else:
            break
    return context

def dashboard(context):
    """
    Fonction affichant le dashboard d'actions
    """
    print('solde: {}€'.format(round(context['balance'], 2)))
    print('shares')
    total_balance = list_my_shares(context)
    print('solde total: {}€'.format(round(total_balance, 2)))

def next_month(context):
    """
    Fonction permettant de passer au mois suivant
    """
    with open('dividendes/Dividendes{}{:02d}.txt'.format(
            context['date'].year,
            context['date'].month), 'r') as dividendes_file:
        for line in dividendes_file.readlines():
            ref = line.split(';')[0]
            dividende = line.split(';')[2]
            for action in context['shares']:
                if action['ref'] == ref:
                    print('{} {}€'.format(get_ref_name(ref), dividende))
                    context['balance'] += float(dividende) * float(action['num'])

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

def main():
    """
    Fonction principale
    """
    display_help()
    context = {
        'date': datetime.strptime(START_DATE, '%Y/%m/%d'),
        'balance': START_MONEY,
        'shares': list()
    }
    while True:
        text = input('[{date}][{balance}€] > '.format(
            date=context['date'],
            balance=round(context['balance'], 2)))
        if text.startswith('a'):
            context = buy(context)
        elif text.startswith('v'):
            context = sell(context)
        elif text.startswith('d'):
            dashboard(context)
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
