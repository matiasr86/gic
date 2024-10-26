from odoo import models, fields, api

class GicDeduction(models.Model):
    _name = 'gic.deduction'
    _description = 'Deducción'

    name = fields.Char(string='Nombre', required=True)
    date = fields.Datetime(string='Fecha', required=True)
    percentage = fields.Float(string='Porcentaje', required=True)
    state = fields.Selection(
        selection=[
            ("active", "Activa"),
            ("suspended", "Suspendido"),
            ("inactive", "inactiva"),
        ],
        string="Estado",
        required=True,
        copy=False,
        default="active",
    )
    type = fields.Selection([
        ('tax', 'Impuesto'),
        ('tariff', 'Arancel'),
        ('quota', 'Cuota')
    ], string='Tipo', required=True)
    iva = fields.Float(string='IVA')

    def calculate_deduction(self, original_amount):
        if self.type == 'tax':
            return original_amount * (self.percentage / 100)
        elif self.type in ['tariff', 'quota']:
            base_amount = original_amount * (self.percentage / 100)
            iva_deduction = base_amount * (self.iva / 100)  # Supongamos 21% de IVA
            return base_amount + iva_deduction
        return 0.0

    @api.model
    def calcular_iva(self):
        # Implementar lógica para calcular el IVA
        pass
