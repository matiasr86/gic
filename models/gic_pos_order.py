from odoo import models, api

class GicPosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def action_pos_order_paid(self):
        res = super(GicPosOrder, self).action_pos_order_paid()

        # Obtener el método de pago
        payment_method = self.payment_method_id

        # Crear la instancia de GicPayment
        self.env['gic.payment'].create({
            'pos_id': self.session_id.id,
            'order_id': self.id,
            'user_id': self.user_id.id,
            'payment_method_id': payment_method.id,
            'cliente_id': self.partner_id.id,
            'state': 'new',
            'order_date': self.date_order,  # Fecha del pedido
            'order_amount': self.amount_total,  # Monto total de la orden
            'payment_plan_id': payment_method.payment_plan_id.id,  # Plan de pago
        })

        return res

