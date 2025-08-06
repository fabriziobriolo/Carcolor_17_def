# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestInvoiceReport(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'street': 'Via Test 123',
            'zip': '12345',
            'city': 'Milano',
            'state_id': cls.env['res.country.state'].search([
                ('code', '=', 'MI'),
                ('country_id.code', '=', 'IT')
            ], limit=1).id,
            'vat': 'IT12345678901',
            'l10n_it_codice_fiscale': 'TSTCST80A01F205X',
            'is_company': True,
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'default_code': 'TEST001',
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'list_price': 100.0,
        })
        
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'quantity': 2,
                'price_unit': 100.0,
            })],
        })
        cls.invoice._post()
        
    def test_invoice_report_data_structure(self):
        """Test che la struttura dati JSON per Carbone sia corretta"""
        report = self.env.ref('account.account_invoices')
        
        # Simula la generazione dei dati JSON
        import ast
        json_data = ast.literal_eval(report.carbone_json_data.replace('object', 'self.invoice'))
        
        # Verifica la struttura principale (nota: il nodo 'd' è implicito in Carbone)
        self.assertIn('company', json_data)
        self.assertIn('partner', json_data)
        self.assertIn('lines', json_data)
        self.assertIn('number', json_data)
        self.assertIn('date', json_data)
        self.assertIn('bank', json_data)
        self.assertIn('iban', json_data)
        self.assertIn('payment_terms', json_data)
        
        # Verifica i dati principali
        self.assertEqual(json_data['number'], self.invoice.name)
        
        # Verifica i dati del company
        company_data = json_data['company']
        self.assertEqual(company_data['name'], self.invoice.company_id.name)
        self.assertTrue(company_data['vat'])
        
        # Verifica i dati del partner
        partner_data = json_data['partner']
        self.assertEqual(partner_data['name'], self.partner.name)
        self.assertEqual(partner_data['vat'], 'IT12345678901')
        self.assertEqual(partner_data['cf'], 'TSTCST80A01F205X')
        
        # Verifica le linee
        lines = json_data['lines']
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['product']['code'], 'TEST001')
        self.assertEqual(lines[0]['product']['qty'], 2)
