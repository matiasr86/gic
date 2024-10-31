from odoo import models, fields, api
from datetime import timedelta

class Dashboard(models.Model):
    _name = 'gic.dashboard'
    _description = 'GIC Dashboard - Summary of Upcoming Payments'

    date = fields.Date(string="Fecha", compute="_compute_date", store=False)
    amount = fields.Float(string="Monto a Cobrar", compute="_compute_total_amount", store=False)
    previous_date = fields.Date(string="Fecha Anterior")  # Campo para almacenar la fecha del registro anterior

    @api.depends('previous_date')
    def _compute_date(self):
        for idx, record in enumerate(self):
            if idx == 0:  # Para el primer registro, usa la fecha actual
                record.date = fields.Date.context_today(self)
            else:
                previous_record = self[idx - 1]
                if previous_record.date:
                    record.date = previous_record.date + timedelta(days=1)
                    record.previous_date = previous_record.date

    @api.depends('date')
    def _compute_total_amount(self):
        for record in self:
            # Obtener fecha actual para comparar con cobros en estado 'charged'
            today = fields.Date.context_today(self)

            # Filtrar cobros en los estados 'new', 'checked', y 'charged' según los criterios
            payment_on_date = self.env['gic.pos.payment'].search([
                '|', '|',
                ('state', '=', 'new'),
                ('state', '=', 'checked'),
                '&', ('state', '=', 'charged'), ('settlement_date', '=', today)
            ])

            # Sumar el monto de cobros que tienen la misma fecha de acreditación que 'record.fecha'
            record.amount = sum(payment.amount_to_collect for payment in payment_on_date if payment.settlement_date == record.date)

    @api.model
    def initialize_dashboard_entries(self):
        # Si ya existen 30 registros en el modelo, no crear nuevos
        if self.search_count([]) < 30:
            # Crear 30 registros sin valores específicos, los campos se calculan dinámicamente
            for _ in range(30):
                self.create({})
