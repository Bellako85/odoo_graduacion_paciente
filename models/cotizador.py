# -*- coding: utf-8 -*-

from odoo import models, fields, api

class OptometriaCotizador(models.Model):
    _name = 'optometria.cotizador'
    _description = 'Cotizador de Lentes'
    _order = 'id desc'
    
    name = fields.Char(string='Número', required=True, copy=False, default='Nuevo', readonly=True)
    
    graduacion_id = fields.Many2one(
        'optica.graduacion',
        string='Graduación',
        required=True,
        help='Graduación del paciente'
    )
    
    paciente_id = fields.Many2one(
        related='graduacion_id.paciente_id',
        string='Paciente',
        store=True,
        readonly=True
    )
    
    fecha = fields.Date(string='Fecha', default=fields.Date.today, required=True)
    
    # Filtros opcionales
    laboratorio_ids = fields.Many2many(
        'optometria.laboratorio',
        string='Laboratorios',
        help='Dejar vacío para buscar en todos'
    )
    
    tipo_lente_buscar = fields.Selection([
        ('monofocal', 'Monofocal'),
        ('bifocal', 'Bifocal'),
        ('progresivo', 'Progresivo'),
    ], string='Tipo de Lente')
    
    material_buscar = fields.Selection([
        ('cr39', 'CR39'),
        ('policarbonato', 'Policarbonato'),
        ('high_index', 'Alto Índice'),
        ('trivex', 'Trivex'),
    ], string='Material')
    
    # Resultados
    linea_ids = fields.One2many('optometria.cotizador.linea', 'cotizador_id', string='Productos Disponibles')
    total_productos_encontrados = fields.Integer(string='Total', compute='_compute_totales')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('cotizado', 'Cotizado'),
    ], default='borrador', string='Estado')
    
    @api.depends('linea_ids')
    def _compute_totales(self):
        for record in self:
            record.total_productos_encontrados = len(record.linea_ids)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('optometria.cotizador') or 'Nuevo'
        return super().create(vals)
    
    def buscar_productos(self):
        """Motor de búsqueda inteligente"""
        self.ensure_one()
        self.linea_ids.unlink()
        
        # Construir dominio
        domain = [
            ('es_lente', '=', True),
            ('active', '=', True),
        ]
        
        # Filtro por serie (de la graduación)
        serie_od = self.graduacion_id.serie_recomendada_od
        serie_oi = self.graduacion_id.serie_recomendada_oi
        
        # Usar la serie más alta de ambos ojos
        serie_requerida = serie_oi if serie_oi > serie_od else serie_od
        
        if serie_requerida:
            domain.append(('serie_rx', '=', serie_requerida))
        
        # Filtro por laboratorios
        if self.laboratorio_ids:
            domain.append(('laboratorio_id', 'in', self.laboratorio_ids.ids))
        
        # Filtro por tipo de lente
        if self.tipo_lente_buscar:
            domain.append(('tipo_lente', '=', self.tipo_lente_buscar))
        
        # Filtro por material
        if self.material_buscar:
            domain.append(('material', '=', self.material_buscar))
        
        # Filtros de rangos de graduación
        if self.graduacion_id.ojo_derecho_esfera:
            domain.extend([
                ('esfera_min', '<=', self.graduacion_id.ojo_derecho_esfera),
                ('esfera_max', '>=', self.graduacion_id.ojo_derecho_esfera),
            ])
        
        if self.graduacion_id.ojo_izquierdo_esfera:
            domain.extend([
                ('esfera_min', '<=', self.graduacion_id.ojo_izquierdo_esfera),
                ('esfera_max', '>=', self.graduacion_id.ojo_izquierdo_esfera),
            ])
        
        if self.graduacion_id.ojo_derecho_cilindro:
            domain.extend([
                ('cilindro_min', '<=', self.graduacion_id.ojo_derecho_cilindro),
                ('cilindro_max', '>=', self.graduacion_id.ojo_derecho_cilindro),
            ])
        
        if self.graduacion_id.ojo_izquierdo_cilindro:
            domain.extend([
                ('cilindro_min', '<=', self.graduacion_id.ojo_izquierdo_cilindro),
                ('cilindro_max', '>=', self.graduacion_id.ojo_izquierdo_cilindro),
            ])
        
        # Buscar productos
        productos = self.env['product.product'].search(domain)
        
        # Crear líneas
        for producto in productos:
            self.env['optometria.cotizador.linea'].create({
                'cotizador_id': self.id,
                'producto_id': producto.id,
            })
        
        self.state = 'cotizado'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Búsqueda Completada',
                'message': f'Se encontraron {len(productos)} productos compatibles',
                'type': 'success',
                'sticky': False,
            }
        }


class OptometriaCotizadorLinea(models.Model):
    _name = 'optometria.cotizador.linea'
    _description = 'Línea de Cotización'
    _order = 'laboratorio_id, precio'
    
    cotizador_id = fields.Many2one('optometria.cotizador', required=True, ondelete='cascade')
    producto_id = fields.Many2one('product.product', string='Producto', required=True)
    
    # Campos relacionados
    laboratorio_id = fields.Many2one(
        related='producto_id.product_tmpl_id.laboratorio_id',
        string='Laboratorio',
        store=True
    )
    serie = fields.Selection(
        related='producto_id.product_tmpl_id.serie_rx',
        string='Serie',
        store=True
    )
    material = fields.Selection(
        related='producto_id.product_tmpl_id.material',
        string='Material',
        store=True
    )
    precio = fields.Float(related='producto_id.list_price', string='Precio', store=True)
    
    cantidad = fields.Integer(string='Cantidad', default=1)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    seleccionado = fields.Boolean(string='Seleccionar', default=False)
    
    @api.depends('cantidad', 'precio')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.cantidad * record.precio
