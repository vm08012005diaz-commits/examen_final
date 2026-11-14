from datetime import timedelta
from uuid import uuid4

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AulaReserva(models.Model):
    _name = "unicah.aula.reserva"
    _description = "Reserva de aula"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha_inicio desc"

    name = fields.Char(string="Referencia", required=True, default="Nueva reserva")
    aula_id = fields.Many2one(
        "resource.resource", string="Aula", required=True,
        domain="[('resource_type', '=', 'material')]", index=True,
    )
    edificio = fields.Char(related="aula_id.edificio", store=True)
    capacidad = fields.Integer(related="aula_id.capacidad_aula", string="Capacidad")
    equipamiento = fields.Text(related="aula_id.equipamiento_aula", string="Equipamiento")
    solicitante_id = fields.Many2one(
        "res.users", string="Solicitante", required=True,
        default=lambda self: self.env.user, index=True,
    )
    fecha_inicio = fields.Datetime(string="Inicio", required=True, index=True)
    fecha_fin = fields.Datetime(string="Fin", required=True, index=True)
    proposito = fields.Text(string="Proposito", required=True)
    estado = fields.Selection(
        [("borrador", "Borrador"), ("pendiente", "Pendiente de aprobacion"),
         ("confirmada", "Confirmada"), ("utilizada", "Utilizada"), ("cancelada", "Cancelada")],
        string="Estado", default="borrador", required=True, index=True,
    )
    duracion_horas = fields.Float(
        string="Duracion (horas)", compute="_compute_duracion_horas", store=True
    )
    active = fields.Boolean(default=True)
    recurrente = fields.Boolean(string="Reserva recurrente")
    repeticiones = fields.Integer(string="Repeticiones semanales", default=1)
    reserva_origen_id = fields.Many2one("unicah.aula.reserva", string="Reserva original", copy=False)
    reserva_recurrente_ids = fields.One2many("unicah.aula.reserva", "reserva_origen_id", string="Reservas generadas")
    codigo_qr = fields.Char(string="Codigo de registro", default=lambda self: uuid4().hex, copy=False, readonly=True)
    qr_html = fields.Html(string="QR de registro", compute="_compute_qr_html", sanitize=False)

    @api.depends("fecha_inicio", "fecha_fin")
    def _compute_duracion_horas(self):
        for reserva in self:
            if reserva.fecha_inicio and reserva.fecha_fin:
                reserva.duracion_horas = (
                    reserva.fecha_fin - reserva.fecha_inicio
                ).total_seconds() / 3600
            else:
                reserva.duracion_horas = 0

    @api.depends("codigo_qr")
    def _compute_qr_html(self):
        for reserva in self:
            reserva.qr_html = Markup(
                '<img alt="Codigo QR" style="width:130px;height:130px" '
                'src="/report/barcode/?barcode_type=QR&amp;value=%s&amp;width=130&amp;height=130"/>'
            ) % (reserva.codigo_qr or "")

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

    def action_solicitar(self):
        self.write({"estado": "pendiente"})
        for reserva in self:
            reserva.message_post(body="La reserva fue enviada para aprobacion.")

    def action_confirmar(self):
        for reserva in self:
            reserva.estado = "confirmada"
            reserva.message_post(
                body="La reserva fue aprobada y confirmada.",
                partner_ids=[reserva.solicitante_id.partner_id.id],
            )
            if reserva.recurrente and not reserva.reserva_origen_id:
                for semana in range(1, max(reserva.repeticiones, 1)):
                    inicio = reserva.fecha_inicio + timedelta(weeks=semana)
                    fin = reserva.fecha_fin + timedelta(weeks=semana)
                    if not self.search_count([("reserva_origen_id", "=", reserva.id), ("fecha_inicio", "=", inicio)]):
                        reserva.copy({
                            "name": f"{reserva.name} - Semana {semana + 1}",
                            "fecha_inicio": inicio, "fecha_fin": fin,
                            "estado": "confirmada", "reserva_origen_id": reserva.id,
                            "recurrente": False, "repeticiones": 1,
                        })

    def action_marcar_utilizada(self):
        self.write({"estado": "utilizada"})
        for reserva in self:
            reserva.message_post(body="Uso del aula registrado mediante el codigo QR.")

    def action_cancelar(self):
        self.write({"estado": "cancelada"})

    def action_borrador(self):
        self.write({"estado": "borrador"})
