from odoo import models, fields, api
from datetime import timedelta  # Asegúrate de que esta línea esté correcta


class GicPayment(models.Model):
    _name = 'gic.payment'
    _description = 'Cobro realizado en el punto de venta'

    order_date = fields.Datetime(string='Fecha del Pedido')
    pos_id = fields.Many2one('pos.session', string='POS')
    order_id = fields.Many2one('pos.order', string='Pedido')
    user_id = fields.Many2one('res.users', string='Usuario')
    payment_method_id = fields.Many2one('pos.payment.method', string='Forma de Pago')
    payment_plan_id = fields.Many2one('gic.payment.plan', string='Plan de Pago')
    order_amount = fields.Float(string='Monto de la Orden')
    cliente_id = fields.Many2one('res.partner', string='Cliente')

    state = fields.Selection(
        selection=[
            ("new", "Ingresado"),
            ("checked", "Presentado"),
            ("charged", "Cobrado"),
        ],
        string="Estado",
        compute='_compute_state',
        store=True,
        copy=False,
        default="new",
    )

    submission_date = fields.Datetime(string='Fecha de Presentación', compute='_compute_submission_date', store=True)
    settlement_date = fields.Datetime(string='Fecha de Acreditación', compute='_compute_settlement_date', store=True)

    @api.depends('order_date', 'submission_date', 'settlement_date')
    def _compute_state(self):
        for record in self:
            current_date = fields.Datetime.now()

            if all([record.order_date, record.submission_date, record.settlement_date]):
                if current_date.date() == record.settlement_date.date():
                    record.state = 'charged'
                elif current_date.date() == record.submission_date.date():
                    record.state = 'checked'
                elif current_date.date() == record.order_date.date():
                    record.state = 'new'
                elif record.order_date < current_date < record.submission_date:
                    record.state = 'new'
                elif record.order_date < current_date < record.settlement_date:
                    record.state = 'checked'
                elif current_date >= record.settlement_date:
                    record.state = 'charged'
            else:
                record.state = 'new'  # Valor por defecto si faltan fechas

    @api.depends('order_id', 'payment_method_id')
    def _compute_submission_date(self):
        for record in self:
            if not record.order_id or not record.payment_method_id:
                record.submission_date = False
                continue

            order_date = record.order_id.date_order
            payment_method = record.payment_method_id
            payment_plan = payment_method.payment_plan_id

            if payment_plan:
                settlement_period = payment_plan.settlement_period
                if settlement_period == 0:
                    record.submission_date = order_date
                else:
                    manual_finish_lot = payment_method.way_id.manual_finish_lot

                    if manual_finish_lot:
                        record.submission_date = order_date
                    else:
                        if order_date.hour < 17:
                            presentation_date = order_date
                        else:
                            presentation_date = order_date + timedelta(days=1)

                        presentation_date = self._get_next_business_day(presentation_date)
                        record.submission_date = presentation_date

    def _get_next_business_day(self, date):
        holidays = self.env['gic.holiday'].search([]).mapped('date')
        while True:
            if date.weekday() == 5:  # Sábado
                date += timedelta(days=2)
            elif date.weekday() == 6:  # Domingo
                date += timedelta(days=1)
            elif date in holidays:
                date += timedelta(days=1)
            else:
                break
        return date

    @api.depends('submission_date', 'payment_method_id')
    def _compute_settlement_date(self):
        for record in self:
            if not record.submission_date or not record.payment_method_id:
                record.settlement_date = False
                continue

            payment_plan = record.payment_method_id.payment_plan_id
            if payment_plan:
                settlement_period = payment_plan.settlement_period
                if settlement_period == 0:
                    record.settlement_date = record.submission_date
                else:
                    record.settlement_date = self._add_business_days(record.submission_date, settlement_period)

    def _add_business_days(self, start_date, days):
        current_date = start_date
        holidays = self.env['gic.holiday'].search([]).mapped('date')

        while days > 0:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5 and current_date not in holidays:
                days -= 1

        return current_date
