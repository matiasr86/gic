from odoo import models, fields, api, exceptions

class GicDeduction(models.Model):
    _name = 'gic.deduction'
    _description = 'Deducción'

    name = fields.Char(string='Nombre', required=True)
    date = fields.Datetime(string='Fecha', required=True)
    percentage = fields.Float(string='Porcentaje', required=True)
    state = fields.Selection(
        selection=[
            ("active", "Activa"),
            ("suspended", "Suspendido"),
            ("inactive", "inactiva"),
        ],
        string="Estado",
        required=True,
        copy=False,
        default="active",
    )
    type = fields.Selection([
        ('tax', 'Impuesto'),
        ('tariff', 'Arancel'),
        ('quota', 'Cuota')
    ], string='Tipo', required=True)
    iva = fields.Float(string='IVA')

    def calculate_deduction(self, original_amount):
        if self.type == 'tax':
            return original_amount * (self.percentage / 100)
        elif self.type in ['tariff', 'quota']:
            base_amount = original_amount * (self.percentage / 100)
            iva_deduction = base_amount * (self.iva / 100)  # Supongamos 21% de IVA
            return base_amount + iva_deduction
        return 0.0

    @api.model
    def calcular_iva(self):
        # Implementar lógica para calcular el IVA
        pass

    ## Metodo para crear una nueva deduccion que reemplace una con valores deprecados
    @api.model
    def create_new_deduction_and_update_plans(self, old_deduction, new_percentage, new_iva):
        # Crear la nueva deducción con valores actualizados
        new_deduction = self.with_context(skip_name_validation=True).create({
            'name': old_deduction.name,
            'date': fields.Datetime.now(),
            'percentage': new_percentage,
            'state': 'active',
            'type': old_deduction.type,
            'iva': new_iva,
        })

        # Actualizar los planes de pago que referencian la deducción antigua
        plans_to_update = self.env['gic.payment.plan'].search([('deduction_ids', '=', old_deduction.id)])
        for plan in plans_to_update:
            plan.deduction_ids = [(3, old_deduction.id)]  # Eliminar deducción anterior
            plan.deduction_ids = [(4, new_deduction.id)]  # Agregar nueva deducción

        # Cambiar el estado de la deducción antigua a 'inactive'
        old_deduction.state = 'inactive'

    def write(self, vals):
        for deduction in self:
            new_percentage = vals.get('percentage', deduction.percentage)
            new_iva = vals.get('iva', deduction.iva)

            if new_percentage != deduction.percentage or new_iva != deduction.iva:
                deduction.create_new_deduction_and_update_plans(deduction, new_percentage, new_iva)
                return True  # Terminar la ejecución para evitar cambios en la deducción original

        return super(GicDeduction, self).write(vals)

    @api.model
    def create(self, vals):
        if not self.env.context.get('skip_name_validation') and vals.get('state') == 'active':
            existing_deduction = self.search([('name', '=', vals.get('name'))], limit=1)
            if existing_deduction:
                raise exceptions.ValidationError("La deducción ya existe con ese nombre.")

        return super(GicDeduction, self).create(vals)