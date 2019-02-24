#!/usr/bin/python

###############################################################################
## Description
###############################################################################


###############################################################################
## Imports 
###############################################################################
import sys, json
from pathlib import Path
root = Path(__file__).absolute().parent.parent
if not str(root.parent) in sys.path:
    sys.path.append(str(root.parent))

import datetime, importlib
import tkinter as tk
from tkinter import filedialog

import pandas as pd
from PyInquirer import prompt
from pyfiglet import Figlet

from Automata.core.udec.ulogger import create_logger
from Automata.core.helpers import circled_str, read_json, read_configuration, write_configuration
from Automata.core.hivemind import Queenb, Honeyb, Browserb
from Automata.core.MillenniumFalcon.gss import get_spreadsheet, get_sheet_data
###############################################################################
## CONSTANTS & HELPER FUNCTIONS
###############################################################################
config_path = root.joinpath('data/config.json')
log_path = root.joinpath('data/logs')
result_path = root.joinpath('data/results')
messages = read_json(root.joinpath('data/messages/{}.json'.format(read_configuration(config_path, 'language') or 'en')))
debug = False if (read_configuration(config_path, 'debug') in [0, "0"]) else True

logger = create_logger(name='AUTOMATA', filepath=log_path.joinpath('automata-cli.log'), stdout=debug, width=86)
###############################################################################
## MAIN PROCESSES
###############################################################################
def main():
    start_at = datetime.datetime.now()
    logger.info('Start executing at {}'.format(start_at))

    while True:
        try:
            config = read_configuration(config_path)
            # clear screen and print welcome messages
            import os
            os.system('cls')
            f = Figlet(font='banner3-D', width=500)
            print(f.renderText('AUTOMATA'))
            # print(sys.path)
            # print(root)

            print(circled_str(messages['welcome']))

            # check for configuration file
            # if not exists, recommend initial configuration
            # todo

            logger.info('Getting input from user...')
###############################################################################
            # select available masters
            masters = {(m.stem[:-6] if m.stem.endswith('Master') else m.stem): m for m in root.joinpath('depository/masters').glob('*.py')}
            q00 = [
                {
                    'type':     'list',
                    'name':     'master',
                    'message':  messages['q_master'],
                    'choices':  [m.capitalize() for m in masters.keys()] + ['Configuration']
                }
            ]
            m = prompt(q00)['master']
            if m.lower() == 'configuration':
                config = read_configuration(config_path)
                q01 = [
                    {
                        'type':     'checkbox',
                        'name':     'config_items',
                        'message':  messages['q_config'],
                        'choices':  [{'name': '{}: \t{}'.format(k, v)} for k, v in config.items()]
                    }
                ]
                a01 = [item.split(': \t') for item in  prompt(q01)['config_items']]
                if not a01: continue
                q011 = [
                    {
                        'type':     'input',
                        'name':     k,
                        'message':  '{} (current value: {}): '.format(k, v)
                    } for [k, v] in a01
                ]
                write_configuration(config_path, **prompt(q011))
                continue
            q02 = [
                {
                    'type':     'list',
                    'name':     'level',
                    'message':  messages['q_master_l'],
                    'choices':  [
                        messages['q_master_l1'],
                        messages['q_master_l2']
                    ]
                }
            ]
            l = prompt(q02)['level']
            l = l.startswith('simple') and 'Simple' or 'Advanced'
            module = importlib.import_module('Automata.depository.masters.{}Master'.format(m.lower()))
            Master = getattr(module, '{}{}Master'.format(m.capitalize(), l.capitalize()))
###############################################################################
            # looking for avaiable scripts online or in depository.
            q1 = [
                {
                    'type':     'list',
                    'name':     'script_src',
                    'message':  messages['q_ops'],
                    'choices':  [
                        messages['q_ops1'],
                        messages['q_ops2']
                    ]
                }
            ]
            a1 = prompt(q1)['script_src']
            if a1.startswith('online'):
                online = True
###############################################################################
            # select from options
            options = []
            if online:
                if not config.get('operation_sp_id'):
                    q21 = [
                        {
                            'type':     'input',
                            'name':     'ops_sp_id',
                            'message':  messages['q_ops_on_id'],
                            'validate': lambda val: val != '' or 'Invalid input!'
                        },
                        {
                            'type':     'input',
                            'name':     'ops_sheet_name',
                            'message':  messages['q_ops_on_name'],
                            'validate': lambda val: val != '' or 'Invalid input!'
                        }
                    ]
                    a21 = prompt(q21)
                    ops_sp_id = a21['ops_sp_id']
                    ops_sheet_name = a21['ops_sheet_name']
                else:
                    ops_sp_id = config.get('operation_sp_id')
                    ops_sheet_name = config.get('operation_ws_name')
                try:
                    ops_sp = get_spreadsheet(ops_sp_id)
                    df_depo = get_sheet_data(ops_sp.worksheet(ops_sheet_name))
                except:
                    logger.fatal('Error opening given sheet. Try again.')
                    break
                options = df_depo['name'].tolist()
            else:
                if not config.get('operation_path'):
                    q22 = [
                        {
                            'type':     'input',
                            'name':     'op_path',
                            'message':  messages['q_ops_off_path']
                        }
                    ]
                    depository_path = prompt(q22)['op_path']
                    if not depository_path:
                        tkroot = tk.Tk()
                        tkroot.withdraw()

                        depository_path = filedialog.askdirectory()
                        tkroot.destory()
                else:
                    depository_path = config.get('operation_path')
                available_scripts = [p for p in depository_path.glob('*.csv')]
                options = [f.stem for f in available_scripts]

            if not options:
                print('No available operations found. Try again with another sheet or folder.')
                break
###############################################################################
            q3 = [
                {
                    'type':     'list',
                    'name':     'op_choice',
                    'message':  messages['q_op_choice'],
                    'choices':  options + ['Exit']
                }
            ]
            a3 = prompt(q3)['op_choice']
            if a3 == 'Exit':
                logger.info('User terminated execution')
                break
            if online:
                op_sheet = ops_sp.worksheet(df_depo[df_depo['name'] == a3]['sheet_name'].iloc[0])
                df_op = get_sheet_data(op_sheet)
            else:
                # df_script = pd.read_csv(available_scripts[options.index(a2)], engine='python', encoding='utf-8')
                df_op = pd.read_csv(available_scripts[options.index(a3)], engine='python')
            df_op = df_op.set_index('#', drop=True)
###############################################################################
            # get data online or offline
            q4 = [
                {
                    'type':     'list',
                    'name':     'data_src',
                    'message':  messages['q_data'],
                    'choices':  [
                        messages['q_ops1'],
                        messages['q_ops2']
                    ]
                }
            ]
            a4 = prompt(q4)['data_src']
            if a4.startswith('online'):
                q51 = [
                    {
                        'type':     'input',
                        'name':     'data_sp_id',
                        'message':  messages['q_data_on_id'],
                        'validate': lambda val: val != '' or 'Invalid input!'
                    },
                    {
                        'type':     'input',
                        'name':     'data_sheet_name',
                        'message':  messages['q_data_on_name'],
                        'validate': lambda val: val != '' or 'Invalid input!'
                    }
                ]
                a51 = prompt(q51)
                data_sp_id = a51['data_sp_id']
                data_sheet_name = a51['data_sheet_name']
                try:
                    data_sp = get_spreadsheet(data_sp_id)
                    df_data = get_sheet_data(data_sp.worksheet(data_sheet_name))
                except:
                    logger.fatal('Error opening given sheet. Try again.')
                    break
            else:
                q52 = [
                    {
                        'type':     'input',
                        'name':     'data_path',
                        'message':  messages['q_data_off_path']
                    }
                ]
                data_path = prompt(q52)['data_path']
                if not data_path:
                    tkroot = tk.Tk()
                    tkroot.withdraw()

                    data_path = filedialog.askopenfilename()
                    tkroot.destory()
                df_data = pd.read_csv(data_path, engine='python')
###############################################################################
            print(circled_str('All information collected. Starting execution...'))
            logger.info('Starting processing...')
            # init master and queen
            master = Master(df_op, df_data)
            try:
                max_children = int(config.get('max_thread'))
            except:
                max_children = 5
            q = Queenb(max_children=max_children, logger=logger)
            q.add_child(Honeyb, flower='list', fetch_args=[df_data], rough_func=master.rough_func, work_func=master.work_func)
            q.add_children(Browserb, quit_on_error=False)
            
            q.start()
            q.join()

            results = []
            for result in q.results:
                r = result[2][0]
                r['result'] = result[3]
                results.append(r)
            df_result = pd.DataFrame(results)
            result_file = result_path.joinpath('{}_{}.csv'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'), a3))
            df_result.to_csv(result_file, index=False)
            logger.info('Results saved at {}'.format(result_file))
            break
        except (KeyboardInterrupt, KeyError):
            logger.info('User terminated execution')
            break

    end_at = datetime.datetime.now()
    logger.info('Time used: {}'.format(end_at - start_at))


if __name__ == '__main__':
    main()