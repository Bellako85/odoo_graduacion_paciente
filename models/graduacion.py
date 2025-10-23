from odoo import models, fields, api
from odoo.exceptions import ValidationError

class GraduacionPaciente(models.Model):
    _name = 'optica.graduacion'
    _description = 'Graduación de Paciente'
    _rec_name = 'paciente_id'
    _order = 'fecha desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    paciente_id = fields.Many2one(
        'res.partner',
        string='Paciente',
        required=True,
        domain=[('is_company', '=', False)],
        ondelete='restrict',
        index=True,
    )
    fecha = fields.Date(string='Fecha de evaluación', default=fields.Date.context_today)
    profesional = fields.Many2one('res.users', string='Optometrista', default=lambda self: self.env.user)

    # ✅ CAMPOS DE GRADUACIÓN
    ojo_derecho_esfera = fields.Float(string='OD Esfera', digits=(8, 2))
    ojo_derecho_cilindro = fields.Float(string='OD Cilindro', digits=(8, 2))
    ojo_derecho_eje = fields.Integer(string='OD Eje')
    ojo_derecho_av = fields.Char(string='OD AV')

    ojo_izquierdo_esfera = fields.Float(string='OI Esfera', digits=(8, 2))
    ojo_izquierdo_cilindro = fields.Float(string='OI Cilindro', digits=(8, 2))
    ojo_izquierdo_eje = fields.Integer(string='OI Eje')
    ojo_izquierdo_av = fields.Char(string='OI AV')

    adicion = fields.Float(string='Adición', digits=(8, 2))
    distancia_nasopupilar_od = fields.Float(string='Distancia Nasopupilar OD', digits=(8, 2))
    distancia_nasopupilar_oi = fields.Float(string='Distancia Nasopupilar OI', digits=(8, 2))
    distancia_interpupilar = fields.Float(string='Distancia Interpupilar', digits=(8, 2))
    altura_centro_optico = fields.Float(string='Altura CO', digits=(8, 2))
    
    tipo_lente = fields.Selection([
        ('monofocal', 'Monofocal'),
        ('bifocal', 'Bifocal'),
        ('progresivo', 'Progresivo'),
    ], string='Tipo de Lente')

    diagnostico = fields.Selection([
        ('miopia', 'Miopía'),
        ('hipermetropia', 'Hipermetropía'),
        ('astigmatismo', 'Astigmatismo'),
        ('astigmatismo_miopico', 'Astigmatismo Miópico'),
        ('astigmatismo_hipermetropico', 'Astigmatismo Hipermetrópico'),
        ('astigmatismo_simple', 'Astigmatismo Simple'),
        ('presbicia', 'Presbicia'),
    ], string='Diagnóstico')

    observaciones = fields.Text(string='Observaciones')

    # ✅ CAMPOS CALCULADOS PARA DIAGNÓSTICO AUTOMÁTICO
    diagnostico_od_detallado = fields.Char(
        string='Diagnóstico OD Detallado', 
        compute='_compute_diagnostico_automatico',
        store=True
    )
    diagnostico_oi_detallado = fields.Char(
        string='Diagnóstico OI Detallado', 
        compute='_compute_diagnostico_automatico',
        store=True
    )
    orientacion_od = fields.Char(
        string='Orientación OD', 
        compute='_compute_diagnostico_automatico',
        store=True
    )
    orientacion_oi = fields.Char(
        string='Orientación OI', 
        compute='_compute_diagnostico_automatico',
        store=True
    )
    formacion_focos_od = fields.Char(
        string='Formación Focos OD', 
        compute='_compute_diagnostico_automatico',
        store=True
    )
    formacion_focos_oi = fields.Char(
        string='Formación Focos OI', 
        compute='_compute_diagnostico_automatico',
        store=True
    )

    # ✅ CAMPOS PARA SERIES RECOMENDADAS
    serie_recomendada_od = fields.Char(
        string='Serie OD', 
        compute='_compute_series_automaticas',
        store=True
    )
    serie_recomendada_oi = fields.Char(
        string='Serie OI', 
        compute='_compute_series_automaticas',
        store=True
    )

    # ✅ CAMPOS PARA TRANSPOSICIÓN
    od_esfera_trans = fields.Float(string='OD Esf Trans', compute='_compute_transposicion')
    od_cilindro_trans = fields.Float(string='OD Cil Trans', compute='_compute_transposicion')
    od_eje_trans = fields.Integer(string='OD Eje Trans', compute='_compute_transposicion')
    oi_esfera_trans = fields.Float(string='OI Esf Trans', compute='_compute_transposicion')
    oi_cilindro_trans = fields.Float(string='OI Cil Trans', compute='_compute_transposicion')
    oi_eje_trans = fields.Integer(string='OI Eje Trans', compute='_compute_transposicion')

    # ✅ CONFIGURACIÓN DE SERIES
    SERIES_CONFIG = {
        'RX1': {
            'nombre': 'Primera Serie',
            'rangos': {
                'esfera': {'min': -4.00, 'max': 4.00},
                'cilindro': {'min': -2.00, 'max': 2.00},
                'adicion': {'min': 0.00, 'max': 0.00}
            }
        },
        'RX2': {
            'nombre': 'Segunda Serie',
            'rangos': {
                'esfera': {'min': -6.00, 'max': 6.00},
                'cilindro': {'min': -4.00, 'max': 4.00},
                'adicion': {'min': 0.00, 'max': 2.50}
            }
        },
        'RX3': {
            'nombre': 'Tercera Serie', 
            'rangos': {
                'esfera': {'min': -20.00, 'max': 20.00},
                'cilindro': {'min': -6.00, 'max': 6.00},
                'adicion': {'min': 0.00, 'max': 3.50}
            }
        }
    }

    @api.constrains('ojo_derecho_eje', 'ojo_izquierdo_eje')
    def _check_valores(self):
        for rec in self:
            if rec.ojo_derecho_eje and not (0 <= rec.ojo_derecho_eje <= 180):
                raise ValidationError('El eje del ojo derecho debe estar entre 0 y 180.')
            if rec.ojo_izquierdo_eje and not (0 <= rec.ojo_izquierdo_eje <= 180):
                raise ValidationError('El eje del ojo izquierdo debe estar entre 0 y 180.')

    # ✅ DIAGNÓSTICO AUTOMÁTICO
    @api.depends('ojo_derecho_esfera', 'ojo_derecho_cilindro', 'ojo_derecho_eje',
                 'ojo_izquierdo_esfera', 'ojo_izquierdo_cilindro', 'ojo_izquierdo_eje')
    def _compute_diagnostico_automatico(self):
        """Calcula el diagnóstico automático para cada ojo"""
        for record in self:
            # Diagnóstico OD
            diag_od = record._analizar_astigmatismo_ojo(
                record.ojo_derecho_esfera, record.ojo_derecho_cilindro, record.ojo_derecho_eje, 'OD'
            )
            record.diagnostico_od_detallado = diag_od['mensaje']
            record.orientacion_od = diag_od['orientacion']
            record.formacion_focos_od = diag_od['formacion_focos']
            
            # Diagnóstico OI
            diag_oi = record._analizar_astigmatismo_ojo(
                record.ojo_izquierdo_esfera, record.ojo_izquierdo_cilindro, record.ojo_izquierdo_eje, 'OI'
            )
            record.diagnostico_oi_detallado = diag_oi['mensaje']
            record.orientacion_oi = diag_oi['orientacion']
            record.formacion_focos_oi = diag_oi['formacion_focos']

    # ✅ SERIES AUTOMÁTICAS
    @api.depends('ojo_derecho_esfera', 'ojo_derecho_cilindro', 'adicion',
                 'ojo_izquierdo_esfera', 'ojo_izquierdo_cilindro', 'adicion')
    def _compute_series_automaticas(self):
        """Determina las series automáticamente según los rangos"""
        for record in self:
            # Serie para OD
            serie_od = record._determinar_serie_ojo(
                record.ojo_derecho_esfera, record.ojo_derecho_cilindro, record.adicion
            )
            record.serie_recomendada_od = serie_od
            
            # Serie para OI
            serie_oi = record._determinar_serie_ojo(
                record.ojo_izquierdo_esfera, record.ojo_izquierdo_cilindro, record.adicion
            )
            record.serie_recomendada_oi = serie_oi

    # ✅ TRANSPOSICIÓN AUTOMÁTICA
    @api.depends('ojo_derecho_esfera', 'ojo_derecho_cilindro', 'ojo_derecho_eje',
                 'ojo_izquierdo_esfera', 'ojo_izquierdo_cilindro', 'ojo_izquierdo_eje')
    def _compute_transposicion(self):
        """Calcula la transposición de lentes"""
        for record in self:
            # Transposición OD
            trans_od = record._transponer_ojo(
                record.ojo_derecho_esfera, record.ojo_derecho_cilindro, record.ojo_derecho_eje
            )
            record.od_esfera_trans = trans_od['esfera']
            record.od_cilindro_trans = trans_od['cilindro']
            record.od_eje_trans = trans_od['eje']
            
            # Transposición OI
            trans_oi = record._transponer_ojo(
                record.ojo_izquierdo_esfera, record.ojo_izquierdo_cilindro, record.ojo_izquierdo_eje
            )
            record.oi_esfera_trans = trans_oi['esfera']
            record.oi_cilindro_trans = trans_oi['cilindro']
            record.oi_eje_trans = trans_oi['eje']

    # ✅ MÉTODOS DE DIAGNÓSTICO
    def _analizar_astigmatismo_ojo(self, esfera, cilindro, eje, lado):
        """Analiza el tipo de astigmatismo para un ojo"""
        if cilindro == 0:
            return self._diagnosticar_esferico(esfera, lado)
        
        diagnostico = self._determinar_tipo_astigmatismo(esfera, cilindro)
        orientacion = self._determinar_orientacion_eje(eje)
        
        return {
            'tipo': diagnostico['tipo'],
            'subtipo': diagnostico['subtipo'],
            'formacion_focos': diagnostico['formacion_focos'],
            'orientacion': orientacion,
            'mensaje': f"{diagnostico['tipo']} ({diagnostico['subtipo']})",
            'esfera': esfera,
            'cilindro': cilindro,
            'eje': eje
        }

    def _determinar_tipo_astigmatismo(self, esfera, cilindro):
        """Determina el tipo específico de astigmatismo según criterios clínicos"""
        abs_esfera = abs(esfera)
        abs_cilindro = abs(cilindro)
        
        # ASTIGMATISMO HIPERMETRÓPICO SIMPLE (AHS)
        if (esfera == 0 and cilindro > 0) or \
           (esfera > 0 and abs_esfera == abs_cilindro and cilindro < 0):
            return {
                'tipo': 'Astigmatismo Hipermetrópico Simple',
                'subtipo': 'AHS',
                'formacion_focos': 'Un foco en retina, otro detrás de retina'
            }
        
        # ASTIGMATISMO MIÓPICO SIMPLE (AMS)
        if (esfera == 0 and cilindro < 0) or \
           (esfera < 0 and abs_esfera == abs_cilindro and cilindro > 0):
            return {
                'tipo': 'Astigmatismo Miópico Simple',
                'subtipo': 'AMS', 
                'formacion_focos': 'Un foco en retina, otro delante de retina'
            }
        
        # ASTIGMATISMO HIPERMETRÓPICO COMPUESTO (AHC)
        if esfera > 0 and (
            (cilindro > 0) or
            (cilindro < 0 and abs_cilindro < esfera)
        ):
            return {
                'tipo': 'Astigmatismo Hipermetrópico Compuesto',
                'subtipo': 'AHC',
                'formacion_focos': 'Ambos focos detrás de retina'
            }
        
        # ASTIGMATISMO MIÓPICO COMPUESTO (AMC)
        if esfera < 0 and (
            (cilindro < 0) or
            (cilindro > 0 and cilindro < abs_esfera)
        ):
            return {
                'tipo': 'Astigmatismo Miópico Compuesto',
                'subtipo': 'AMC',
                'formacion_focos': 'Ambos focos delante de retina'
            }
        
        # ASTIGMATISMO MIXTO (AM)
        if (esfera > 0 and cilindro < 0 and abs_cilindro > esfera) or \
           (esfera < 0 and cilindro > 0 and cilindro > abs_esfera):
            return {
                'tipo': 'Astigmatismo Mixto',
                'subtipo': 'AM',
                'formacion_focos': 'Un foco delante y otro detrás de retina'
            }
        
        return {
            'tipo': 'Astigmatismo',
            'subtipo': 'Indeterminado',
            'formacion_focos': 'Formación de focos no determinada'
        }

    def _diagnosticar_esferico(self, esfera, lado):
        if esfera == 0:
            return {
                'mensaje': "Emétrope (0.00)",
                'orientacion': 'N/A',
                'formacion_focos': 'N/A'
            }
        elif esfera > 0:
            return {
                'mensaje': f"Hipermetropía Simple {esfera:.2f}D",
                'orientacion': 'N/A',
                'formacion_focos': 'Foco detrás de retina'
            }
        else:
            return {
                'mensaje': f"Miopía Simple {abs(esfera):.2f}D", 
                'orientacion': 'N/A',
                'formacion_focos': 'Foco delante de retina'
            }

    def _determinar_orientacion_eje(self, eje):
        if (0 <= eje <= 30) or (150 <= eje <= 180):
            return "Con la Regla"
        elif 60 <= eje <= 120:
            return "Contra la Regla"
        else:
            return "Oblicuo"

    def _determinar_serie_ojo(self, esfera, cilindro, adicion):
        for serie, config in self.SERIES_CONFIG.items():
            if self._es_graduacion_dentro_de_rango(esfera, cilindro, adicion, config['rangos']):
                return serie
        return 'RX3'

    def _es_graduacion_dentro_de_rango(self, esfera, cilindro, adicion, rangos):
        return (rangos['esfera']['min'] <= esfera <= rangos['esfera']['max'] and
                abs(cilindro) <= abs(rangos['cilindro']['max']) and
                rangos['adicion']['min'] <= adicion <= rangos['adicion']['max'])

    def _transponer_ojo(self, esfera, cilindro, eje):
        nueva_esfera = esfera + cilindro
        nuevo_cilindro = -cilindro
        nuevo_eje = eje + 90 if eje <= 90 else eje - 90
        
        return {
            'esfera': round(nueva_esfera, 2),
            'cilindro': round(nuevo_cilindro, 2),
            'eje': nuevo_eje
        }

    # ✅ ACCIONES ADICIONALES
    def action_calcular_distancia_vertice(self):
        """Calcula la distancia al vértice para lentes de contacto"""
        self.ensure_one()
        
        vertex_od = self._calcular_vertex_ojo(
            self.ojo_derecho_esfera, self.ojo_derecho_cilindro, self.ojo_derecho_eje
        )
        vertex_oi = self._calcular_vertex_ojo(
            self.ojo_izquierdo_esfera, self.ojo_izquierdo_cilindro, self.ojo_izquierdo_eje
        )
        
        mensaje = f"""
        <b>🎯 Cálculo de Distancia al Vértice (12mm)</b><br/><br/>
        <b>OD:</b> {vertex_od['mensaje']}<br/>
        <b>OI:</b> {vertex_oi['mensaje']}<br/><br/>
        <i>Nota: Para cilindros mayores a 4.00D se rcomienda RGP.</i>
        """
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cálculo de Distancia al Vértice',
                'message': mensaje,
                'type': 'info',
                'sticky': True,
            }
        }

    def _calcular_vertex_ojo(self, esfera, cilindro, eje, distancia=12):
        d_metros = distancia / 1000.0
        
        # Calcular vertex para la esfera
        esfera_contacto = self._calcular_potencia_vertex(esfera, d_metros)
        
        # Calcular vertex para el cilindro (si existe)
        cilindro_contacto = 0.0
        if cilindro != 0:
            potencia_esferica_equivalente = esfera + (cilindro / 2)
            potencia_cilindrica_vertex = self._calcular_potencia_vertex(potencia_esferica_equivalente, d_metros)
            cilindro_contacto = (potencia_cilindrica_vertex - esfera_contacto) * 2
        
        mensaje = f"Oftálmico: {esfera} {cilindro} x {eje} → Contacto: {esfera_contacto:.2f}"
        if cilindro != 0:
            mensaje += f" {cilindro_contacto:.2f} x {eje}"
        
        return {
            'oftalmico': {'esfera': esfera, 'cilindro': cilindro, 'eje': eje},
            'contacto': {
                'esfera': round(esfera_contacto * 4) / 4,
                'cilindro': round(cilindro_contacto * 4) / 4 if cilindro != 0 else 0.0,
                'eje': eje
            },
            'mensaje': mensaje
        }

    def _calcular_potencia_vertex(self, potencia, distancia):
        if potencia == 0:
            return 0.0
        potencia_contacto = potencia / (1 - distancia * potencia)
        return round(potencia_contacto, 2)

    def action_mostrar_notacion_bicilindrica(self):
        """Muestra la notación bicilíndrica"""
        self.ensure_one()
        
        bicil_od = self._calcular_notacion_bicilindrica(
            self.ojo_derecho_esfera, self.ojo_derecho_cilindro, self.ojo_derecho_eje
        )
        bicil_oi = self._calcular_notacion_bicilindrica(
            self.ojo_izquierdo_esfera, self.ojo_izquierdo_cilindro, self.ojo_izquierdo_eje
        )
        
        mensaje = f"""
        <b>📐 Notación Bicilíndrica</b><br/><br/>
        <b>OD:</b> {bicil_od}<br/>
        <b>OI:</b> {bicil_oi}
        """
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification', 
            'params': {
                'title': 'Notación Bicilíndrica',
                'message': mensaje,
                'type': 'info',
                'sticky': True,
            }
        }

    def _calcular_notacion_bicilindrica(self, esfera, cilindro, eje):
        meridiano1 = esfera
        meridiano2 = esfera + cilindro
        eje1 = eje
        eje2 = eje + 90 if eje <= 90 else eje - 90
        
        return f"{meridiano1:.2f} x {eje1}° / {meridiano2:.2f} x {eje2}°"

    def action_imprimir_historia_clinica(self):
        self.ensure_one()
        return self.env.ref('odoo_graduacion_paciente.action_report_graduacion_paciente').report_action(self)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    graduacion_ids = fields.One2many('optica.graduacion', 'paciente_id', string='Graduaciones')

def action_crear_cotizacion(self):
    """Crea una cotización desde la graduación"""
    self.ensure_one()
    
    cotizacion = self.env['optometria.cotizador'].create({
        'graduacion_id': self.id,
    })
    
    return {
        'type': 'ir.actions.act_window',
        'name': 'Cotizador',
        'res_model': 'optometria.cotizador',
        'res_id': cotizacion.id,
        'view_mode': 'form',
        'target': 'current',
    }
