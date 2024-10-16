from odoo import models, fields, api

# Modelo Plan de Pago
class PaymentPlan(models.Model):
    _name = 'gic.payment.plan'
    _description = 'Plan de Pago'

    name = fields.Char(string='Nombre', required=True)
    settlement_period = fields.Integer(string='Plazo de Acreditación (días)', required=True)
    deduction_ids = fields.Many2many('gic.deduction', string='Deducciones')

