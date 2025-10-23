# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Clasificación óptica
    es_lente = fields.Boolean(string='Es Lente Oftálmica')
    laboratorio_id = fields.Many2one('optometria.laboratorio', string='Laboratorio')
    
    serie_rx = fields.Selection([
        ('RX1', 'RX1'),
        ('RX2', 'RX2'),
        ('RX3', 'RX3'),
    ], string='Serie RX')
    
    tipo_lente = fields.Selection([
        ('monofocal', 'Monofocal'),
        ('bifocal', 'Bifocal'),
        ('progresivo', 'Progresivo'),
    ], string='Tipo de Lente')
    
    material = fields.Selection([
        ('cr39', 'CR39'),
        ('policarbonato', 'Policarbonato'),
        ('high_index_1.60', 'Alto Índice 1.60'),
        ('high_index_1.67', 'Alto Índice 1.67'),
        ('trivex', 'Trivex'),
    ], string='Material')
    
    tipo_fabricacion = fields.Selection([
        ('terminado', 'Terminado (Stock)'),
        ('base_tallar', 'Base para Tallar'),
    ], string='Tipo de Fabricación')
    
    # Rangos de graduación que soporta
    esfera_min = fields.Float(string='Esfera Mínima', digits=(8, 2))
    esfera_max = fields.Float(string='Esfera Máxima', digits=(8, 2))
    cilindro_min = fields.Float(string='Cilindro Mínimo', digits=(8, 2))
    cilindro_max = fields.Float(string='Cilindro Máximo', digits=(8, 2))
    
    @api.constrains('esfera_min', 'esfera_max')
    def _check_rango_esfera(self):
        for record in self:
            if record.es_lente and record.esfera_min and record.esfera_max:
                if record.esfera_min > record.esfera_max:
                    raise ValidationError('La esfera mínima no puede ser mayor que la máxima')
    
    @api.constrains('cilindro_min', 'cilindro_max')
    def _check_rango_cilindro(self):
        for record in self:
            if record.es_lente and record.cilindro_min and record.cilindro_max:
                if record.cilindro_min > record.cilindro_max:
                    raise ValidationError('El cilindro mínimo no puede ser mayor que el máximo')
