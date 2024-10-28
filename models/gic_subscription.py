from datetime import timedelta

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
    gic_pos_ids = fields.One2many('gic.pos', 'subscription_id', string='Puntos de Venta GIC')
    active = fields.Boolean(string="Suscripción Activa", default=True)
    start_date = fields.Datetime(string="Fecha de Inicio", default=lambda self: fields.Datetime.now())
    days_remaining = fields.Integer(string="Días Restantes", compute="_compute_days_remaining", store=False)

    # Método para calcular los días restantes de prueba de la suscripción
    @api.depends('start_date')
    def _compute_days_remaining(self):
        for record in self:
            if record.name == "Prueba Plan GIC" and record.active:
                days_remaining = (record.start_date + timedelta(days=30) - fields.Datetime.now()).days
                record.days_remaining = max(0, days_remaining)
                # Desactivar la suscripción si los días restantes llegan a 0
                if record.days_remaining == 0:
                    record.active = False
            else:
                record.days_remaining = 0

    # Metodo para implementar una validación que permita crear solo una instancia suscripccion
    @api.model
    def create(self, vals):
        if self.search_count([]) > 0:
            raise UserError("Solo se permite una única suscripción activa.")
        return super(GicSubscription, self).create(vals)

    # Metodo para modificar el plan solo si se tiene el token para hacerlo
    def write(self, vals):
        token_input = vals.get('token_input')
        stored_token = self.env['ir.config_parameter'].sudo().get_param('gic.subscription.token')

        if token_input != stored_token:
            raise AccessError("Token inválido. No tienes permiso para modificar esta suscripción.")

        # Si el campo 'strategy' se cambia, valida los límites de gic_pos con la nueva estrategia
        new_strategy = vals.get('strategy', self.strategy)
        if new_strategy != self.strategy:
            self._validate_gic_pos_limit(new_strategy)

        return super(GicSubscription, self).write(vals)

    # Implementacion del patrón de diseño strategy
    # Retorna la estrategia de validación de sesiones según el tipo de suscripción
    def get_strategy(self):
        if self.strategy == 'plan_gic':
            return PlanGIC()
        elif self.strategy == 'plan_gic_plus':
            return PlanGICPlus()
        elif self.strategy == 'plan_gic_premium':
            return PlanGICPremium()
        else:
            raise UserError("Tipo de plan no soportado.")

    # Metodo para agregar un nuevo punto de venta GIC respetando el limite segun la estrategia del plan.
    def add_gic_pos(self, vals):
        strategy = self.get_strategy()
        sesiones_contadas = len(self.gic_pos_ids.filtered(lambda pos: pos.active))

        # Validación de límite de sesiones
        strategy.validar_sesiones(sesiones_contadas + 1)  # +1 porque se va a añadir una nueva sesión
        return self.env['gic.pos'].create(vals)

    # Metodo para validar y al cambiar de plan a un plan inferior desactivar los puntos de venta gic que sobrepasan el plan
    def _validate_gic_pos_limit(self, strategy_key):
        # Crear una instancia de la estrategia según la clave recibida
        if strategy_key == 'plan_gic':
            strategy = PlanGIC()
        elif strategy_key == 'plan_gic_plus':
            strategy = PlanGICPlus()
        elif strategy_key == 'plan_gic_premium':
            strategy = PlanGICPremium()
        else:
            raise UserError("Tipo de plan no soportado.")

        # Obtener el límite de puntos de venta permitidos
        limit = strategy.get_limit()
        active_gic_pos = self.gic_pos_ids.filtered(lambda pos: pos.active)

        # Desactivar los puntos de venta que exceden el límite
        if len(active_gic_pos) > limit:
            excess_count = len(active_gic_pos) - limit
            for gic_pos in active_gic_pos.sorted(key=lambda r: r.create_date, reverse=True)[:excess_count]:
                gic_pos.active = False  # Desactivar la instancia gic_pos

class SesionPlanStrategy:
    def validar_sesiones(self, sesiones_contadas):
        raise NotImplementedError("Este método debe ser implementado por subclases")

class PlanGIC(SesionPlanStrategy):
    def validar_sesiones(self, sesiones_contadas):
        if sesiones_contadas > 3:
            raise UserError("El Plan GIC solo permite hasta 3 sesiones.")

    def get_limit(self):
        return 3

class PlanGICPlus(SesionPlanStrategy):
    def validar_sesiones(self, sesiones_contadas):
        if sesiones_contadas > 10:
            raise UserError("El Plan GIC+ solo permite hasta 10 sesiones.")

    def get_limit(self):
        return 10

class PlanGICPremium(SesionPlanStrategy):
    def validar_sesiones(self, sesiones_contadas):
        # Sin límite, no lanza error.
        pass

    def get_limit(self):
        return float('inf')  # Sin límite

