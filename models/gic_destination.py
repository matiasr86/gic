from odoo import models, fields, api

class GicDestination(models.Model):
    _name = 'gic.destination'
    _description = 'Destino de Cobro'

    name = fields.Char(string='Nombre del Destino', required=True)
    type = fields.Selection([
        ('cashbox', 'Caja'),
        ('bank', 'Banco'),
        ('wallet', 'Billetera Virtual'),
    ], string='Tipo de Destino', required=True)
