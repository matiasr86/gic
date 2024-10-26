from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError


class GicSubscription(models.Model):
    _name = 'gic.subscription'
    _description = 'Planes de Suscripción'

    name = fields.Char(string="Nombre", required=True)
    strategy = fields.Selection([
        ('plan_gic', 'Plan GIC'),
        ('plan_gic_plus', 'Plan GIC+'),
        ('plan_gic_premium', 'Plan GIC Premium'),
    ], string="Estrategia de Plan", required=True)

    token_input = fields.Char(string="Token de Seguridad", store=False)  # Campo temporal para el token

    @api.model
    def create(self, vals):
        if self.search_count([]) > 0:
            raise UserError("Solo se permite una única suscripción activa.")
        return super(GicSubscription, self).create(vals)

    def write(self, vals):
        token_input = vals.get('token_input')
        stored_token = self.env['ir.config_parameter'].sudo().get_param('gic.subscription.token')

        if token_input != stored_token:
            raise AccessError("Token inválido. No tienes permiso para modificar esta suscripción.")

        return super(GicSubscription, self).write(vals)


class SesionPlanStrategy:
    def validar_sesiones(self, sesiones_contadas):
        raise NotImplementedError("Este método debe ser implementado por subclases")

class PlanGIC(SesionPlanStrategy):
    def validar_sesiones(self, sesiones_contadas):
        if sesiones_contadas > 3:
            raise ValueError("El Plan GIC solo permite hasta 3 sesiones.")

class PlanGICPlus(SesionPlanStrategy):
    def validar_sesiones(self, sesiones_contadas):
        if sesiones_contadas > 10:
            raise ValueError("El Plan GIC+ solo permite hasta 10 sesiones.")

class PlanGICPremium(SesionPlanStrategy):
    def validar_sesiones(self, sesiones_contadas):
        # Sin límite, se puede omitir la validación
        pass


