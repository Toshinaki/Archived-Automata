import sys, json
from pathlib import Path
root = Path(__file__).absolute().parent.parent.parent
if not str(root.parent) in sys.path:
    sys.path.append(str(root.parent))

import pandas as pd

from Automata.core.MillenniumFalcon import gss
from Automata.core.helpers import try_n, read_configuration
# google account info
config_path = root.joinpath('data/config.json')
config = read_configuration(config_path)
account_name = config.get('google_account_name')

# google's popup menu for selection
special_selects = [
    '//div[contains(@id, "lineItemTypePriority-lstLineItemTypes")]',
    '//div[contains(@id, "lineItemType-startDateBox")]',

]

class AdmanagerSimpleMaster:

    '''Read operation steps and information from sheets, then execute.'''

    def __init__(self, df_op, df_data, end_flags=['o', 'x'], *args, **kwargs):
        self.df_op = df_op
        self.df_data = df_data
        self.end_flags = end_flags
    
    def rough_func(self, df, *args, **kwargs):
        '''`rough_func` can be created as many as possible when a specific mission requests it.'''
        new_df = pd.DataFrame(columns=['raw'])
        new_df['raw'] = df.to_dict('records')
        return new_df
    
    def work_func(self, raw, driver, *args, **kwargs):
        '''`work_fun` can be created as many as possible for different missions.'''
        max_run_times = 3
        run_times = 1

        curr_step_num = 0
        failed = False
        error = ''
        while True:
            # last execution failed, run again
            if failed:
                # run time excessed, some error must happened, return that error
                if run_times >= max_run_times:
                    return error
                run_times += 1
                curr_step_num = 0
                failed = False
                error = ''
            # read one row
            curr_step = self.df_op.iloc[curr_step_num]
            # parse row content
            service, dim, page, item, xpath, data, nxt = curr_step
            if nxt in self.end_flags: # end flags
                return nxt
            # select needed information from raw
            nxt_dim, nxt_page, nxt_item, input_ = data.format(**raw).split(',', 3)
            
            if not input_.startswith('SKIP'):
                input_ = input_.split('#!#')
                # current step opens an url; if {}, insert input_ into it
                if 'url' in item:
                    url, checker = xpath.split('###', 1)
                    url = url.format(*input_)
                    if driver.getsu(url) == False:
                        failed = True
                        error = 'error at step {}. Cannot open given url ({})'.format(curr_step_num, url)
                        continue
                    # checking for account selection
                    if account_name:
                        account_xpath = '//*[@id="profileIdentifier"][contains(text(), "{}")]'.format(account_name)
                    else:
                        account_xpath = '//*[@id="profileIdentifier"][1]'
                    branch = driver.find_branch({'select_account': account_xpath, 'search_box': '//global-search[@role="search"]'})
                    if branch == 'select_account':
                        driver.xpath_exists(account_xpath).click()
                    
                    if not driver.wait_xpath(checker):
                        failed = True
                        error = 'error at step {}. Cannot find element {} at given url ({})'.format(curr_step_num, checker, url)
                        continue


                # current step searchs for an element; input input_ into it
                else:
                    n_format = xpath.count('{}')
                    if n_format:
                        xpath = xpath.format(input_[:n_format])
                        input_ = input_[n_format:]
                    for i in input_:
                        if not try_n(3, driver.fill_form_item, 0.5, xpath, i):
                            print(try_n(3, driver.fill_form_item, 0.5, xpath, i))
                            print('error {};{}.'.format(xpath, i))
                            print(driver.fill_form_item(xpath, i))
                            print(type(i))
                            failed = True
                            error = 'error at step {}. no element {}'.format(curr_step_num, xpath)
                            continue
                    # if xpath in special_selects: # google's special selects containing input box for filtering
                    #     if not try_n(3, driver.fill_form_item, 0.5, xpath, input_):
                    #         print('error {};{}.'.format(xpath, input_))
                    #         print(type(input_))
                    #         failed = True
                    #         error = 'error at step {}. no element {}'.format(curr_step_num, xpath)
                    #         continue
                    #     # check if input box available
                    #     input_boxes = driver.find_displayed_xpath(xpath+'//input')
                    #     # if input boxes exist, count number of it and split input_data
                    #     if input_boxes:
                    #         for i in range(len(input_boxes)):
                    #             temp_input = xpath+'//input[{}]'.format(i+1)
                    #             if not try_n(3, driver.fill_form_item, 0.5, temp_input, input_[i]):
                    #                 print('error {};{}.'.format(temp_input, input_[i]))
                    #                 print(type(input_[i]))
                    #                 failed = True
                    #                 error = 'error at step {}. no element {}'.format(curr_step_num, temp_input)
                    #                 continue
                    #     else:
                    #         item_xpath = '''//div[@class="popupContent"]//*[contains(text(), "{}")]'''.format(input_)
                    #         if not try_n(3, driver.fill_form_item, 0.5, item_xpath, 'CLICK'):
                    #             print('error {};{}.'.format(xpath, input_))
                    #             print(type(input_))
                    #             failed = True
                    #             error = 'error at step {}. no element {}'.format(curr_step_num, item_xpath)
                    #             continue
                    # else:
                    #     if not try_n(3, driver.fill_form_item, 0.5, xpath, input_):
                    #         print(try_n(3, driver.fill_form_item, 0.5, xpath, input_))
                    #         print(driver.fill_form_item(xpath, input_))
                    #         print('error {};{}.'.format(xpath, input_))
                    #         print(type(input_))
                    #         failed = True
                    #         error = 'error at step {}. no element {}'.format(curr_step_num, xpath)
                    #         continue
            
            # read next step(s)
            nxt = json.loads(nxt)
            # only one integer, go to it
            if isinstance(nxt, int):
                curr_step_num = nxt
            # a list
            elif isinstance(nxt, list):
                # get every row in the list
                nxts = {n: self.df_op.iloc[n] for n in nxt}
                # select most match row from "dim" and "item"
                which = sorted([(n, len(set(r[1:4]) & set([nxt_dim, nxt_page, nxt_item]))) for n, r in nxts.items()], key=lambda x:x[1], reverse=True)[0]
                if which[1]:
                    curr_step_num = which[0]
                # nothing match, find xpath that appears
                else:
                    curr_step_num = driver.find_branch({n: self.df_op.iloc[n]['xpath'] for n in nxt})
                    if not curr_step_num:
                        failed = True
                        error = 'error at step {}. no element {}'.format(curr_step_num, ', '.join([self.df_op.iloc[n]['xpath'] for n in nxt]))
                        continue
            else:
                return 'error at step {}. Valid "next" item is number or a list of numbers.'.format(curr_step_num)



class AdmanagerAdvancedMaster:

    '''All methods and properties and custom. Nothing pre-made'''

    def __init__(self):
        pass
    
    def rough_func(self, *args):
        pass
    
    def work_fun(self, *args):
        pass