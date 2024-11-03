from odoo import models, fields, api
from datetime import datetime, timedelta


class GicDashboardPlan(models.Model):
    _name = 'gic.dashboard.plan'
    _description = 'Resumen de Cobros por Plan de Pago'

    month = fields.Selection([(str(i), str(i)) for i in range(1, 13)], string="Mes", required=True,
                             default=lambda self: str(datetime.now().month))
    year = fields.Selection([(str(i), str(i)) for i in range(2020, datetime.now().year + 1)], string="Año",
                            required=True, default=lambda self: str(datetime.now().year))
    payment_plan_id = fields.Many2one('gic.payment.plan', string='Plan de Pago', required=True)
    total_collected = fields.Float(string="Monto Cobrado", compute="_compute_total_collected", store=True)

    @api.depends('month', 'year', 'payment_plan_id')
    def _compute_total_collected(self):
        for record in self:
            current_month = int(record.month)
            current_year = int(record.year)
            payment_plan = record.payment_plan_id

            # Calcula el rango de fechas para el mes seleccionado
            start_date = datetime(current_year, current_month, 1)
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)

            # Filtramos los cobros dentro del período y con el plan de pago especificado
            payments = self.env['pos.payment'].search([
                ('payment_plan', '=', payment_plan.id),
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date)
            ])

            # Calculamos el monto total cobrado
            total_collected = sum(payment.amount for payment in payments)

            # Asignamos el valor calculado al campo
            record.total_collected = total_collected

