from odoo import models, _, fields, api
import logging
import io
import os
from . import def_all


class GoogleSheetsApi(models.Model):
    _inherit = 'picking.transport.info'

    def google_sheets_api_action(self):
        # Для регистрации
        service = def_all.authenticate(self)
        sheet = service.spreadsheets()
        sheet_id = self.env['ir.config_parameter'].sudo().search([('key', '=', 'TableNameId')]).value

        # Быстрые данные
        list = 'КопиДан'
        list_setting = self.env['ir.config_parameter'].sudo().search([('key', '=', 'ListTable')])
        errors_row = []
        object = def_all.list_update(sheet, sheet_id, list_setting)
        list_setting = eval(list_setting.value)

        transport = self.name
        number_pl = self.picking_seal_number
        if not number_pl:
            number_pl = ''
        transport_number = self.vehicle_id.name
        date = self.transport_date
        if not transport_number:
            transport_number = ''
        for el in self.delivery_ids:
            box = int(el.dlinbox_count)
            product = el.client_order_ref
            # Номер строки продукта в таблице
            if product in object:
                row_id = object[el.client_order_ref]
            else:
                errors_row.append(product)
                continue

            # Поиск пакетов
            pack = ''
            picking_done = self.env['stock.picking'].search([
                ('origin', '=', el.sale_id.name),
                ('state', '=', 'done'),
                ('picking_type_id.sequence_code', '=', 'INT'),
            ])
            picking_assigned = self.env['stock.picking'].search([
                ('origin', '=', el.sale_id.name),
                ('state', '=', 'assigned'),
                ('picking_type_id.sequence_code', '=', 'INT'),
            ])
            if picking_done:
                state_int = 'Завершено'
                for done in picking_done:
                    for elem in done.move_line_ids_without_package:
                        if elem.result_package_id.name == False or elem.result_package_id.name in pack:
                            continue
                        else:
                            if pack == '':
                                pack = elem.result_package_id.name
                            else:
                                pack = pack + ', ' + elem.result_package_id.name
            elif picking_assigned:
                state_int = 'Ожидани компонентов'
                for assigned in picking_assigned:
                    for elem in assigned.move_line_ids_without_package:
                        if elem.result_package_id.name == False or elem.result_package_id.name in pack:
                            continue
                        else:
                            if pack == '':
                                pack = elem.result_package_id.name
                            else:
                                pack = pack + ', ' + elem.result_package_id.name
            else:
                state_int = 'Не начато'

            # Присвоение значений
            values_odoo = {'Номер машины под отгрузку': transport,
                           'Номер машины': transport_number,
                           'Дата отгрузки': str(date),
                           'Статус производства': state_int,
                           'Упаковка': pack,
                           'Номер пломбы': number_pl,
                           'Кол-во коробок': str(box)
                           }
            # logging.info(f'slavik | {values_odoo["Кол-во коробок"]}')
            spisok = []
            for el in values_odoo:
                slovar = {}
                if not el in list_setting:
                    continue
                slovar["range"] = list + '!' + list_setting[el] + str(row_id)
                slovar["values"] = [[values_odoo[el]]]
                spisok.append(slovar)

            batch_request_body = {
                'value_input_option': 'RAW',
                "data": [spisok]
            }
            # logging.info(f'slavik | batch_request_body {batch_request_body}')
            resp = service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body=batch_request_body
            ).execute()

        if errors_row:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'type': 'danger',
                    'message': f'Не найден подходящий продукт: {errors_row}',
                }
            }
            return notification