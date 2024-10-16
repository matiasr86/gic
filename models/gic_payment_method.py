from odoo import models, fields, api

# Extendiendo el modelo Forma de Pago (POS)
class GicPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    way_id = fields.Many2one('gic.way', string='Medio de Cobro')
    payment_plan_id = fields.Many2one('gic.payment.plan', string='Plan de Pago')


