from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .res_partner import TIPOS_CLIENTE


class TiendaConvenio(models.Model):
    _name = "tienda.convenio"
    _description = "Convenio de descuento"
    _order = "tipo_cliente, fecha_inicio desc, id desc"

    name = fields.Char(string="Nombre", required=True)
    tipo_cliente = fields.Selection(
        TIPOS_CLIENTE, string="Tipo de cliente", required=True, index=True
    )
    porcentaje = fields.Float(string="Descuento (%)", required=True)
    fecha_inicio = fields.Date(
        string="Desde", required=True, default=fields.Date.context_today, index=True
    )
    fecha_fin = fields.Date(string="Hasta", index=True)
    active = fields.Boolean(string="Activo", default=True)

    @api.constrains("porcentaje", "fecha_inicio", "fecha_fin")
    def _check_convenio(self):
        for convenio in self:
            if not 0 < convenio.porcentaje <= 40:
                raise ValidationError("El descuento debe ser mayor que 0 y no superar 40 %.")
            if convenio.fecha_fin and convenio.fecha_fin < convenio.fecha_inicio:
                raise ValidationError("La fecha final no puede ser anterior a la fecha inicial.")
