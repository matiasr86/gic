from odoo import models, fields, api
from odoo.exceptions import ValidationError

# Modelo Plan de Pago
class PaymentPlan(models.Model):
    _name = 'gic.payment.plan'
    _description = 'Plan de Pago'

    @api.constrains('deduction_ids')
    def _check_deductions_state(self):
        for record in self:
            for deduction in record.deduction_ids:
                if deduction.state == 'inactive':
                    raise ValidationError("No se pueden agregar deducciones inactivas al plan de pago.")

    name = fields.Char(string='Nombre', required=True)
    settlement_period = fields.Integer(string='Plazo de Acreditación (días)', required=True)
    deduction_ids = fields.Many2many('gic.deduction', string='Deducciones')

