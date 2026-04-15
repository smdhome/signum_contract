# signum_contract
Signum Contract Manager: signum_contract

Overview
--------
The Signum Contract Manager (signum_contract.py) is a python and tkinter program that 
uses the Signum API to get a list of the contracts created by Signa wallet provided.
Clicking on any non-zero balance will offer to send a cancellation request to the contract.  
This is useful when a user loses control of a BUY or SELL contract created by BTDEX and needs to cancel it and get any balance held by that contract refunded.

The user will need to enter their secret passphrase to perform the cancelation.  This info is not stored by the program of compromised.

Features
--------
- The signum contracts are reported by contract address (S- or TS-).  

- Clicking on a non-zero contract balance, will attempt to cancel the contract holding that amount by sending the unencrypted message: b00e004992c79bd8000000000000000000000000000000000000000000000000 with 0.2 SIGNA and 0.03 SIGNA fee to that contract address after securely prompting for a secret passphrase. 

- Clicking on the contract addresses open that address in the signum explorer.

- This program can be run using Python3.  A portable executable version is also provided.

=====

To make this Python script a Portable Windows Executable (.exe)

Step 1 — Install PyInstaller

pip install pyinstaller

Step 2 — Build a single portable EXE
Run this in the same folder:

pyinstaller --onefile --windowed signum_contracts.py
