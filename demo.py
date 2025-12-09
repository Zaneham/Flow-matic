#!/usr/bin/env python3
"""
FLOW-MATIC Quick Demo
=====================
Run this to see FLOW-MATIC in action!

Just run: python demo.py
"""

from decimal import Decimal
from flowmatic_parser import FlowMaticInterpreter


def demo_invoice_generator():
    """
    Invoice Generator Demo
    ======================
    A real business application written in FLOW-MATIC!
    
    This is EXACTLY the kind of program Grace Hopper designed 
    FLOW-MATIC for in 1957.
    """
    
    print("\n" + "="*70)
    print("  FLOW-MATIC INVOICE GENERATOR")
    print("  A 1957 Business Application Running in 2024")
    print("="*70)
    
    # The authentic FLOW-MATIC source code
    invoice_program = """
    * FLOW-MATIC INVOICE GENERATOR
    * Generates invoices by matching orders with product catalog
    
    (0)  INPUT CUSTOMER-ORDERS FILE-A PRODUCT-CATALOG FILE-B ;
         OUTPUT INVOICE-OUTPUT FILE-C ;
         HSP D .
    
    * Read first records
    (1)  READ-ITEM A ;
         IF END OF DATA GO TO OPERATION 8 ;
         READ-ITEM B .
    
    * Match order with catalog - single-letter aliases FTW!
    (2)  COMPARE PRODUCT-NO (A) WITH PRODUCT-NO (B) ;
         IF EQUAL GO TO OPERATION 4 ;
         IF LESS GO TO OPERATION 3 ;
         OTHERWISE GO TO OPERATION 5 .
    
    * Order product not in catalog - try next order
    (3)  READ-ITEM A ;
         IF END OF DATA GO TO OPERATION 8 ;
         JUMP TO OPERATION 2 .
    
    * Match! Calculate line total
    (4)  TRANSFER A TO C ;
         MOVE PRODUCT-DESC (B) TO PRODUCT-DESC (C) ;
         MOVE UNIT-PRICE (B) TO UNIT-PRICE (C) ;
         MULTIPLY QUANTITY (A) BY UNIT-PRICE (B) GIVING LINE-TOTAL (C) ;
         WRITE-ITEM C ;
         PRINT-ITEM D ;
         READ-ITEM A ;
         IF END OF DATA GO TO OPERATION 8 ;
         JUMP TO OPERATION 2 .
    
    * Advance catalog
    (5)  READ-ITEM B ;
         IF END OF DATA GO TO OPERATION 6 ;
         JUMP TO OPERATION 2 .
    
    * End of catalog
    (6)  JUMP TO OPERATION 8 .
    
    * Reserved
    (7)  JUMP TO OPERATION 8 .
    
    * Finalize
    (8)  CLOSE-OUT FILES C ;
         STOP .
    """
    
    # Sample order data
    orders = [
        {'CUSTOMER-NO': 'C001', 'CUSTOMER-NAME': 'ACME CORPORATION', 
         'ORDER-NO': 'ORD-1957-001', 'PRODUCT-NO': 'P001', 'QUANTITY': 10},
        {'CUSTOMER-NO': 'C001', 'CUSTOMER-NAME': 'ACME CORPORATION',
         'ORDER-NO': 'ORD-1957-001', 'PRODUCT-NO': 'P002', 'QUANTITY': 25},
        {'CUSTOMER-NO': 'C002', 'CUSTOMER-NAME': 'UNIVERSAL EXPORTS',
         'ORDER-NO': 'ORD-1957-002', 'PRODUCT-NO': 'P001', 'QUANTITY': 50},
        {'CUSTOMER-NO': 'C002', 'CUSTOMER-NAME': 'UNIVERSAL EXPORTS',
         'ORDER-NO': 'ORD-1957-002', 'PRODUCT-NO': 'P003', 'QUANTITY': 5},
    ]
    
    # Product catalog
    products = [
        {'PRODUCT-NO': 'P001', 'PRODUCT-DESC': 'UNIVAC RIBBON CARTRIDGE', 
         'UNIT-PRICE': Decimal('12.50')},
        {'PRODUCT-NO': 'P002', 'PRODUCT-DESC': 'PUNCH CARDS (BOX OF 1000)',
         'UNIT-PRICE': Decimal('8.75')},
        {'PRODUCT-NO': 'P003', 'PRODUCT-DESC': 'MAGNETIC TAPE REEL',
         'UNIT-PRICE': Decimal('45.00')},
    ]
    
    print("\n--- INPUT DATA ---")
    print("\nCustomer Orders (File A):")
    for order in orders:
        print(f"  {order['CUSTOMER-NAME']}: {order['QUANTITY']}x Product {order['PRODUCT-NO']}")
    
    print("\nProduct Catalog (File B):")
    for prod in products:
        print(f"  {prod['PRODUCT-NO']}: {prod['PRODUCT-DESC']} @ ${prod['UNIT-PRICE']}")
    
    # Run the FLOW-MATIC program
    interpreter = FlowMaticInterpreter(debug=False)
    interpreter.load_program(invoice_program)
    interpreter.load_file('A', orders)
    interpreter.load_file('B', products)
    interpreter.run()
    
    # Display results
    print("\n--- INVOICE OUTPUT (File C) ---")
    print("-" * 70)
    print(f"{'CUSTOMER':<20} {'PRODUCT':<25} {'QTY':>5} {'PRICE':>10} {'TOTAL':>10}")
    print("-" * 70)
    
    grand_total = Decimal('0')
    for record in interpreter.get_output('C'):
        customer = record.get('CUSTOMER-NAME', 'N/A')
        product = record.get('PRODUCT-DESC', 'N/A')
        qty = record.get('QUANTITY', 0)
        price = record.get('UNIT-PRICE', Decimal('0'))
        total = record.get('LINE-TOTAL', Decimal('0'))
        
        print(f"{customer:<20} {product:<25} {qty:>5} ${price:>9.2f} ${total:>9.2f}")
        grand_total += total
    
    print("-" * 70)
    print(f"{'GRAND TOTAL':>62} ${grand_total:>9.2f}")
    print("-" * 70)


def demo_set_operation():
    """
    SET OPERATION Demo - The Feature COBOL Killed
    ==============================================
    
    Runtime modification of program flow in ONE ENGLISH SENTENCE.
    No Strategy pattern. No vtables. No function pointers.
    Just: SET OPERATION 5 TO GO TO OPERATION 10
    """
    
    print("\n" + "="*70)
    print("  SET OPERATION DEMO")
    print("  The Feature COBOL Killed - Runtime Flow Modification")
    print("="*70)
    
    program = """
    * Demonstrate SET OPERATION - runtime flow modification
    
    (0)  INPUT TRANSACTIONS FILE-A ACCOUNT-CONFIG FILE-B ;
         OUTPUT PROCESSED FILE-C ;
         HSP D .
    
    * Configure routes based on account type
    (1)  READ-ITEM B ;
         IF END OF DATA GO TO OPERATION 3 .
    
    * Dynamic routing - THIS is what COBOL killed!
    (2)  TEST ACCOUNT-TYPE (B) AGAINST "PREMIUM" ;
         IF EQUAL SET OPERATION 6 TO GO TO OPERATION 7 ;
         TEST ACCOUNT-TYPE (B) AGAINST "STANDARD" ;
         IF EQUAL SET OPERATION 6 TO GO TO OPERATION 8 ;
         READ-ITEM B ;
         IF END OF DATA GO TO OPERATION 3 ;
         JUMP TO OPERATION 2 .
    
    * Process transactions
    (3)  READ-ITEM A ;
         IF END OF DATA GO TO OPERATION 10 .
    
    (4)  TRANSFER A TO C .
    
    * Find account config
    (5)  JUMP TO OPERATION 6 .
    
    * DYNAMICALLY ROUTED! Target changes based on SET OPERATION
    (6)  JUMP TO OPERATION 8 .
    
    * PREMIUM processing - 5% bonus
    (7)  MULTIPLY AMOUNT (A) BY 1.05 GIVING PROCESSED-AMOUNT (C) ;
         MOVE "PREMIUM BONUS APPLIED" TO STATUS (C) ;
         JUMP TO OPERATION 9 .
    
    * STANDARD processing - no bonus
    (8)  MOVE AMOUNT (A) TO PROCESSED-AMOUNT (C) ;
         MOVE "STANDARD PROCESSING" TO STATUS (C) ;
         JUMP TO OPERATION 9 .
    
    * Write result
    (9)  WRITE-ITEM C ;
         PRINT-ITEM D ;
         JUMP TO OPERATION 3 .
    
    (10) STOP .
    """
    
    transactions = [
        {'ACCOUNT-NO': 'A001', 'AMOUNT': Decimal('100.00')},
        {'ACCOUNT-NO': 'A002', 'AMOUNT': Decimal('250.00')},
        {'ACCOUNT-NO': 'A001', 'AMOUNT': Decimal('500.00')},
    ]
    
    account_config = [
        {'ACCOUNT-NO': 'A001', 'ACCOUNT-TYPE': 'PREMIUM'},
        {'ACCOUNT-NO': 'A002', 'ACCOUNT-TYPE': 'STANDARD'},
    ]
    
    print("\nThe magic line: SET OPERATION 6 TO GO TO OPERATION 7")
    print("This CHANGES where operation 6 jumps to AT RUNTIME!")
    print("\nIn modern code, this requires:")
    print("  - Interface definition")
    print("  - Concrete strategy classes")
    print("  - Context class")
    print("  - Factory or dependency injection")
    print("\nIn FLOW-MATIC: ONE ENGLISH SENTENCE.\n")
    
    interpreter = FlowMaticInterpreter(debug=False)
    interpreter.load_program(program)
    interpreter.load_file('A', transactions)
    interpreter.load_file('B', account_config)
    interpreter.run()
    
    print("--- RESULTS ---")
    for record in interpreter.get_output('C'):
        acct = record.get('ACCOUNT-NO', 'N/A')
        amount = record.get('AMOUNT', Decimal('0'))
        processed = record.get('PROCESSED-AMOUNT', Decimal('0'))
        status = record.get('STATUS', 'N/A')
        print(f"  Account {acct}: ${amount:.2f} -> ${processed:.2f} ({status})")


def demo_file_aliases():
    """
    Single-Letter File Aliases Demo
    ================================
    
    FLOW-MATIC used (A), (B), (C) throughout the program.
    COBOL required verbose FD declarations and full names.
    
    18 FLOW-MATIC operations became 50+ COBOL statements!
    """
    
    print("\n" + "="*70)
    print("  SINGLE-LETTER FILE ALIASES")  
    print("  Another Feature COBOL Made Verbose")
    print("="*70)
    
    print("""
FLOW-MATIC (1957):
    COMPARE PRODUCT-NO (A) WITH PRODUCT-NO (B)
    TRANSFER A TO C
    WRITE-ITEM C

COBOL (1960):
    COMPARE PRODUCT-NUMBER OF INVENTORY-MASTER-FILE
        WITH PRODUCT-NUMBER OF PRICE-LIST-FILE
    MOVE CORRESPONDING INVENTORY-MASTER-RECORD
        TO OUTPUT-INVOICE-RECORD
    WRITE OUTPUT-INVOICE-RECORD

Grace Hopper believed brevity was a virtue.
CODASYL decided verbosity was better.
    """)
    
    program = """
    * File alias demonstration
    (0)  INPUT MASTER FILE-A DETAIL FILE-B ;
         OUTPUT MERGED FILE-C .
    
    (1)  READ-ITEM A ;
         READ-ITEM B .
    
    (2)  COMPARE KEY (A) WITH KEY (B) ;
         IF EQUAL GO TO OPERATION 3 ;
         IF LESS GO TO OPERATION 4 ;
         OTHERWISE GO TO OPERATION 5 .
    
    (3)  TRANSFER A TO C ;
         MOVE VALUE (B) TO DETAIL-VALUE (C) ;
         WRITE-ITEM C ;
         JUMP TO OPERATION 6 .
    
    (4)  TRANSFER A TO C ;
         WRITE-ITEM C ;
         READ-ITEM A ;
         IF END OF DATA GO TO OPERATION 7 ;
         JUMP TO OPERATION 2 .
    
    (5)  READ-ITEM B ;
         IF END OF DATA GO TO OPERATION 4 ;
         JUMP TO OPERATION 2 .
    
    (6)  READ-ITEM A ;
         READ-ITEM B ;
         IF END OF DATA GO TO OPERATION 7 ;
         JUMP TO OPERATION 2 .
    
    (7)  STOP .
    """
    
    master = [
        {'KEY': '001', 'NAME': 'ITEM ONE'},
        {'KEY': '002', 'NAME': 'ITEM TWO'},
        {'KEY': '004', 'NAME': 'ITEM FOUR'},
    ]
    
    detail = [
        {'KEY': '001', 'VALUE': Decimal('100')},
        {'KEY': '002', 'VALUE': Decimal('200')},
        {'KEY': '003', 'VALUE': Decimal('300')},
    ]
    
    interpreter = FlowMaticInterpreter(debug=False)
    interpreter.load_program(program)
    interpreter.load_file('A', master)
    interpreter.load_file('B', detail)
    interpreter.run()
    
    print("--- MERGED OUTPUT ---")
    for record in interpreter.get_output('C'):
        key = record.get('KEY', 'N/A')
        name = record.get('NAME', 'N/A')
        value = record.get('DETAIL-VALUE', 'N/A')
        print(f"  Key {key}: {name}, Value: {value}")


def main():
    """Run all demos"""
    
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "    FLOW-MATIC: GRACE HOPPER'S BUSINESS LANGUAGE (1957)    ".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#" + "    The first English-like programming language.".center(68) + "#")
    print("#" + "    Direct ancestor of COBOL.".center(68) + "#")
    print("#" + "    Running today, 67 years later.".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    demos = [
        ("Invoice Generator", demo_invoice_generator),
        ("SET OPERATION (The Feature COBOL Killed)", demo_set_operation),
        ("Single-Letter File Aliases", demo_file_aliases),
    ]
    
    for name, func in demos:
        print(f"\n\n>>> Running: {name}")
        func()
        print("\n" + "-"*70)
    
    print("\n" + "="*70)
    print("  DEMONSTRATION COMPLETE")
    print("  ")
    print("  FLOW-MATIC was developed 1955-1959 by Grace Hopper")
    print("  at Remington Rand for the UNIVAC I and UNIVAC II.")
    print("  ")
    print("  It proved that computers could understand English-like")
    print("  syntax, paving the way for COBOL and all that followed.")
    print("  ")
    print("  Some features were ahead of their time:")
    print("    - SET OPERATION: Runtime flow modification (killed by COBOL)")
    print("    - X-I Sections: Inline machine code (killed by COBOL)")
    print("    - Block Integrity: Built-in data validation (killed by COBOL)")
    print("    - File Aliases: Concise (A), (B), (C) syntax (killed by COBOL)")
    print("  ")
    print("  Grace Hopper knew what she was doing.")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()

