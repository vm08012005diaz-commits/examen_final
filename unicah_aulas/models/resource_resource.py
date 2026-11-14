from odoo import fields, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    edificio = fields.Char(string="Edificio")
    capacidad_aula = fields.Integer(string="Capacidad")
    equipamiento_aula = fields.Text(string="Equipamiento")
