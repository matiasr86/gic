from odoo import models, fields, api

class GicWay(models.Model):
    _name = 'gic.way'
    _description = 'Medio de Cobro'

    name = fields.Char(string='Nombre', required=True)
    supplier = fields.Char(string='Proveedor')
    manual_finish_lot = fields.Boolean(string='Cierre de Lote Manual')
    state = fields.Selection(
        selection=[
            ("active", "Activa"),
            ("suspended", "Suspendido"),
            ("inactive", "inactivo"),
        ],
        string="Estado",
        required=True,
        copy=False,
        default="active",
    )
