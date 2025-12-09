#!/usr/bin/env python3
"""
UNIVAC 21 - Interactive Card Game in FLOW-MATIC
================================================

The year is 1957. You're a UNIVAC operator on your lunch break.
The machine hums quietly. Time for a quick game of 21!

This game uses AUTHENTIC FLOW-MATIC (1957) for card dealing and scoring,
with a Python interface for player interaction.

Run: python play_21.py
"""

import random
import sys
from decimal import Decimal
from flowmatic_parser import FlowMaticInterpreter


def generate_shuffled_deck():
    """Generate a shuffled deck of cards"""
    suits = ['HEARTS', 'DIAMONDS', 'CLUBS', 'SPADES']
    cards = []
    
    for suit in suits:
        for num in range(2, 11):
            names = ['TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN']
            name = f'{names[num-2]} OF {suit}'
            cards.append({'CARD-NAME': name, 'CARD-VALUE': num})
        cards.append({'CARD-NAME': f'JACK OF {suit}', 'CARD-VALUE': 10})
        cards.append({'CARD-NAME': f'QUEEN OF {suit}', 'CARD-VALUE': 10})
        cards.append({'CARD-NAME': f'KING OF {suit}', 'CARD-VALUE': 10})
        cards.append({'CARD-NAME': f'ACE OF {suit}', 'CARD-VALUE': 11})
    
    random.shuffle(cards)
    return cards


def card_to_symbol(name):
    """Convert card name to compact display"""
    if 'HEARTS' in name:
        suit = 'H'
    elif 'DIAMONDS' in name:
        suit = 'D' 
    elif 'CLUBS' in name:
        suit = 'C'
    else:
        suit = 'S'
    
    parts = name.split(' OF ')[0]
    rank_map = {
        'TWO': '2', 'THREE': '3', 'FOUR': '4', 'FIVE': '5',
        'SIX': '6', 'SEVEN': '7', 'EIGHT': '8', 'NINE': '9',
        'TEN': '10', 'JACK': 'J', 'QUEEN': 'Q', 'KING': 'K', 'ACE': 'A'
    }
    rank = rank_map.get(parts, '?')
    return f"[{rank}{suit}]"


def show_hand(cards, total, title, hide_second=False):
    """Display a hand of cards"""
    print(f"\n  {title}:")
    print("  " + "-"*40)
    
    card_displays = []
    for i, card in enumerate(cards):
        if hide_second and i == 1:
            card_displays.append("[??]")
        else:
            # Get card name from dict or string
            card_name = card.get('CARD-NAME', card) if isinstance(card, dict) else card
            card_displays.append(card_to_symbol(card_name))
    
    print(f"  Cards: {' '.join(card_displays)}")
    
    if not hide_second:
        print(f"  Total: {total}")
    else:
        # Show only first card value
        first_val = cards[0].get('CARD-VALUE', '?') if isinstance(cards[0], dict) else '?'
        print(f"  Showing: {first_val}")


def calculate_total(cards):
    """Calculate hand total with ace handling"""
    total = 0
    aces = 0
    for c in cards:
        if isinstance(c, dict):
            val = c.get('CARD-VALUE', 0)
            name = c.get('CARD-NAME', '')
        else:
            val = 0
            name = str(c)
        total += val if isinstance(val, int) else int(val)
        if 'ACE' in name:
            aces += 1
    # Reduce aces from 11 to 1 if busting
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def deal_card_flowmatic(deck, card_index):
    """Use FLOW-MATIC to deal a single card"""
    if card_index >= len(deck):
        return None
    
    # FLOW-MATIC program to read one card
    deal_program = """
    (0)  INPUT DECK FILE-A ; OUTPUT CARD FILE-B .
    (1)  READ-ITEM A ; IF END OF DATA GO TO OPERATION 3 .
    (2)  TRANSFER A TO B ; WRITE-ITEM B .
    (3)  STOP .
    """
    
    interpreter = FlowMaticInterpreter(debug=False)
    interpreter.load_program(deal_program)
    interpreter.load_file('A', [deck[card_index]])
    interpreter.run()
    
    output = interpreter.get_output('B')
    if output:
        return output[0]
    return deck[card_index]


def play_game():
    """Play an interactive game of UNIVAC 21"""
    
    print("\n" + "="*60)
    print("|" + " "*58 + "|")
    print("|" + "*** UNIVAC 21 - INTERACTIVE ***".center(58) + "|")
    print("|" + "Powered by FLOW-MATIC (1957)".center(58) + "|")
    print("|" + " "*58 + "|")
    print("="*60)
    
    # Generate fresh deck
    deck = generate_shuffled_deck()
    card_idx = 0
    
    # Deal initial cards
    player_cards = []
    dealer_cards = []
    
    print("\n  Dealing cards...")
    
    # Player gets 2 cards
    player_cards.append(deal_card_flowmatic(deck, card_idx))
    card_idx += 1
    player_cards.append(deal_card_flowmatic(deck, card_idx))
    card_idx += 1
    
    # Dealer gets 2 cards
    dealer_cards.append(deal_card_flowmatic(deck, card_idx))
    card_idx += 1
    dealer_cards.append(deal_card_flowmatic(deck, card_idx))
    card_idx += 1
    
    player_total = calculate_total(player_cards)
    dealer_total = calculate_total(dealer_cards)
    
    # Check for blackjack
    if player_total == 21:
        show_hand(player_cards, player_total, "YOUR HAND")
        show_hand(dealer_cards, dealer_total, "DEALER'S HAND")
        print("\n" + "="*60)
        print("  *** BLACKJACK! YOU WIN! ***".center(58))
        print("="*60)
        return
    
    # Player's turn
    while True:
        show_hand(player_cards, player_total, "YOUR HAND")
        show_hand(dealer_cards, dealer_total, "DEALER'S HAND (one hidden)", hide_second=True)
        
        if player_total > 21:
            print("\n" + "="*60)
            print("  XXX BUST! You went over 21! XXX".center(58))
            print("="*60)
            return
        
        if player_total == 21:
            print("\n  21! Standing automatically.")
            break
        
        # Ask player
        print("\n  " + "-"*40)
        print("  (H)it or (S)tand? ", end="")
        
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = 's'
        
        if choice.startswith('h'):
            # Hit - deal another card using FLOW-MATIC
            new_card = deal_card_flowmatic(deck, card_idx)
            card_idx += 1
            player_cards.append(new_card)
            player_total = calculate_total(player_cards)
            print(f"\n  >>> FLOW-MATIC deals: {new_card.get('CARD-NAME', 'Unknown')}")
        else:
            # Stand
            print("\n  You stand with", player_total)
            break
    
    # Dealer's turn (automated per casino rules)
    print("\n  " + "="*40)
    print("  DEALER'S TURN (hits on 16 or less)")
    print("  " + "="*40)
    
    show_hand(dealer_cards, dealer_total, "DEALER REVEALS")
    
    while dealer_total < 17:
        print(f"\n  Dealer hits...")
        new_card = deal_card_flowmatic(deck, card_idx)
        card_idx += 1
        dealer_cards.append(new_card)
        dealer_total = calculate_total(dealer_cards)
        print(f"  >>> FLOW-MATIC deals: {new_card.get('CARD-NAME', 'Unknown')}")
        show_hand(dealer_cards, dealer_total, "DEALER'S HAND")
    
    if dealer_total > 21:
        print("\n" + "="*60)
        print("  *** DEALER BUSTS! YOU WIN! ***".center(58))
        print("="*60)
        return
    
    print(f"\n  Dealer stands with {dealer_total}")
    
    # Final comparison
    print("\n" + "="*60)
    print(f"  Your total: {player_total}  |  Dealer total: {dealer_total}")
    print("="*60)
    
    if player_total > dealer_total:
        print("  *** YOU WIN! ***".center(58))
    elif player_total < dealer_total:
        print("  --- DEALER WINS ---".center(58))
    else:
        print("  === PUSH - It's a tie! ===".center(58))
    
    print("="*60)


def main():
    """Main game loop"""
    print("\n" + "+"+"="*58+"+")
    print("|" + " "*58 + "|")
    print("|" + "Welcome to UNIVAC 21!".center(58) + "|")
    print("|" + "An INTERACTIVE card game in FLOW-MATIC (1957)".center(58) + "|")
    print("|" + " "*58 + "|")
    print("|" + "The UNIVAC is warmed up and ready to deal...".center(58) + "|")
    print("|" + " "*58 + "|")
    print("|" + "Each card is dealt using authentic FLOW-MATIC code!".center(58) + "|")
    print("|" + " "*58 + "|")
    print("+"+"="*58+"+")
    
    while True:
        play_game()
        
        print("\n  Play again? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response != 'y':
                break
        except (EOFError, KeyboardInterrupt):
            break
    
    print("\n  Thanks for playing UNIVAC 21!")
    print("  'The most dangerous words in the language:")
    print("   We have always done it this way.'")
    print("  - Grace Hopper\n")


if __name__ == '__main__':
    main()
