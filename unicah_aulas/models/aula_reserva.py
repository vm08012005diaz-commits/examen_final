from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AulaReserva(models.Model):
    _name = "unicah.aula.reserva"
    _description = "Reserva de aula"
    _order = "fecha_inicio desc"

    name = fields.Char(string="Referencia", required=True, default="Nueva reserva")
    aula_id = fields.Many2one(
        "resource.resource", string="Aula", required=True,
        domain="[('resource_type', '=', 'material')]", index=True,
    )
    solicitante_id = fields.Many2one(
        "res.users", string="Solicitante", required=True,
        default=lambda self: self.env.user, index=True,
    )
    fecha_inicio = fields.Datetime(string="Inicio", required=True, index=True)
    fecha_fin = fields.Datetime(string="Fin", required=True, index=True)
    proposito = fields.Text(string="Proposito", required=True)
    estado = fields.Selection(
        [("borrador", "Borrador"), ("confirmada", "Confirmada"), ("cancelada", "Cancelada")],
        string="Estado", default="borrador", required=True, index=True,
    )
    duracion_horas = fields.Float(
        string="Duracion (horas)", compute="_compute_duracion_horas", store=True
    )
    active = fields.Boolean(default=True)

    @api.depends("fecha_inicio", "fecha_fin")
    def _compute_duracion_horas(self):
        for reserva in self:
            if reserva.fecha_inicio and reserva.fecha_fin:
                reserva.duracion_horas = (
                    reserva.fecha_fin - reserva.fecha_inicio
                ).total_seconds() / 3600
            else:
                reserva.duracion_horas = 0

    @api.constrains("fecha_inicio", "fecha_fin")
    def _check_fechas(self):
        for reserva in self:
            if reserva.fecha_inicio and reserva.fecha_fin and reserva.fecha_fin <= reserva.fecha_inicio:
                raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")

    @api.constrains("aula_id", "fecha_inicio", "fecha_fin", "estado")
    def _check_traslape(self):
        for reserva in self.filtered(lambda r: r.estado == "confirmada"):
            conflicto = self.search_count([
                ("id", "!=", reserva.id), ("aula_id", "=", reserva.aula_id.id),
                ("estado", "=", "confirmada"),
                ("fecha_inicio", "<", reserva.fecha_fin), ("fecha_fin", ">", reserva.fecha_inicio),
            ])
            if conflicto:
                raise ValidationError("El aula ya esta reservada en ese intervalo.")

    def action_confirmar(self):
        self.write({"estado": "confirmada"})

    def action_cancelar(self):
        self.write({"estado": "cancelada"})

    def action_borrador(self):
        self.write({"estado": "borrador"})
