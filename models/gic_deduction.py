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

    @api.model
    def calcular_deduccion(self):
        # Implementar lógica para calcular la deducción de impuestos
        pass

    @api.model
    def calcular_iva(self):
        # Implementar lógica para calcular el IVA
        pass
