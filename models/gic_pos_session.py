from odoo import models, fields, api

class GicPosSession(models.Model):
    _name = 'gic.pos.session'
    _description = 'Sesiones de Punto de Venta'

    subscription_id = fields.Many2one('gic.subscription', string="Suscripción")
    point_of_sale_id = fields.Many2one('pos.config', string="Punto de Venta")

    @api.model
    def create(self, vals):
        # Obtener el ID de la suscripción
        subscription_id = vals.get('subscription_id')
        if subscription_id:
            # Obtener la suscripción seleccionada
            subscription = self.env['gic.subscription'].browse(subscription_id)

            # Contar la cantidad de puntos de venta
            active_pos_count = self.env['pos.config'].search_count([])  # Contar todos los puntos de venta

            # Obtener la estrategia y validar el número de puntos de venta permitidos
            strategy = subscription.get_strategy()
            strategy.validar_puntos_de_venta(active_pos_count)

        # Crear la sesión si la validación es exitosa
        return super(GicPosSession, self).create(vals)
