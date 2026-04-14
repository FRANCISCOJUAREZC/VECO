# -*- coding: utf-8 -*-
# Migration: mark leave type xmlids as noupdate=True so _process_end
# does not attempt to delete records that are still referenced by hr_leave.
# These records were previously owned by nomina_cfdi_extras_ee but are now
# defined in nomina_cfdi_ee.


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_model_data
           SET noupdate = True
         WHERE module = 'nomina_cfdi_extras_ee'
           AND model  = 'hr.leave.type'
           AND name IN (
               'hr_holidays_status_fjc',
               'hr_holidays_status_fjs',
               'hr_holidays_status_fi',
               'hr_holidays_status_fr',
               'hr_holidays_status_vac',
               'hr_holidays_status_inc_rt',
               'hr_holidays_status_inc_eg',
               'hr_holidays_status_inc_mat',
               'hr_holidays_status_dfest',
               'hr_holidays_status_dfest3'
           )
    """)
