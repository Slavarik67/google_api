from odoo import models, _, fields, api
import logging
import io
import os
from . import def_all
import time
import ast


class SaleOrdered(models.Model):
    _inherit = 'sale.order'

    def create_sale_product(self):
        # Для регистрации
        service = def_all.authenticate(self)
        sheet = service.spreadsheets()
        sheet_id = self.env['ir.config_parameter'].sudo().search([('key', '=', 'TableNameId')]).value

        resp1 = sheet.values().get(spreadsheetId=sheet_id, range='КопиДан!D:D').execute()['values'][1:]

        slov = {}
        list = []
        list2 = []
        count = 1
        for el in resp1:
            slov["".join(el)] = count
            list.append("".join(el))
            count +=1
        element = self.env['product.template'].search([('name', 'in', list)])
        for elem in element:
            list2.append(elem.name)
        res = set(list) - set(list2)

        list = []
        list2 = []
        count = 0
        for re in res:
            list2.append(re)
            list.append({
                'name': re,
                'categ_id': 150,
                'type': 'product',
                'default_code': f'SKF-{slov[re]}-{re.split("-")[-1]}',
                'barcode': f'19116{slov[re]}{re.split("-")[-1]}',
                'multiplicity_on_pallet': 1
            })
            count += 1
            if count == 1000:
                break
        self.env['product.template'].create(list)
        system_param = self.env['ir.config_parameter'].sudo().search([('key', '=', 'CreateProduct')])
        system_param.value = str(list2)

    def sale_create_pr(self):
        sale = []
        elements = self.env['ir.config_parameter'].sudo().search([('key', '=', 'CreateProduct')])
        if not elements:
            return
        elements_ls = ast.literal_eval(elements.value)
        for el in elements_ls:
            sale.append({
                    'partner_id': 3, #?
                    'order_line': [(0, 0, {'product_id': self.env['product.product'].search([('name', '=', el)]).id,
                                           'product_uom': 2, 'product_uom_qty': 1})],
                    'client_order_ref': el,
                    'warehouse_id': 8
                })
        elements.value = ''
        sale_order = self.env['sale.order'].sudo().create(sale)


