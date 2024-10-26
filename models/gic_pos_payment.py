from datetime import timedelta

from odoo import models, fields, api

class GicPosPayment(models.Model):
    _inherit = 'pos.payment'

    submission_date = fields.Datetime(string='Fecha de Presentación', compute='_compute_submission_date')
    settlement_date = fields.Datetime(string='Fecha de Acreditación', compute='_compute_settlement_date')
    #payment_plan_id = fields.Many2one('gic.payment.plan', string='Plan de Pago')
    payment_plan = fields.Many2one(related='payment_method_id.payment_plan_id', string='Plan de Pago', store=False)
    #pricelist_id = fields.Many2one('pos.session', string='Lista de precios')
    pricelist = fields.Many2one(related='pos_order_id.pricelist_id', string='Lista de precios', store=False)
    amount_to_collect = fields.Monetary(string="A Acreditar", currency_field='currency_id', compute='_compute_amount_to_collect')
    currency_id = fields.Many2one('res.currency', string='Currency')
    coupon_number = fields.Integer(string='Cupón')

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

    @api.model
    def create(self, vals):
        # Creamos la instancia del modelo
        record = super(GicPosPayment, self).create(vals)

        # Verificamos si la forma de pago tiene un medio de pago asociado
        if record.payment_method_id and record.payment_method_id.way_id:
            # Asignamos el valor actual de next_number a coupon_number
            record.coupon_number = record.payment_method_id.way_id.next_number
            # Incrementamos el campo numerico en el modelo gic_way
            record.payment_method_id.way_id.next_number += 1

        return record

    @api.depends('amount', 'payment_plan.deduction_ids')
    def _compute_amount_to_collect(self):
        for record in self:
            if record.payment_plan.deduction_ids:
                amount_deductions = sum(
                    deduction.calculate_deduction(record.amount) for deduction in record.payment_plan.deduction_ids
                )
                record.amount_to_collect = record.amount - amount_deductions
            else:
                record.amount_to_collect = record.amount

    @api.depends('create_date', 'submission_date', 'settlement_date')
    def _compute_state(self):
        for record in self:
            if not record.payment_plan:
                continue  # Salta a la siguiente iteración
            current_date = fields.Datetime.now()

            if all([record.create_date, record.submission_date, record.settlement_date]):
                if current_date.date() == record.settlement_date.date():
                    record.state = 'charged'
                elif current_date.date() == record.submission_date.date():
                    record.state = 'checked'
                elif current_date.date() == record.create_date.date():
                    record.state = 'new'
                elif record.create_date < current_date < record.submission_date:
                    record.state = 'new'
                elif record.create_date < current_date < record.settlement_date:
                    record.state = 'checked'
                elif current_date >= record.settlement_date:
                    record.state = 'charged'
            else:
                record.state = 'new'  # Valor por defecto si faltan fechas

    @api.depends('create_date', 'payment_method_id')
    def _compute_submission_date(self):
        for record in self:
            if not record.payment_plan:
                record.submission_date = record.create_date  # O alguna fecha por defecto
                continue  # Salta a la siguiente iteración

            order_date = record.create_date
            payment_method = record.payment_method_id
            payment_plan = payment_method.payment_plan_id

            if payment_plan:
                settlement_period = payment_plan.settlement_period

                # Determinamos la fecha de presentación
                if settlement_period == 0:
                    # Si el periodo de liquidación es 0, la fecha de presentación es la misma que la de creación
                    record.submission_date = order_date
                else:
                    # Verificamos la hora de creación
                    if order_date.hour < 17:
                        record.submission_date = order_date
                    else:
                        # Si la hora es mayor o igual a 17, se presenta al siguiente día hábil
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
            if not record.payment_plan:
                record.settlement_date = record.submission_date
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
