import pandas as pd
import create_mail_dataframe as crd
from os import listdir
import translation_module as tm
import datetime as dt
import network_visualizer as nv



def create_email_master(file_dir, file_name, include_body = False, include_names = True, transliterate = True):
    file_list = listdir(file_dir)
    email_list = []
    for index, file in enumerate(file_list):
        if file.endswith('.zip'):
            print(file)
            directory = fr"{file_dir}\{file}"
            email_list.append(crd.get_eml_dataset(directory,
                                                  include_email_body=include_body,
                                                  include_names=include_names,
                                                  transliterate_names=transliterate))
    email_list = sum(email_list, [])
    df = pd.DataFrame(email_list)
    df.to_csv(file_name, index = False)
    return None


#create_email_master(transneft_loc, 'transneft_named.csv')

def create_correspondence_history(pandas_df_master):
    to_dataframe = pandas_df_master[['Date', 'From', 'To']].copy(deep=True)
    to_dataframe['To'] = to_dataframe['To'].str.split('; ')
    to_dataframe = to_dataframe.explode('To').reset_index(drop=True)
    cc_dataframe = pandas_df_master[['Date', 'From', 'Cc']].copy(deep=True)
    cc_dataframe['Cc'] = cc_dataframe['Cc'].str.split('; ')
    cc_dataframe = cc_dataframe.explode('Cc').reset_index(drop=True)
    to_dataframe.rename(columns={'From': 'Sender', 'To': 'Recipient'}, inplace=True)
    cc_dataframe.rename(columns={'From': 'Sender', 'Cc': 'Recipient'}, inplace=True)
    final_df = pd.concat([to_dataframe, cc_dataframe], ignore_index=True)
    final_df['Recipient'] = final_df['Recipient'].str.replace(';', '')
    return final_df

# test2 = create_correspondence_history(test_df)
def filter_mails (df, from_date = None, to_date = None, Sender = None,Recipient = None):
    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    if from_date is not None:
        df = df[df['Date'] > from_date]
    if to_date is not None:
        df = df[df['Date'] < to_date]
    if Sender is not None:
        df = df[df['From'].str.contains(rf'{Sender}', na = False)]
    if Recipient is not None:
        mask = ((df['To'].str.contains(rf'{Recipient}', na = False)) |
                (df['Cc'].str.contains(rf'{Recipient}', na = False)))
        df = df[mask]
    return df