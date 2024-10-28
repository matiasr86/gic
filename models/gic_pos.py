from odoo import models, fields, api
from odoo.exceptions import UserError


class GicPos(models.Model):
    _name = 'gic.pos'
    _description = 'Punto de Venta GIC'

    name = fields.Char(string='Nombre del Punto de Venta')
    subscription_id = fields.Many2one('gic.subscription', string='Plan de Suscripción', required=True)
    odoo_pos_id = fields.Many2one('pos.config', string='Punto de Venta en Odoo', required=True)
    active = fields.Boolean(default=True, string="Activo")

    @api.model
    def create(self, vals):
        # Verifica si ya existe un GicPos con el mismo odoo_pos_id
        existing_pos = self.search([('odoo_pos_id', '=', vals.get('odoo_pos_id'))])
        if existing_pos:
            raise UserError("Este Punto de Venta ya está asignado a otro GIC.")

        # Recupera la suscripción asociada
        subscription = self.env['gic.subscription'].browse(vals.get('subscription_id'))
        pos_count = self.search_count([('subscription_id', '=', subscription.id)])

        # Llama a la estrategia para validar el límite de puntos de venta
        strategy_instance = subscription.get_strategy()
        strategy_instance.validar_sesiones(pos_count + 1)  # +1 por el nuevo punto de venta que se va a crear

        return super(GicPos, self).create(vals)

    @api.constrains('odoo_pos_id')
    def _check_unique_pos(self):
        for record in self:
            existing_pos = self.search([
                ('odoo_pos_id', '=', record.odoo_pos_id.id),
                ('id', '!=', record.id)  # Excluye el registro actual
            ])
            if existing_pos:
                raise UserError("Este Punto de Venta ya está asignado a otro GIC.")

    _sql_constraints = [
        ('unique_odoo_pos_id', 'unique(odoo_pos_id)', "Este Punto de Venta ya está asignado a otro Punto de Venta GIC.")
    ]
