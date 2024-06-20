from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2

def authenticate(self):
    addres = self.env['ir.config_parameter'].sudo().search([('key', '=', 'AddressGoogleJson')]).value
    # addres = "/odoo/custom/odoo_eurodesign/py_google_drive_api/static/json/service_account.json"  # TEST
    # addres = '/home/odooadmin/custom/odoo_eurodesign/py_google_drive_api/static/json/service_account.json'
    # creds_json = os.path.dirname(__file__) + "/service_account.json"
    # creds_json = addres
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(addres, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


def list_update(sheet, sheet_id, list_setting):
    alf = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M',
           14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y',
           26: 'Z', 27: 'AA', 28: 'AB', 29: 'AC', 30: 'AD', 31: 'AE', 32: 'AF', 33: 'AG', 34: 'AH', 35: 'AI', 36: 'AJ',
           37: 'AK', 38: 'AL', 39: 'AM', 40: 'AN', 41: 'AO', 42: 'AP', 43: 'AQ', 44: 'AR', 45: 'AS', 46: 'AT', 47: 'AU',
           48: 'AV', 49: 'AW', 50: 'AX', 51: 'AY', 52: 'AZ'}

    row = 'D'
    resp1 = sheet.values().get(spreadsheetId=sheet_id, range='КопиДан!1:1').execute()
    if 'values' in resp1:
        for el in resp1['values']:
            listok = {}
            for i in range(len(resp1['values'][0])):
                if el[i] == 'Код объекта':
                    row = alf[i + 1]
                elif el[i] == 'Заказ продажи':
                    listok['Заказ продажи'] = alf[i + 1]
                elif el[i] == 'Статус производства':
                    listok['Статус производства'] = alf[i + 1]
                elif el[i] == 'ДОГОВОР':
                    listok['ДОГОВОР'] = alf[i + 1]
                elif el[i] == 'Заказ на закупку техники':
                    listok['Заказ на закупку техники'] = alf[i + 1]
                elif el[i] == 'Заказ на закупку услуг':
                    listok['Заказ на закупку услуг'] = alf[i + 1]
                elif el[i] == 'Заказ на закупку столешниц':
                    listok['Заказ на закупку столешниц'] = alf[i + 1]
                elif el[i] == 'Цена без ндс':
                    listok['Цена без ндс'] = alf[i + 1]
                elif el[i] == 'Номер машины под отгрузку':
                    listok['Номер машины под отгрузку'] = alf[i + 1]
                elif el[i] == 'Номер машины':
                    listok['Номер машины'] = alf[i + 1]
                elif el[i] == 'Дата отгрузки':
                    listok['Дата отгрузки'] = alf[i + 1]
                elif el[i] == 'Упаковка':
                    listok['Упаковка'] = alf[i + 1]
                elif el[i] == 'Номер пломбы':
                    listok['Номер пломбы'] = alf[i + 1]
                elif el[i] == 'Кол-во коробок':
                    listok['Кол-во коробок'] = alf[i + 1]
        list_setting.value = str(listok)

        resp2 = sheet.values().get(spreadsheetId=sheet_id, range=f'КопиДан!{row}:{row}').execute()
        object = {}
        if 'values' in resp2:
            for i in range(len(resp2['values'])):
                if resp2['values'][i] == []:
                    continue
                object[resp2['values'][i][0]] = i + 1
        return object
    else:
        return False