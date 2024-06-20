from odoo import models, _, fields, api
import logging
import requests
from bs4 import BeautifulSoup
# from datetime import datetime, date
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import pandas as pd
from datetime import date
import io
import os


class GoogleDriveApi(models.Model):
    _inherit = 'sale.order'

    def authenticate(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        # SERVICE_ACCOUNT_FILE = '/odoo/custom/odoo_eurodesign/py_google_drive_api/static/json/service_account.json' # TEST
        # SERVICE_ACCOUNT_FILE = '/home/odooadmin/custom/odoo_eurodesign/py_google_drive_api/static/json/service_account.json'
        SERVICE_ACCOUNT_FILE = self.env['ir.config_parameter'].sudo().search([('key', '=', 'AddressGoogleJson')]).value
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds

    def google_test(self):
        creds = self.authenticate()
        service = build('drive', 'v3', credentials=creds)\

        file_metadata = {
            'name': 'Название_файла.xlsx',
            'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'parents': ['1sNUy61dLFu5cEcI2Wrg-vkcje62SXF6v'],
            'data': "123wef"
        }

        file = service.files().create(body=file_metadata).execute()

        # file_id = file.get('id')
        # data = "123wef"
        #
        # # Отправка запроса на обновление содержимого файла
        # update_request = service.files().update(media_body=data, fileId=file_id).execute()