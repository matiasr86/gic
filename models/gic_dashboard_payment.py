from odoo import models, fields, api
from datetime import datetime, timedelta

class GicCobrosDashboard(models.Model):
    _name = 'gic.dashboard.payment'
    _description = 'Resumen de Cobros y Ventas del Mes Actual'

    month = fields.Selection([(str(i), str(i)) for i in range(1, 13)], string="Mes", required=True,
                             default=lambda self: str(datetime.now().month))
    year = fields.Selection([(str(i), str(i)) for i in range(2020, datetime.now().year + 1)], string="Año",
                            required=True, default=lambda self: str(datetime.now().year))
    total_to_collect = fields.Float(string="Monto Total a Cobrar", compute="_compute_totals", readonly=True)
    total_sales = fields.Float(string="Monto Total Vendido", compute="_compute_totals", readonly=True)
    total_to_accredit = fields.Float(string="Monto Total a Acreditar", compute="_compute_totals", readonly=True)
    selected_date = fields.Date(string='Fecha Seleccionada', default=fields.Date.context_today)
    coupons = fields.One2many('pos.payment', string='Cupones', compute='_compute_coupons')

    @api.depends('month', 'year')
    def _compute_totals(self):
        for record in self:
            current_month = int(record.month)
            current_year = int(record.year)

            # Calcula el rango de fechas para el mes seleccionado
            start_date = datetime(current_year, current_month, 1)
            end_date = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)
                        if current_month < 12 else datetime(current_year, 12, 31))

            # Filtramos los cobros y ventas dentro del período seleccionado
            payments = self.env['pos.payment'].search([
                ('state', '!=', 'cancelled'),
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date)
            ])
            # Filtramos los cobros a acreditar
            payments_to_collect = self.env['pos.payment'].search([
                ('state', 'in', ['new', 'checked'])
            ])

            # Calculamos los totales
            total_collect = sum(payment.amount_to_collect for payment in payments_to_collect)
            total_sales = sum(payment.amount for payment in payments if payment.gic_pos_id)
            total_accredit = sum(payment.amount_to_collect for payment in payments if payment.state in ["new", "checked"])

            # Asignamos los valores calculados a los campos
            record.total_to_collect = total_collect
            record.total_sales = total_sales
            record.total_to_accredit = total_accredit

    @api.depends('selected_date')
    def _compute_coupons(self):
        for record in self:
            if record.selected_date:
                record.coupons = self.env['pos.payment'].search([
                    ('state', '!=', 'cancelled'),
                    ('settlement_date_only', '=', record.selected_date)
                ])

    @api.model
    def default_get(self, field_list):
        res = super(GicCobrosDashboard, self).default_get(field_list)
        if 'selected_date' in field_list:
            res['selected_date'] = fields.Date.context_today(self)
        if 'month' in field_list:
            res['month'] = str(datetime.now().month)
        if 'year' in field_list:
            res['year'] = str(datetime.now().year)
        return res
