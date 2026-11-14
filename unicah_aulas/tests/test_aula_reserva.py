from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAulaReserva(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.aula = cls.env["resource.resource"].create({
            "name": "Aula 101", "resource_type": "material"
        })

    def test_duration_and_overlap(self):
        inicio = fields.Datetime.now()
        reserva = self.env["unicah.aula.reserva"].create({
            "name": "Examen", "aula_id": self.aula.id,
            "fecha_inicio": inicio, "fecha_fin": inicio + timedelta(hours=2),
            "proposito": "Examen parcial", "estado": "confirmada",
        })
        self.assertEqual(reserva.duracion_horas, 2)
        with self.assertRaises(ValidationError):
            self.env["unicah.aula.reserva"].create({
                "name": "Conflicto", "aula_id": self.aula.id,
                "fecha_inicio": inicio + timedelta(hours=1),
                "fecha_fin": inicio + timedelta(hours=3),
                "proposito": "Otra actividad", "estado": "confirmada",
            })
