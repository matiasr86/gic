from odoo import models, fields, api

class GicDashboard(models.Model):
    _name = 'gic.dashboard'
    _description = 'Dashboard de Cobros'

    date = fields.Date(string='Fecha', required=True)
    total_amount = fields.Monetary(string='Monto Total', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Moneda')

    @api.model
    def get_data(self):
        # Limpiar datos existentes
        existing_dashboards = self.search([])
        existing_dashboards.unlink()

        # Obtener todos los GicPosPayment
        payments = self.env['gic.pos.payment'].search([])

        # Agrupar los pagos por fecha de liquidación
        amounts_by_date = {}
        for payment in payments:
            if payment.settlement_date:
                date_key = payment.settlement_date.date()
                if date_key not in amounts_by_date:
                    amounts_by_date[date_key] = 0.0
                amounts_by_date[date_key] += payment.amount_to_collect

        # Crear registros en el modelo GicDashboard
        for date_key, total in amounts_by_date.items():
            self.create({
                'date': date_key,
                'total_amount': total,
                'currency_id': payments[0].currency_id.id if payments else False,  # Asumir moneda del primer pago
            })
