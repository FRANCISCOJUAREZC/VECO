# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import TransactionCase


class TestSaleDoubleValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_salemanager = cls.env.ref("sales_team.group_sale_manager")
        group_salesman = cls.env.ref("sales_team.group_sale_salesman")
        group_employee = cls.env.ref("base.group_user")

        cls.user_manager = cls.env["res.users"].create({
            "name": "Test Manager SDV",
            "login": "test_manager_sdv",
            "groups_id": [(6, 0, [group_salemanager.id, group_employee.id])],
        })
        cls.user_employee = cls.env["res.users"].create({
            "name": "Test Employee SDV",
            "login": "test_employee_sdv",
            "groups_id": [(6, 0, [group_salesman.id, group_employee.id])],
        })

        cls.partner = cls.env.ref("base.res_partner_1")

        cls.product_map = {
            "test": cls.env["product.product"].create({
                "name": "Test Product SDV",
                "list_price": 100.0,
                "type": "service",
            })
        }

    def _make_order_lines(self):
        return [
            (0, 0, {
                "name": p.name,
                "product_id": p.id,
                "product_uom_qty": 2,
                "product_uom": p.uom_id.id,
                "price_unit": p.list_price,
            })
            for p in self.product_map.values()
        ]

    def test_one_step(self):
        self.user_employee.company_id.sudo().so_double_validation = "one_step"
        so = (
            self.env["sale.order"]
            .with_user(self.user_employee)
            .create({
                "partner_id": self.partner.id,
                "order_line": self._make_order_lines(),
            })
        )
        self.assertEqual(so.state, "draft")

    def test_two_steps_under_limit(self):
        self.user_employee.company_id.sudo().so_double_validation = "two_step"
        so = (
            self.env["sale.order"]
            .with_user(self.user_employee)
            .create({
                "partner_id": self.partner.id,
                "order_line": self._make_order_lines(),
            })
        )
        self.assertEqual(so.state, "draft")

    def test_two_steps_manager(self):
        self.user_employee.company_id.sudo().so_double_validation = "two_step"
        self.user_employee.company_id.sudo().so_double_validation_amount = 10
        so = (
            self.env["sale.order"]
            .with_user(self.user_manager)
            .create({
                "partner_id": self.partner.id,
                "order_line": self._make_order_lines(),
            })
        )
        self.assertEqual(so.state, "draft")

    def test_two_steps_limit(self):
        self.user_employee.company_id.sudo().so_double_validation = "two_step"
        self.user_employee.company_id.sudo().so_double_validation_amount = sum(
            2 * p.list_price for p in self.product_map.values()
        )
        so = (
            self.env["sale.order"]
            .with_user(self.user_employee)
            .create({
                "partner_id": self.partner.id,
                "order_line": self._make_order_lines(),
            })
        )
        self.assertEqual(so.state, "to_approve")

    def test_two_steps_above_limit(self):
        self.user_employee.company_id.sudo().so_double_validation = "two_step"
        self.user_employee.company_id.sudo().so_double_validation_amount = 10
        so = (
            self.env["sale.order"]
            .with_user(self.user_employee)
            .create({
                "partner_id": self.partner.id,
                "order_line": self._make_order_lines(),
            })
        )
        self.assertEqual(so.state, "to_approve")
        so.with_user(self.user_manager).action_approve()
        self.assertEqual(so.state, "draft")
