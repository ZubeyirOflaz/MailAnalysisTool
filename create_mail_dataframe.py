import datetime
import email
import struct
import zipfile
from email.policy import default as default_p
from base64 import b64decode
import transliterate as trl
import codecs
from io import StringIO
from html.parser import HTMLParser
import logging

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


# This function gets a person field from an email  file and provides a structured string for further processing.
#
def get_person_info(email_str, include_name=True, transliterate=True):
    # Separate the multiple emails into a list
    if email_str:
        e_list = email_str.split(', ')
        final_string = ''
        for item in e_list:
            # Separate name from email
            str = item.replace('>', '')
            str_list = str.split(' <')
            if include_name:
                if transliterate:
                    try:
                        name_tra = trl.translit(str_list[0], reversed=True)
                        final_string += fr'{name_tra} ({str_list[0]}) <{str_list[1]}>'
                    except:
                        # print(fr"{str_list[0]} is causing an error, the name will not be transliterated")

                        final_string += item
                    # else:
                    #    final_string += fr'{str_list[0]} <{str_list[1]}>'
                else:
                    final_string += fr'{str_list[0]} <{str_list[1]}>'
            elif len(str_list) > 1:
                final_string += fr'{str_list[1]}'
            else:
                final_string += item
            final_string += '; '
        final_string = final_string[:-1]
    else:
        final_string = email_str
    return final_string


def extract_mail_elements(mail_dict, key_list):
    extracted_dict = {}
    for key in key_list:
        if mail_dict[key] is not None:
            extracted_dict[key] = mail_dict[key]
    return extracted_dict


def get_attachments(file_name, file_list):
    file_name = file_name[:-4]
    attachment_list = [s for s in file_list if s.startswith(file_name) and not s.endswith('eml')]
    if len(attachment_list) > 0:
        attachments = '; '.join(attachment_list)
    else:
        return None
    return attachments


def parse_thread_index(index):
    s = codecs.decode(index, 'base64')

    guid = struct.unpack('>IHHQ', s[6:22])
    guid = '{%08X-%04X-%04X-%04X-%12X}' % (
        guid[0], guid[1], guid[2], (guid[3] >> 48) & 0xFFFF, guid[3] & 0xFFFFFFFFFFFF)

    f = struct.unpack(b'>Q', s[:6] + b'\0\0')[0]
    return guid


def get_eml_dataset(zip_file, include_email_body=True, additional_fields=[],
                    include_names=True, transliterate_names=True):
    zip = zipfile.ZipFile(zip_file)
    files = zip.namelist()
    files.sort()
    mail_list = []
    for file in files:
        mail_dict = {}
        if file.endswith('eml'):
            # print(file)
            e_mail = (zip.open(file))
            mail_data = email.parser.BytesParser(policy=default_p).parse(e_mail)
            mail_dict['origin_person'] = file.split('/')[0]
            mail_dict['file_name'] = file.split('/')[1]
            fields_to_include = ['Subject', 'Thread-Index', 'Date']
            mail_dict.update(extract_mail_elements(mail_data, fields_to_include))
            if mail_data['Received']:
                mail_dict['Received'] = mail_data['Received'].split('; ')[-1]
            if mail_data['Thread-Index']:
                mail_dict['Thread GUID'] = parse_thread_index(bytes(str(mail_data['Thread-Index']), 'utf-8'))
            mail_dict['From'] = get_person_info(mail_data['From'], include_name=include_names,
                                                transliterate=transliterate_names)
            mail_dict['To'] = get_person_info(mail_data['To'], include_name=include_names,
                                              transliterate=transliterate_names)
            if mail_data['Cc'] is not None:
                mail_dict['Cc'] = get_person_info(mail_data['Cc'], include_name=include_names,
                                                  transliterate=transliterate_names)
            attachments = get_attachments(file, files)
            if attachments is not None:
                mail_dict['Attachments'] = attachments
            if include_email_body:  # and mail_data['body'] is not None:
                try:
                    mail_dict['body'] = mail_data.get_body(preferencelist=('plain')).get_content()
                except:
                    try:
                        logging.debug(f'The content of the body for {file} cannot be extracted as plain text, '
                                      f'importing it as html instead')
                        mail_dict['body'] = mail_data.get_body(preferencelist=('html', 'plain')).get_content()
                    except AttributeError:
                        logging.debug(f'Mail body attribute error')
                    except:
                        logging.error(f'Error at trying to extract {file} body that cannot be handled')
        if mail_dict != {}:
            mail_list.append(mail_dict)
    return mail_list
