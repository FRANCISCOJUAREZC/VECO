# VECO — Odoo 19 Custom Modules

Repositorio de customizaciones para Morwi Encoders Consulting / VECO, corriendo sobre Odoo 19 Community + Enterprise.

---

## Índice

1. [Árbol de módulos](#árbol-de-módulos)
2. [Flujos de negocio principales](#flujos-de-negocio-principales)
   - [Fabricación y workorders](#fabricación-y-workorders)
   - [Contabilidad de mano de obra](#contabilidad-de-mano-de-obra)
   - [Reporte de costos MRP](#reporte-de-costos-mrp)
   - [Plan de producción](#plan-de-producción)
   - [Compras y solicitudes](#compras-y-solicitudes)
   - [Inventario y Kárdex](#inventario-y-kárdex)
   - [Nómina y CFDI nómina](#nómina-y-cfdi-nómina)
   - [Facturación electrónica CFDI](#facturación-electrónica-cfdi)
   - [CFDI Traslado con Carta Porte](#cfdi-traslado-con-carta-porte)
3. [Catálogo de módulos](#catálogo-de-módulos)
4. [Extensiones de modelos clave](#extensiones-de-modelos-clave)
5. [Compatibilidad Odoo 19 — campos y métodos renombrados](#compatibilidad-odoo-19)
6. [Dependencias entre módulos custom](#dependencias-entre-módulos-custom)

---

## Árbol de módulos

```
VECO/
├── account_move_line_stock_info      # Liga movimientos de stock a líneas contables
├── account_partner_budget            # Dimensión de partner en presupuestos
├── account_xunnel                    # Sincronización bancaria vía Xunnel API
├── auditlog                          # Trazabilidad de cambios en registros
├── bi_sql_editor                     # Vistas BI con SQL materializado
├── invoice_xunnel                    # Descarga de facturas del SAT vía Xunnel
├── l10n_mx_adenda_veco               # Nodo addenda OC en CFDI
├── l10n_mx_catalogos                 # Catálogos SAT (transporte, aduanas, etc.)
├── l10n_mx_edi_extended_ext          # Descripciones específicas para CE en CFDI
├── l10n_mx_traslado                  # CFDI Traslado + Carta Porte
├── mrp_account_cost_report           # Reporte de costos de fabricación
├── mrp_account_workorder             # Asientos de mano de obra (v1, legacy)
├── mrp_account_workorder_v2          # Asientos de mano de obra (v2, activo)
├── mrp_automatic_tracking            # Asignación automática de lotes en WO
├── mrp_production_plan               # Plan de producción integrado con ventas
├── nomina_cfdi_bancos                # Archivos de dispersión bancaria de nómina
├── nomina_cfdi_ee                    # Nómina electrónica CFDI v1.2 Enterprise
├── nomina_cfdi_extras_ee             # Préstamos, incapacidades, viáticos
├── nomina_cfdi_sbc                   # Cálculo quincenal de SBC
├── nomina_cfdi_sua                   # Exportación SUA/IDSE para IMSS
├── nomina_veco                       # Ajustes de nómina específicos de VECO
├── om_hr_payroll                     # Payroll Community base para Odoo 19
├── payroll_multicompany              # Filtros multiempresa en nómina
├── product_forecast_qty_report       # Reporte de cantidades pronosticadas
├── purchase_discount                 # Descuentos en líneas de OC
├── purchase_request                  # Solicitudes de compra con flujo de aprobación
├── report_xlsx                       # Framework base para reportes Excel
├── sale_double_validation            # Doble validación en órdenes de venta
├── sale_propagate_notes              # Copia notas de venta a OFs
├── stock_kardex_report               # Kárdex de inventario (PDF + Excel)
├── stock_mts_mto_rule                # Regla híbrida MTS+MTO
├── stock_no_negative                 # Previene stock negativo
├── stock_product_available_qty       # Disponible real excluyendo ubicaciones de producción
├── stock_quantity_history_location   # Historial de stock por ubicación y fecha
├── veco_customizations               # Customizaciones generales VECO (v1)
├── veco_customizations_2             # Customizaciones generales VECO (v2)
├── veco_security                     # Seguridad por filas en MRP y calidad
└── web_environment_ribbon            # Cinta visual de entorno (prod/stage/test)
```

---

## Flujos de negocio principales

### Fabricación y workorders

**Modelos involucrados:** `mrp.production`, `mrp.workorder`, `quality.check`, `stock.move`, `stock.move.line`

**Enterprise involucrado:** `mrp_workorder` (workorders), `quality_mrp` / `quality_control` (checks de calidad), `mrp_subcontracting`

```
mrp.production.action_confirm()
  └── veco_customizations/models/mrp_production.py:action_confirm()
        ├── (super) → mrp base confirm
        ├── (move_raw_ids | move_finished_ids)._action_confirm(merge=False)
        │     └── quality_mrp → quality_control → mrp_subcontracting → mrp → stock
        │           └── stock.rule.run() → procurement routing
        │                 ├── stock_mts_mto_rule._run_split_procurement()  [si regla MTS+MTO]
        │                 └── mrp.stock_rule._run_manufacture() → MO anidada.action_confirm()
        └── production.workorder_ids._action_confirm()
              └── mrp_workorder (enterprise): _action_confirm()
                    └── filtered(not cancel, no checks)._create_checks()
                          └── mrp_automatic_tracking/mrp_workorder.py:_create_checks()
                                ├── super() → crea quality checks para lotes/series
                                └── si NOT set_manual_tracking:
                                      rec.check_ids.unlink()   ← elimina checks automáticos
```

**Campo clave en `mrp.production`:**
- `set_manual_tracking` (Boolean) — si está activo, los operarios deben registrar lotes manualmente en workorders; si está desactivado, el módulo `mrp_automatic_tracking` elimina los quality checks y el sistema no pide lotes.

**`_generate_lot_ids` (mrp_automatic_tracking):**
- Si `set_manual_tracking` es False, omite la generación automática de IDs de lote.
- Si es True, delega a `super()` (enterprise).

---

### Contabilidad de mano de obra

**Módulo activo:** `mrp_account_workorder_v2`
**Módulo legacy (mantener pero no usar):** `mrp_account_workorder`

**Modelos:**
- `mrp.workcenter.productivity` — línea de tiempo de trabajo (pausa/inicio/fin)
- `account.move` — asiento contable generado
- `workforce.account.line` — distribución porcentual de cuentas por almacén

**Flujo:**

```
mrp.workcenter.productivity.create()  [operario marca inicio+fin]
  └── si date_start AND date_end → create_workforce_entry()
        ├── Obtiene workforce_account_ids del almacén del workcenter
        ├── _prepare_workforce_lines() → genera líneas contables con % distribución
        ├── AccountMove.create({journal, date, lines, ref=workorder.display_name})
        ├── workforce_entry_id = move.id
        └── move.action_post()

mrp.workcenter.productivity.write()
  └── si cambia date_start/date_end y contexto is_edition:
        ├── button_cancel() en asiento existente
        ├── write() nuevas líneas
        └── action_post()

mrp.workcenter.productivity.unlink()
  └── workforce_entry_id.button_cancel() + unlink()
```

**Configuración por almacén (`stock.warehouse`):**
- `workforce_cost_journal_id` — diario donde se registran asientos
- `workforce_account_ids` → `workforce.account.line`:
  - `account_id` — cuenta contable de costo
  - `percentage` — porcentaje asignado a esta cuenta

---

### Reporte de costos MRP

**Módulo:** `mrp_account_cost_report`
**Depende de:** `mrp_account_workorder_v2`, `mrp_workorder`, `mrp_account`, `sale`

**Campos calculados en `mrp.production`:**

| Campo | Descripción |
|---|---|
| `components_amount` | Suma de capas de valoración de componentes consumidos |
| `workforce_amount` | Suma de asientos de mano de obra (`mrp_timeline_id`) |
| `indirects_amount` | Costos indirectos imputados |
| `total_cost` | components + workforce + indirects |
| `unit_cost` | total_cost / qty_done |
| `qty_done` | `sum(finished_move_line_ids.mapped('quantity'))` — campo `quantity` en Odoo 17+ |
| `sale_amount` | Suma de `sale.order.line.price_subtotal` asociadas |

**Método `refresh_costs()`:** Recomputa costos del día actual. Llamado desde cron o manualmente.

**SQL en reporte:** `manufacture_cost_report.py` usa raw SQL sobre tablas `mrp_production`, `stock_valuation_layer`, `mrp_workcenter_productivity`.

---

### Plan de producción

**Módulo:** `mrp_production_plan`

**Modelos creados:**
- `mrp.production.plan.item` — fila del plan (1 por línea de venta × producto)
- `mrp.production.plan.subproduct.line` — subproductos en OFs de múltiples niveles

**Flujo `run_production_plan()`:**
1. Busca `sale.order.line` en el rango de fecha indicado
2. Correlaciona con `mrp.production` via `procurement_group_id` o `sale_id`
3. Calcula delays: `sales_time`, `plant_time`, `warehouse_delay`
4. Crea/actualiza `mrp.production.plan.item` con estado: `production`, `delivery`, `fully_delivered`

---

### Compras y solicitudes

**Módulo:** `purchase_request`

**Flujo:**
```
Necesidad de material (stock.move o demanda manual)
  └── purchase.request.create()
        ├── purchase.request.line (producto, cantidad, fecha requerida)
        └── flujo de aprobación → approved
              └── purchase.request.line._create_purchase_order()
                    ├── Crea purchase.order si no existe para proveedor
                    ├── Crea purchase.order.line con allocation
                    └── purchase.request.allocation (liga PR line ↔ PO line)

stock.rule._run_buy() [override en purchase_request]
  └── Si hay PR activa para el producto, reutiliza en lugar de crear PO directa
```

**Nota:** `qty_done` en `purchase.request.line` es un campo **custom** que mide cuánto se ha recibido contra la solicitud — no es `stock.move.line.quantity`.

**Módulo `purchase_discount`:** Agrega `discount` (Float) a `purchase.order.line` y `product.supplierinfo`. Calcula `price_unit` final después de descuento.

---

### Inventario y Kárdex

**Módulo:** `stock_kardex_report`

**Flujo del wizard:**
1. Usuario selecciona almacén/ubicación, producto(s), rango de fechas
2. `generate_report()`:
   - Query SQL de saldo inicial — columna `quantity` en `stock_move_line` (Odoo 17+)
   - Query SQL de movimientos — alias `sml.quantity`
   - Procesa `dictfetchall` con clave `'quantity'`
   - Crea registros `stock.kardex.report` con saldo acumulado en campo custom `qty_done`
3. Abre vista lista o genera PDF/XLSX

**Nota:** `stock.kardex.report.qty_done` es campo **custom** del reporte — no confundir con `stock.move.line.quantity`.

**Módulo `stock_mts_mto_rule`:**
- Agrega acción `split_procurement` en `stock.rule`
- `_run_split_procurement()`: si hay stock disponible usa MTS; el sobrante lo procesa como MTO (`_run_mto_action`)
- `_run_mto_action()` llama a la sub-regla MTO configurada en `mto_rule_id`

**Módulo `stock_product_available_qty`:**
- Override de `_get_domain_locations_new()` en `product.product`
- Excluye `sam_loc_id` (pre-producción) y `pbm_loc_id` (post-producción) del cálculo de disponible
- Evita que material en proceso cuente como disponible para nuevas ventas

---

### Nómina y CFDI nómina

**Stack completo:**
```
om_hr_payroll              ← base Community
  └── hr_payroll (EE)      ← Enterprise base
        └── nomina_cfdi_ee           ← CFDI v1.2 + firma PAC
              ├── nomina_cfdi_extras_ee    ← préstamos, incapacidades, viáticos
              │     ├── nomina_cfdi_sbc    ← SBC quincenal
              │     └── nomina_cfdi_sua    ← SUA/IDSE para IMSS
              ├── nomina_cfdi_bancos       ← dispersión bancaria
              └── nomina_veco              ← ajustes VECO
                    └── payroll_multicompany
```

**Modelos custom clave:**

| Modelo | Propósito |
|---|---|
| `employee_loan` | Préstamo al empleado con `installment_line` de pagos |
| `employee_loan_type` | Tipo de préstamo (cuenta contable, periodicidad) |
| `incapacidades_nomina` | Incapacidad IMSS con días y tipo |
| `faltas_nomina` | Faltas injustificadas por periodo |
| `viaticos_nomina` | Viáticos gravados/exentos |
| `dev_skip_installment` | Excepción de descuento de cuota en periodo |

**Flujo de nómina (`nomina_cfdi_extras_ee`):**
```
hr.payslip.action_payslip_done()
  ├── Aplica cuotas de préstamos activos (installment_line)
  ├── Aplica descuentos por faltas/incapacidades
  ├── Genera CFDI XML vía nomina_cfdi_ee
  ├── Timbra con PAC (Finkok / SW Sapien / SolucionFactible)
  └── Marca installment_line.is_paid = True

hr.payslip.action_payslip_cancel()
  ├── Cancela CFDI en PAC
  ├── moves.filtered(state == 'posted').button_cancel()
  └── payslip.installment_ids.write({'is_paid': False, 'payslip_id': None})
```

---

### Facturación electrónica CFDI

**`l10n_mx_adenda_veco`:**
- `account.move.action_add_addenda_oc()` — parsea CFDI XML firmado y añade nodo `<Addenda>` con datos de OC del cliente

**`l10n_mx_edi_extended_ext`:**
- Agrega `info_mercancias` en líneas de factura → `account.move.mercancias.info`
- Campos: Marca, Modelo, SubModelo, números de serie para complemento Comercio Exterior
- Override de `_l10n_mx_edi_add_invoice_cfdi_values()` para incluirlos en XML CE

**`veco_customizations_2` — pagos CFDI:**
- Override de `_l10n_mx_edi_cfdi_invoice_get_reconciled_payments_values()`
- Incluye entradas contables directas (banco/caja) como pagos CFDI, no solo `account.payment`

**`invoice_xunnel`:**
- Descarga CFDIs recibidos del SAT vía API Xunnel
- Crea `ir.attachment` + `documents.document` con el XML

---

### CFDI Traslado con Carta Porte

**Módulo:** `l10n_mx_traslado`
**Modelo principal:** `cfdi.traslado`

**Campos clave:**

| Grupo | Campos |
|---|---|
| Transporte | `tipo_transporte` (01=Autotransporte, 02=Marítimo, 03=Aéreo, 04=Ferroviario) |
| Autotransporte | `num_permiso_sct`, `config_vehicular`, `placa_vm`, `anio_modelo_vm`, `aseguradora_resp_civil` |
| Ubicaciones | `ubicaciones_ids` → `ccp.ubicaciones.line` (origen/destino, distancia, hora) |
| Figura de transporte | `figura_ids` → `ccp.figura.line` (operador, tipo figura, RFC, licencia) |
| Mercancías | `traslado_line_ids` → `cfdi.traslado.line` (producto, qty, unidad SAT, peso, peligroso) |
| Aduanas | `aduanera_ids` → `cfdi.aduanera.line`, `ccp.aduanero.line` |
| Estado | `state`: draft → valid → cancel |

**Flujo de timbrado:**
```
cfdi.traslado.action_cfdi_generate()
  ├── Construye payload JSON con to_json_carta_porte()
  │     ├── Distancia Haversine entre origen y destino
  │     ├── Datos de autotransporte, remolques, figuras
  │     └── Mercancías con claves SAT
  ├── Llama PAC (Finkok/SW/SolucionFactible) para firma
  ├── Almacena XML timbrado en ir.attachment
  ├── state = 'valid'
  └── Genera QR de verificación SAT

cfdi.traslado.action_cfdi_cancel()
  ├── Llama PAC para cancelación con motivo
  └── state = 'cancel'
```

---

## Catálogo de módulos

| Módulo | Propósito breve |
|---|---|
| `account_move_line_stock_info` | Liga stock moves a líneas contables |
| `account_partner_budget` | Partner en presupuestos analíticos |
| `account_xunnel` | Sincronización bancaria Xunnel |
| `auditlog` | Trazabilidad completa de cambios |
| `bi_sql_editor` | Reportes BI con SQL |
| `invoice_xunnel` | Descarga facturas SAT |
| `l10n_mx_adenda_veco` | Addenda OC en CFDI |
| `l10n_mx_catalogos` | Catálogos SAT |
| `l10n_mx_edi_extended_ext` | Descripciones CE en CFDI |
| `l10n_mx_traslado` | CFDI Traslado + Carta Porte |
| `mrp_account_cost_report` | Costos de fabricación |
| `mrp_account_workorder` | Asientos MO (v1, legacy) |
| `mrp_account_workorder_v2` | Asientos MO (v2, activo) |
| `mrp_automatic_tracking` | Tracking automático de lotes en WO |
| `mrp_production_plan` | Plan producción ↔ ventas |
| `nomina_cfdi_bancos` | Dispersión bancaria nómina |
| `nomina_cfdi_ee` | Nómina electrónica CFDI v1.2 |
| `nomina_cfdi_extras_ee` | Préstamos, incapacidades, viáticos |
| `nomina_cfdi_sbc` | SBC quincenal |
| `nomina_cfdi_sua` | SUA/IDSE para IMSS |
| `nomina_veco` | Ajustes nómina VECO |
| `om_hr_payroll` | Payroll Community base |
| `payroll_multicompany` | Multiempresa en nómina |
| `product_forecast_qty_report` | Pronóstico de stock |
| `purchase_discount` | Descuentos en OC |
| `purchase_request` | Solicitudes de compra |
| `report_xlsx` | Framework reportes Excel |
| `sale_double_validation` | Doble aprobación ventas |
| `sale_propagate_notes` | Notas venta → OF |
| `stock_kardex_report` | Kárdex de inventario |
| `stock_mts_mto_rule` | Regla MTS+MTO híbrida |
| `stock_no_negative` | Sin stock negativo |
| `stock_product_available_qty` | Disponible real (excluye prod) |
| `stock_quantity_history_location` | Historial stock por ubicación |
| `veco_customizations` | Customizaciones generales v1 |
| `veco_customizations_2` | Customizaciones generales v2 |
| `veco_security` | Seguridad filas MRP/calidad |
| `web_environment_ribbon` | Cinta indicadora de entorno |

---

## Extensiones de modelos clave

### `mrp.production`

| Módulo | Qué agrega |
|---|---|
| `mrp_automatic_tracking` | `set_manual_tracking` (Boolean) |
| `mrp_account_cost_report` | `components_amount`, `workforce_amount`, `indirects_amount`, `total_cost`, `unit_cost`, `qty_done`, `sale_amount`, `*_percentage` |
| `veco_customizations` | Override `action_confirm()` — confirma moves y workorders manualmente |
| `sale_propagate_notes` | Copia `note` de `sale.order` al crear OF |

### `mrp.workorder`

| Módulo | Qué agrega |
|---|---|
| `mrp_automatic_tracking` | Override `_create_checks()`, `_generate_lot_ids()` |
| `mrp_account_workorder_v2` | Asientos de mano de obra vía `mrp.workcenter.productivity` |

### `stock.move.line` — renombres Odoo 17+

| Campo antiguo (≤16) | Campo nuevo (17+/19) |
|---|---|
| `qty_done` | `quantity` |
| `product_uom_qty` | `reserved_uom_qty` |

### `account.move` — renombres Odoo 14+

| Método antiguo (≤13) | Método nuevo (14+/19) |
|---|---|
| `.post()` | `.action_post()` |

---

## Compatibilidad Odoo 19

Registro de bugs por campos/métodos eliminados que ya fueron corregidos:

| Archivo | Cambio |
|---|---|
| `mrp_automatic_tracking/models/mrp_workorder.py:21` | Eliminado `write({'is_last_step': True})` — campo no existe en v19 |
| `veco_customizations/models/mrp_production.py:131,134` | `sml.qty_done` → `sml.quantity` |
| `mrp_account_cost_report/models/mrp_production.py:210` | `.mapped('qty_done')` → `.mapped('quantity')` |
| `mrp_account_workorder/models/mrp_workorder.py:138,151` | `.post()` → `.action_post()` |
| `stock_kardex_report/wizard/stock_kardex_report_wizard.py:84,104,133,181,183` | Columna SQL `qty_done` → `quantity`; claves dict de `dictfetchall` actualizadas |

---

## Dependencias entre módulos custom

```
report_xlsx
  └── stock_kardex_report
  └── nomina_cfdi_extras_ee

om_hr_payroll
  └── nomina_cfdi_ee
        ├── nomina_cfdi_extras_ee
        │     ├── nomina_cfdi_sbc
        │     └── nomina_cfdi_sua
        ├── nomina_cfdi_bancos
        └── nomina_veco
              └── payroll_multicompany

stock_product_available_qty
  └── product_forecast_qty_report

purchase_request
  └── veco_customizations
  └── veco_customizations_2

mrp_account_workorder_v2
  └── mrp_account_cost_report

mrp_workorder (EE)
  └── mrp_automatic_tracking
  └── mrp_account_workorder
  └── mrp_account_workorder_v2
  └── mrp_account_cost_report

l10n_mx_catalogos
  └── l10n_mx_traslado

account_xunnel
  └── invoice_xunnel
```
