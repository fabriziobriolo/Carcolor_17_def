from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import formatLang, get_lang
from itertools import chain


class ProductPriceListItem(models.Model):
    _inherit = 'product.pricelist.item'
    _order = "sequence, applied_on, min_quantity desc, categ_id desc, id desc"


    applied_on = fields.Selection(
        selection_add=[('4_product_brand', "Product brand"),
            ('5_product_model', "Product model"),
            ('6_product_brand_category', "Product Brand and Category")], 
            ondelete={
                '4_product_brand': 'set default', 
                '5_product_model':'set default',
                '6_product_brand_category':'set default'
                })
    product_brand_id = fields.Many2one(
        'product.brand', 'Product brand', ondelete='cascade', required=False)
    product_model_id = fields.Many2one(
        'product.model', 'Product model', ondelete='cascade')
    product_brand_category_id = fields.Many2one(
        'product.category',
        'Product category of selected Brand',
        ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    def _check_product_consistency(self):
        super()._check_product_consistency()
        for item in self:
            if (item.applied_on == "4_product_brand" and not
                    item.product_brand_id):
                raise ValidationError(
                    _("Please specify the brand for which this rule should be applied"))
            elif (item.applied_on == "5_product_model" and not
                    item.product_model_id):
                raise ValidationError(
                    _("Please specify the model for which this rule should be applied"))
    
    def _compute_name_and_price(self):
        super()._compute_name_and_price()
        for item in self:
            match = False
            if item.applied_on == "4_product_brand" and item.product_brand_id:
                match = True
                item.name = _("Brand: %s", item.product_brand_id.display_name)
            elif item.applied_on == "5_product_model" and item.product_model_id:
                match = True
                item.name = _("Model: %s", item.product_model_id.display_name)
            elif (item.applied_on == "6_product_brand_category" and
                    item.product_brand_category_id):
                match = True
                item.name = _(
                    "Brand and Category: %s - %s" %
                    (
                        item.product_brand_id.display_name,
                        item.product_brand_category_id.display_name
                    )
                )

            if match:
                if item.compute_price == 'fixed':
                    item.price = formatLang(
                        item.env,
                        item.fixed_price,
                        monetary=True,
                        dp="Product Price",
                        currency_obj=item.currency_id)
                elif item.compute_price == 'percentage':
                    item.price = _("%s %% discount", item.percent_price)
                else:
                    item.price = _(
                        "%(percentage)s %% discount and %(price)s surcharge",
                        percentage=item.price_discount,
                        price=item.price_surcharge)

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_applicable_rules(self, products, date, **kwargs):
        self and self.ensure_one()
        if not self:
            return self.env['product.pricelist.item']

        brand = products.product_brand_id
        model = products.product_model_id
        categ = products.categ_id

        domain = [
            '&',
            ('applied_on', 'in', [
                '4_product_brand', '5_product_model', '6_product_brand_category']),
            ('pricelist_id', '=', self.id),
            '|', ('product_model_id', 'in', model.ids),
            '|', ('product_brand_id', 'in', brand.ids),
            '|', ('product_brand_category_id', 'parent_of', categ.ids), ('product_brand_id', 'in', brand.ids),
            '|', ('date_start', '=', False), ('date_start', '<=', date),
            '|', ('date_end', '=', False), ('date_end', '>=', date),
        ]
        rules = self.env['product.pricelist.item'].with_context(
            with_company=self.company_id.id, active_test=False).search(
                domain)
        if rules:
            return rules
        else:
            return self.env['product.pricelist.item'].with_context(active_test=False).search(
            self._get_applicable_rules_domain(products=products, date=date, **kwargs)
        ).with_context(self.env.context)
