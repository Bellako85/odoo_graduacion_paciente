# -*- coding: utf-8 -*-

from odoo import models, fields

class OptometriaLaboratorio(models.Model):
    _name = 'optometria.laboratorio'
    _description = 'Laboratorios Proveedores de Lentes'
    _order = 'name'
    
    name = fields.Char(string='Nombre del Laboratorio', required=True)
    telefono = fields.Char(string='Teléfono')
    email = fields.Char(string='Email')
    dias_entrega = fields.Integer(string='Días de Entrega', default=5)
    activo = fields.Boolean(string='Activo', default=True)
    notas = fields.Text(string='Notas')
