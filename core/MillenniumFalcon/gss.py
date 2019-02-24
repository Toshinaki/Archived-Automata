#!/usr/bin/python
###############################################################################
## Description
###############################################################################
# helper functions for Google SpreadSheet

###############################################################################
## Imports
###############################################################################
import sys, re
from pathlib import Path
root = Path(__file__).absolute().parent.parent.parent
if not str(root.parent) in sys.path:
    sys.path.append(str(root.parent))

import numpy as np
import pandas as pd
import gspread

from Automata.core.helpers import col2num, num2col

###############################################################################
## Constants
###############################################################################
data_path           = root.joinpath('data')
SP_CREDNTIAL_FILE   = data_path.joinpath('gss_credential.json')                                         # authen info for gspread API
SP_SCOPE            = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive'] # gspread API URL(spreadsheets, gdrive)


credentials = None
try:
    from oauth2client.client import SignedJwtAssertionCredentials
    import json, os

    json_key = json.loads(os.read(os.open(SP_CREDNTIAL_FILE, os.O_RDONLY),9999999))
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), SP_SCOPE)
except FileNotFoundError:
    pass
except ImportError:
    from oauth2client.service_account import ServiceAccountCredentials
    
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(SP_CREDNTIAL_FILE, SP_SCOPE)
    except FileNotFoundError:
        pass
if not credentials:
    print('Warning: Credential file is not found. Google apps functions cannot be used.')
    
###############################################################################
## Functions
###############################################################################
def get_spreadsheet(key_or_url):
    gc = gspread.authorize(credentials)
    try:
        return gc.open_by_key(key_or_url)
    except:
        return gc.open_by_url(key_or_url)

def get_sheet(key_or_url, sheet_name):
    gc = gspread.authorize(credentials)
    try:
        sp = gc.open_by_key(key_or_url)
    except:
        sp = gc.open_by_url(key_or_url)
    return sp.worksheet(sheet_name)

def get_sheet_data(sheet, *sheet_range, header=1):
    if sheet_range:
        return get_range_data(sheet, *sheet_range, header=header)

    values = sheet.get_all_values()
    if header:
        df = pd.DataFrame(values[header:], columns=values[header-1])
    else:
        df = pd.DataFrame(values)
    return df

def get_range_data(sheet, *args, header=1):
    r = sheet.range(*args)
    if len(args) == 1: # A1 notation
        ptn = re.compile(r'([A-Z]+)(\d+):([A-Z]+)(\d+)')
        start_col, start_row, end_col, end_row = ptn.findall(*args)[0]
        start_col, end_col = col2num(start_col), col2num(end_col)
        start_row, end_row = int(start_row), int(end_row)
    else:
        start_row, start_col, end_row, end_col = args
    
    values = np.array([cell.value for cell in r]).reshape((end_row-start_row+1, end_col-start_col+1))
    if header:
        df = pd.DataFrame(values[header:], columns=values[header-1])
    else:
        df = pd.DataFrame(values)
    return df