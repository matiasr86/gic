from odoo import models, fields, api

class GicHoliday(models.Model):
    _name = 'gic.holiday'
    _description = 'Registro de Feriados'

    date = fields.Datetime(string='Fecha', required=True)

