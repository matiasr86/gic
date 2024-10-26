from odoo import models, fields, api

class GicSubscription(models.Model):
    _name = 'gic.subscription'
    _description = 'Planes de Suscripción'

    name = fields.Char(string="Nombre", required=True)
    strategy = fields.Selection([
        ('plan_gic', 'Plan GIC'),
        ('plan_gic_plus', 'Plan GIC+'),
        ('plan_gic_premium', 'Plan GIC Premium'),
    ], string="Estrategia de Plan", required=True)

    def get_strategy(self):
        strategies = {
            'plan_gic': PlanGIC(),
            'plan_gic_plus': PlanGICPlus(),
            'plan_gic_premium': PlanGICPremium(),
        }
        return strategies.get(self.strategy)


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