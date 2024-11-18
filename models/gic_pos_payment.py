import pytz
from datetime import timedelta
from odoo import models, fields, api

class GicPosPayment(models.Model):
    _inherit = 'pos.payment'

    gic_pos_id = fields.Many2one('gic.pos', string='Punto de Venta GIC')
    destination_id = fields.Many2one(related='payment_method_id.way_id.destination_id', string="Destino")
    pos_config_id = fields.Many2one(related='pos_order_id.config_id', string='Punto de Venta en Odoo', store=False)
    submission_date = fields.Datetime(string='Fecha de Presentación', compute='_compute_submission_date')
    settlement_date = fields.Datetime(string='Fecha de Acreditación',compute='_compute_settlement_date')
    settlement_date_only = fields.Date(string='Fecha de Acreditación (Solo Fecha)',compute='_compute_settlement_date_only',store=True)
    payment_plan = fields.Many2one(related='payment_method_id.payment_plan_id', string='Plan de Pago', store=False)
    applied_deductions = fields.Many2many('gic.deduction', string='Deducciones Aplicadas')
    pricelist = fields.Many2one(related='pos_order_id.pricelist_id', string='Lista de precios', store=False)
    amount_to_collect = fields.Monetary(string="A Acreditar", currency_field='currency_id', compute='_compute_amount_to_collect')
    currency_id = fields.Many2one('res.currency', string='Currency')
    coupon_number = fields.Integer(string='Cupón')

    state = fields.Selection(
        selection=[
            ("new", "Ingresado"),
            ("checked", "Presentado"),
            ("charged", "Cobrado"),
            ("excluded", "Excluido"),

        ],
        string="Estado",
        compute='_compute_state',
        store=True,
        copy=False,
        default="new",
    )

    # Verifica si el registro tiene un gic_pos asociado y si la suscripción está activa.
    def has_gic_pos(self):
        return bool(self.gic_pos_id) and self.gic_pos_id.subscription_id.active

    # Metodo para establecer el numero de cupon al cobro realizado con terminal
    @api.model
    def create(self, vals):
        # Creamos la instancia del modelo
        record = super(GicPosPayment, self).create(vals)

        # Asignar gic_pos_id basado en el pos.config de la orden
        pos_order = record.pos_order_id
        if pos_order and pos_order.config_id:
            gic_pos = self.env['gic.pos'].search([('odoo_pos_id', '=', pos_order.config_id.id)], limit=1)
            record.gic_pos_id = gic_pos.id if gic_pos else False

        # Verificamos si la forma de pago tiene un medio de pago asociado
        if record.payment_method_id and record.payment_method_id.way_id:
            # Asignamos el valor actual de next_number a coupon_number
            record.coupon_number = record.payment_method_id.way_id.next_number
            # Incrementamos el campo numerico en el modelo gic_way
            record.payment_method_id.way_id.next_number += 1

        # Asignar deducciones específicas del plan de pago en el momento del cobro
        if record.payment_plan and record.payment_plan.deduction_ids:
            record.applied_deductions = [(6, 0, record.payment_plan.deduction_ids.ids)]

        return record

    @api.depends('amount', 'applied_deductions')
    def _compute_amount_to_collect(self):
        for record in self:
            if not record.has_gic_pos():
                record.amount_to_collect = 0
                continue

            if record.applied_deductions:
                amount_deductions = sum(
                    deduction.calculate_deduction(record.amount) for deduction in record.applied_deductions
                )
                record.amount_to_collect = record.amount - amount_deductions
            else:
                record.amount_to_collect = record.amount

    @api.depends('create_date', 'submission_date', 'settlement_date')
    def _compute_state(self):
        for record in self:
            # Verificamos si el registro tiene un gic_pos
            if not record.has_gic_pos():
                record.state = 'excluded'
                continue

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
        argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')

        for record in self:
            if not record.has_gic_pos() or not record.payment_plan or record.payment_plan.settlement_period == 0:
                # Si no tiene gic_pos, no tiene un plan de pago, o el plazo de acreditación es 0, la fecha de presentación es la fecha de venta
                record.submission_date = record.create_date
                continue

            # Convertir create_date a la zona horaria de Argentina
            order_date = pytz.utc.localize(record.create_date).astimezone(argentina_tz)
            gic_way = record.payment_method_id.way_id

            if gic_way.manual_finish_lot:
                # Cierre de lote manual - siempre el próximo día hábil sin importar la hora del cobro
                submission_date = self._get_next_business_day(order_date)
            else:
                # Cierre de lote automático
                if order_date.hour < 17:
                    submission_date = order_date  # Mismo día si es antes de las 17
                else:
                    # Ajustar la fecha de presentación al siguiente día hábil
                    submission_date = self._get_next_business_day(order_date)

            # Eliminar la zona horaria para que sea naive datetime
            record.submission_date = submission_date.replace(tzinfo=None)

    def _get_next_business_day(self, date):
        next_date = date + timedelta(days=1)
        while next_date.weekday() in (5, 6) or self._is_holiday(next_date):
            next_date += timedelta(days=1)
        return next_date

    def _is_holiday(self, date):
        holiday = self.env['gic.holiday'].search([('date', '=', date.date())], limit=1)
        return bool(holiday)

    @api.depends('submission_date', 'payment_method_id')
    def _compute_settlement_date(self):
        for record in self:
            if not record.has_gic_pos():
                record.settlement_date = record.create_date  # O alguna fecha por defecto
                continue
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

    @api.depends('settlement_date')
    def _compute_settlement_date_only(self):
        for record in self:
            record.settlement_date_only = record.settlement_date.date() if record.settlement_date else False

    def _add_business_days(self, start_date, days):
        current_date = start_date
        holidays = self.env['gic.holiday'].search([]).mapped('date')

        while days > 0:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5 and current_date not in holidays:
                days -= 1

        return current_date
