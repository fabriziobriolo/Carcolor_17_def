import json
import io
import requests
from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = "stock.location"

    is_modula = fields.Boolean(string="Modula")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    modula_sync = fields.Boolean(string="Sync Modula")
    modula_result = fields.Text(string="Modula Result")

    @api.depends('move_ids_without_package')
    def _compute_modula(self):
        for rec in self:
            modula = False
            for line in rec.move_line_ids_without_package:
                if (line.location_id.is_modula or
                        line.location_dest_id.is_modula):
                    modula = True
                    break
            rec.modula = modula

    modula = fields.Boolean(
        string="Modula", compute="_compute_modula")
    
    def sync_modula(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'modula_sync_action',
            'target': 'new',
        }

    def sync_modula_old(self):
        source = self.location_id
        destination = self.location_dest_id
        json_data = {}
        json_data['picking'] = self.name
        json_data['scheduled_date'] = fields.Datetime.to_string(
            self.scheduled_date)
        json_data['effective_date'] = fields.Datetime.to_string(
            self.date_done)
        json_data['partner'] = self.partner_id.name
        json_data['operation'] = self.picking_type_id.code
        json_data['lines'] = []
        for line in self.move_ids_without_package:
            line_data = {}
            line_data['id'] = line.id
            line_data['source'] = source.barcode or source.name
            line_data['destination'] = destination.barcode or destination.name
            line_data['product_code'] = line.product_id.default_code
            line_data['product_name'] = line.product_id.name
            line_data['quantity_ordered'] = line.product_uom_qty
            #line_data['quantity_done'] = line.quantity
            json_data['lines'].append(line_data)

        modula_url = self.env[
            'ir.config_parameter'
            ].sudo().get_param(
                'modula_url',
                'http://pinotivede.addns.org:5000/apis/modulaupload'
               )

        files = {'filesUP': io.StringIO(json.dumps(json_data))}

        response = requests.put(
            modula_url,
            files=files)
        
        if response.content:
            json_data = json.loads(response.content)
            if json_data['result'] == 1:
                for line in json_data['lines']:
                    self.move_ids_without_package.browse(
                        line['id']).quantity_done = line['quantity_done']
                self.modula_sync = True
            else:
                self.modula_result = json_data['message']

        print(json.dumps(json_data))