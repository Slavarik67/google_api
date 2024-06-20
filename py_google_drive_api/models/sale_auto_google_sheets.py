from odoo import models, _, fields, api
import logging
import io
import os
from . import def_all


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.google_sheets_api_sale()
        return res

    def google_sheets_api_sale(self):
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

        for el in self:
            product = el.client_order_ref
            # Номер строки продукта в таблице
            if product in object:
                row_id = object[el.client_order_ref]
            else:
                errors_row.append(product)
                continue
            # Sale
            sale = el.name
            state_int = 'Не начато'
            price = el.amount_untaxed
            document = el.contract_id.name
            if not document:
                document = ''

            # Данные по закупкам
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            purchase_u = ''
            purchase_t = ''
            purchase_s = ''
            purchase = self.env['purchase.order'].search([('origin', 'ilike', sale)])
            for purch in purchase:
                if purch.order_line[0].product_id.categ_id.name == 'Техника':
                    purchase_t = base_url + '/web#id=' + str(purch.id) + '&view_type=form&model=purchase.order'
                elif purch.order_line[0].product_id.categ_id.name == 'Услуги по установке кухни':
                    purchase_u = base_url + '/web#id=' + str(purch.id) + '&view_type=form&model=purchase.order'
                elif purch.order_line[0].product_id.categ_id.name == 'WIP':
                    purchase_s = base_url + '/web#id=' + str(purch.id) + '&view_type=form&model=purchase.order'

            # Присвоение значений
            values_odoo = {'Заказ продажи': sale,
                           'Статус производства': state_int,
                           'Цена без ндс': price,
                           'ДОГОВОР': document,
                           'Заказ на закупку столешниц': purchase_s,
                           'Заказ на закупку техники': purchase_t,
                           'Заказ на закупку услуг': purchase_u}

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