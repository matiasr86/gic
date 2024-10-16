
from odoo import http
from odoo.http import request, _logger


class GicPaymentController(http.Controller):
    @http.route('/api/create_gic_payment', type='json', auth='user', methods=['POST'])
    def create_gic_payment(self, **kwargs):
        order_id = kwargs.get('order_id')

        # Obtener la orden correspondiente
        order = request.env['pos.order'].browse(order_id)
        _logger.info(f"Order found: {order.id} - {order.name}")

        # Comprobar que la orden existe
        if not order.exists():
            return {'error': 'Order not found'}

        # Datos para crear el GicPayment
        payment_data = {
            'order_date': order.date_order,
            'pos_id': order.session_id.id,
            'order_id': order.id,
            'user_id': request.env.user.id,
            'payment_method_id': order.payment_method_id.id,
            'payment_plan_id': order.payment_plan_id.id,
            'order_amount': order.amount_total,
            'cliente_id': order.partner_id.id,
        }
        _logger.info(f"Payment data: {payment_data}")

        try:
            # Crear la instancia de GicPayment
            payment = request.env['gic.payment'].create(payment_data)
            return {'payment_id': payment.id}
        except Exception as e:
            return {'error': str(e)}



# class Gic(http.Controller):
#     @http.route('/gic/gic', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gic/gic/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('gic.listing', {
#             'root': '/gic/gic',
#             'objects': http.request.env['gic.gic'].search([]),
#         })

#     @http.route('/gic/gic/objects/<model("gic.gic"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gic.object', {
#             'object': obj
#         })
