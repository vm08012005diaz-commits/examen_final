from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    reserva_aula_ids = fields.One2many(
        "unicah.aula.reserva", "solicitante_id", string="Reservas de aulas"
    )
    reserva_aula_count = fields.Integer(
        string="Reservas", compute="_compute_reserva_aula_count"
    )

    def _compute_reserva_aula_count(self):
        data = self.env["unicah.aula.reserva"]._read_group(
            [("solicitante_id", "in", self.ids)], ["solicitante_id"], ["__count"]
        )
        counts = {user.id: count for user, count in data}
        for user in self:
            user.reserva_aula_count = counts.get(user.id, 0)

    def action_ver_reservas_aula(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("unicah_aulas.aula_reserva_action")
        action["domain"] = [("solicitante_id", "=", self.id)]
        action["context"] = {"default_solicitante_id": self.id}
        return action
