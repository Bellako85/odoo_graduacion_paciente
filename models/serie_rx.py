# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class OptometriaSerieRx(models.Model):
    _name = 'optometria.serie.rx'
    _description = 'Rangos de Series RX para Laboratorios'
    _order = 'nombre_serie, esfera_min'
    
    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True
    )
    
    nombre_serie = fields.Selection([
        ('RX1', 'RX1'),
        ('RX2', 'RX2'),
        ('RX3', 'RX3'),
    ], string='Serie', required=True, index=True)
    
    esfera_min = fields.Float(string='Esfera Mínima', digits=(8, 2), required=True)
    esfera_max = fields.Float(string='Esfera Máxima', digits=(8, 2), required=True)
    cilindro_min = fields.Float(string='Cilindro Mínimo', digits=(8, 2), required=True)
    cilindro_max = fields.Float(string='Cilindro Máximo', digits=(8, 2), required=True)
    activo = fields.Boolean(string='Activo', default=True)
    
    @api.depends('nombre_serie', 'esfera_min', 'esfera_max', 'cilindro_min', 'cilindro_max')
    def _compute_name(self):
        for record in self:
            record.name = (
                f"{record.nombre_serie}: "
                f"ESF {record.esfera_min:+.2f} a {record.esfera_max:+.2f} | "
                f"CIL {record.cilindro_min:+.2f} a {record.cilindro_max:+.2f}"
            )
