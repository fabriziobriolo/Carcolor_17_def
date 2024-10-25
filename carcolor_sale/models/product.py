from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Brand of product'

    name = fields.Char('Brand name', required=True)
    notes = fields.Text('Notes')
    product_ids = fields.One2many(
        'product.template', 'product_brand_id', readonly=True)
    pricelist_items_ids = fields.One2many(
        'product.pricelist.item', 'product_brand_id')
    product_model_ids = fields.One2many(
        'product.model', 'product_brand_id')


class ProductModel(models.Model):
    _name = 'product.model'
    _description = 'Model of product'

    name = fields.Char('Model name', required=True)
    notes = fields.Text('Notes')
    product_ids = fields.One2many(
        'product.template', 'product_model_id')
    pricelist_items_ids = fields.One2many(
        'product.pricelist.item', 'product_model_id')
    product_brand_id = fields.Many2one(
        'product.brand',
        string='Product Brand',
        ondelete='cascade',
        required=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Product Brand',
        ondelete='set null')
    product_model_id = fields.Many2one(
        'product.model',
        string='Product Model',
        ondelete='set null')