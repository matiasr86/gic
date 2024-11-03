from datetime import timedelta
from odoo import models, fields, api

class Dashboard(models.Model):
    _name = 'gic.dashboard'
    _description = 'GIC Dashboard - Summary of Upcoming Payments'

    name = fields.Char(string='Nombre', required=True)
    date = fields.Date(string="Fecha", compute="_compute_date", store=False)
    amount = fields.Float(string="Monto Total a Acreditar", compute="_compute_total_amount", store=False)
    amount_by_destination = fields.Text(string="Monto por Destino", compute="_compute_amount_by_destination", store=False)
    previous_date = fields.Date(string="Fecha Anterior")

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
            payment_on_date = self.env['pos.payment'].search([
                '|', '|',
                ('state', '=', 'new'),
                ('state', '=', 'checked'),
                '&', ('state', '=', 'charged'), ('settlement_date', '=', today)
            ])

            # Sumar el monto de cobros que tienen la misma fecha de acreditación que 'record.fecha'
            record.amount = sum(
                payment.amount_to_collect
                for payment in payment_on_date
                if payment.settlement_date.date() == record.date
            )
            # Asignar al campo name de forma concatenada
            record.name = f"A Acreditar ({record.amount})"

    @api.depends('date')
    def _compute_amount_by_destination(self):
        for record in self:
            # Inicializamos un diccionario vacío para cada registro
            amount_by_destination = {}

            # Verificamos que el registro tenga una fecha antes de proceder
            if record.date:
                # Ejecutamos la búsqueda en `gic.pos.payment` usando `settlement_date_only`
                payments_on_date = self.env['pos.payment'].search([
                    ('settlement_date_only', '=', record.date)
                ])

                # Procesamos los montos acumulados por destino en el diccionario de cada registro
                for payment in payments_on_date:
                    destination = payment.destination_id.name or "Sin destino"
                    if destination in amount_by_destination:
                        amount_by_destination[destination] += payment.amount_to_collect
                    else:
                        amount_by_destination[destination] = payment.amount_to_collect

            # Convertimos el diccionario en un formato de texto específico para el campo `amount_by_destination`
            record.amount_by_destination = "\n".join(
                f"{destino}: ${monto:.2f}" for destino, monto in amount_by_destination.items()
            ) if amount_by_destination else "Sin datos para esta fecha"

    @api.model
    def initialize_dashboard_entries(self):
        if self.search_count([]) < 30:
            for _ in range(30):
                self.create({})