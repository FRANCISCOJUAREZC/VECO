# -*- coding: utf-8 -*-
# © 2021 Morwi Encoders Consulting SA DE CV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import traceback
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def unlink(self):
        if self:
            _logger.warning(
                "stock.move unlink called for IDs %s\n%s",
                self.ids,
                ''.join(traceback.format_stack()),
            )
        return super().unlink()
