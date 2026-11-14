from odoo import api, fields, models
from odoo.exceptions import UserError


LIMITE_UNIDADES_ESTUDIANTE = 10


class SaleOrder(models.Model):
    _inherit = "sale.order"

    tipo_cliente = fields.Selection(
        related="partner_id.tipo_cliente", string="Tipo de cliente"
    )
    convenio_id = fields.Many2one(
        "tienda.convenio",
        string="Convenio",
        compute="_compute_convenio_id",
        store=True,
        readonly=False,
        domain="[('tipo_cliente', '=', tipo_cliente)]",
    )
    convenio_aplicado = fields.Boolean(
        string="Convenio aplicado", readonly=True, copy=False
    )
    monto_ahorro = fields.Monetary(
        string="Ahorro por convenio",
        compute="_compute_monto_ahorro",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("partner_id", "date_order", "partner_id.tipo_cliente")
    def _compute_convenio_id(self):
        Convenio = self.env["tienda.convenio"]
        for order in self:
            fecha = (order.date_order or fields.Datetime.now()).date()
            order.convenio_id = Convenio.search(
                [
                    ("tipo_cliente", "=", order.partner_id.tipo_cliente),
                    ("fecha_inicio", "<=", fecha),
                    "|",
                    ("fecha_fin", "=", False),
                    ("fecha_fin", ">=", fecha),
                ],
                order="fecha_inicio desc, id desc",
                limit=1,
            )

    @api.depends(
        "order_line.price_unit",
        "order_line.product_uom_qty",
        "order_line.discount",
        "order_line.display_type",
    )
    def _compute_monto_ahorro(self):
        for order in self:
            order.monto_ahorro = sum(
                line.price_unit * line.product_uom_qty * line.discount / 100
                for line in order.order_line
                if not line.display_type
            )

    def action_aplicar_convenio(self):
        for order in self:
            if order.state not in ("draft", "sent"):
                raise UserError("Solo se puede aplicar un convenio a una cotizacion.")
            if not order.convenio_id:
                raise UserError("El pedido no tiene un convenio asignado.")
            lineas = order.order_line.filtered(lambda line: not line.display_type)
            lineas.write({"discount": order.convenio_id.porcentaje})
            order.convenio_aplicado = True
            order.message_post(
                body=(
                    f"Se aplico el {order.convenio_id.name} con "
                    f"{order.convenio_id.porcentaje:g} % de descuento."
                )
            )
        return True

    def action_confirm(self):
        for order in self:
            if order.tipo_cliente == "estudiante":
                total_unidades = sum(
                    order.order_line.filtered(lambda line: not line.display_type).mapped(
                        "product_uom_qty"
                    )
                )
                if total_unidades > LIMITE_UNIDADES_ESTUDIANTE:
                    raise UserError(
                        "Los estudiantes pueden confirmar como maximo "
                        f"{LIMITE_UNIDADES_ESTUDIANTE} unidades por pedido. "
                        f"Este pedido contiene {total_unidades:g}."
                    )
        return super().action_confirm()
