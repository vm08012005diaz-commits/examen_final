from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestTiendaUnicah(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.student = cls.env["res.partner"].create({
            "name": "Estudiante Prueba", "tipo_cliente": "estudiante",
            "numero_cuenta": "0801200012", "carrera": "Ingenieria",
        })
        cls.product = cls.env["product.product"].create({"name": "Libro", "list_price": 100})

    def test_student_account_requires_ten_digits(self):
        with self.assertRaises(ValidationError):
            self.student.numero_cuenta = "12345678"

    def test_convenio_limits(self):
        with self.assertRaises(ValidationError):
            self.env["tienda.convenio"].create({
                "name": "Invalido", "tipo_cliente": "estudiante", "porcentaje": 50,
            })

    def test_apply_convenio_and_compute_saving(self):
        order = self.env["sale.order"].create({
            "partner_id": self.student.id,
            "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 2,
                                    "price_unit": 100})],
        })
        self.assertEqual(order.convenio_id.porcentaje, 15)
        order.action_aplicar_convenio()
        self.assertEqual(order.order_line.discount, 15)
        self.assertEqual(order.monto_ahorro, 30)

    def test_student_unit_limit(self):
        order = self.env["sale.order"].create({
            "partner_id": self.student.id,
            "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 12})],
        })
        with self.assertRaises(UserError):
            order.action_confirm()
