from odoo import models, _, fields, api
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from bs4 import BeautifulSoup
from datetime import date, datetime
from . import def_all
import requests
import pandas as pd
import io
import os
import math
import logging


class GoogleDriveApi(models.Model):
    _inherit = 'mrp.bom'

    def authenticate(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        # SERVICE_ACCOUNT_FILE = '/odoo/custom/odoo_eurodesign/py_google_drive_api/static/json/service_account.json' # TEST
        # SERVICE_ACCOUNT_FILE = '/home/odooadmin/custom/odoo_eurodesign/py_google_drive_api/static/json/service_account.json'
        SERVICE_ACCOUNT_FILE = self.env['ir.config_parameter'].sudo().search([('key', '=', 'AddressGoogleJson')]).value
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds

    def google_drive_api_action(self, bool=True):
        # Синхр. с google drive
        creds = self.authenticate()
        service = build('drive', 'v3', credentials=creds)
        # pute_finish = '1rx4bO21EqeUoBPwXU1HSUS2TjP7kriWt'
        # pute = '1sNUy61dLFu5cEcI2Wrg-vkcje62SXF6v'
        if bool:
            pute = '1Trs_4FOaXyIT50AQsGKB4wRbDF9OpoDE'
        else:
            pute = '1KuNhivvhe0Xgti3vhxOI_AztsveA7J5P'
        pute_finish = '1CZm4x22WpTuC_h2_DU3siaRyKOYP9lpt'
        query = f'parents = "{pute}"'
        response = service.files().list(q=query).execute()
        files = response.get('files')

        # Переменные
        list_create = [] # Список словарей для создания BOM
        list_info = [] # Список возникших проблем
        list_upgrade = [] # спискок переносимых файлов

        # Цикл прохождения по файлам
        for file in files:
            kitchen = self.download_file_from_drive(file['id'], service, file['name'], bool)

            #Проверки
            if type(kitchen) == type({}):
                list_create.append(kitchen)
                list_upgrade.append(file['id'])
            else:
                list_info.append(kitchen)

        try:
            self.env.cr.execute('BEGIN')
            self._table_info(list_info)
            ref = self.env['mrp.bom'].create(list_create)
            self.env.cr.execute('COMMIT')
            self._message_table(len(list_upgrade))
            for ids in list_upgrade:
            # if el['mimeType'] != 'application/vnd.google-apps.folder':
                service.files().update(fileId=ids, addParents=pute_finish, removeParents=pute).execute()
        except Exception as e:
            self.env.cr.execute('ROLLBACK')
            raise e

    def _message_table(self, col):
        service = def_all.authenticate(self)
        table_info = '10xN4OsTgkqJCjEs0b2Dafp1iwnoZKo5liLRgijRmemw'
        sheet = service.spreadsheets()
        chek = sheet.values().get(spreadsheetId=table_info, range=f'Отчет загрузок!A:A').execute()
        logging.info(f'slavik | {chek}')
        slovar = {}
        slovar['values'] = [[f"{datetime.today().strftime('%d.%m.%Y %H:%M:%S')} было загружено {col} ведомостей."]]
        slovar['range'] = f'Отчет загрузок!A{len(chek["values"])+1}'

        batch_request_body = {
            'value_input_option': 'RAW',
            "data": [[slovar]]
        }
        resp = service.spreadsheets().values().batchUpdate(
            spreadsheetId=table_info,
            body=batch_request_body
        ).execute()

    def _table_info(self, list_info):
        service = def_all.authenticate(self)
        table_info = '10xN4OsTgkqJCjEs0b2Dafp1iwnoZKo5liLRgijRmemw'
        sheet = service.spreadsheets()
        table = sheet.values().clear(spreadsheetId=table_info, range=f'Загрузка BOM!A2:B1000').execute()
        slovar = {}
        slovar['values'] = list_info
        slovar['range'] = 'Загрузка BOM!A2'

        batch_request_body = {
            'value_input_option': 'RAW',
            "data": [[slovar]]
        }
        resp = service.spreadsheets().values().batchUpdate(
            spreadsheetId=table_info,
            body=batch_request_body
        ).execute()

    def download_file_from_drive(self, file_id, service, file_name, bool):
        # Преобразование данных для считывания
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_excel(fh)

        # Переменные
        list_work = []

        # Обработка данных
        ## Поиск айдишника продукта
        df['Продукт'] = df['Продукт'].fillna('')
        # if math.isnan(df.iloc[0, 0]):
        #     return [file_name, f'Продукт пуст'] # Вывод названия и описания проблемы ( Пуйтой продукт )
        name = self.env['product.template'].search([('name', '=', df.iloc[0, 0])]).id
        if not name:
            return [file_name, f'Продукт ({df.iloc[0, 0]}) не найдет']  # Вывод названия и описания проблемы ( Не нашел такой продукт )

        ## Поиск компонентов
        for el in range(len(df)):
            product_product = self.env['product.product'].search([('default_code', '=', df.iloc[el, 1])]).id
            if not product_product:
                product_product = self.env['product.product'].search([('default_code', '=', str(df.iloc[el, 1])[1:-1])]).id
                if not product_product:
                    return [file_name, f'Компонент ({df.iloc[el, 1]}) не найдет']  # Вывод названия и описания проблемы ( Не нашел такой компонент)
            list_work.append((0, 0, {
                'product_id': product_product,
                'product_qty': df.iloc[el, 3],
                'product_uom_id': self.env['uom.uom'].search([('name', '=', df.iloc[el, 4])]).id}))

        ## Поиск типа продукта
        type = df.iloc[0, 5]
        if type == 'Комплект':
            type = 'phantom'
        elif type == 'Производство этого продукта':
            type = 'normal'
        else:
            type = 'subcontract'

        # Присвоение данных и их отправка
        record = {'product_tmpl_id': name, 'type': type, 'bom_line_ids': list_work, 'state': 'approved'}
        if not bool:
            record['code'] = 'Типовая спецификация от ' + date.today().strftime('%d.%m.%Y')
        return record









