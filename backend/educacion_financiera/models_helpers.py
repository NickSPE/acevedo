"""Clases helper para la app educacion_financiera"""


class TipObject:
    """Clase para estructurar consejos financieros"""
    
    CATEGORY_MAP = {
        'savings': '💰 Ahorros',
        'investment': '📈 Inversiones',
        'budget': '📊 Presupuesto',
        'debt': '💳 Deudas',
        'insurance': '🛡️ Seguros',
        'retirement': '🏖️ Jubilación'
    }
    
    PRIORITY_MAP = {
        'alta': 'Alta',
        'media': 'Media',
        'baja': 'Baja',
        'high': 'Alta',
        'medium': 'Media',
        'low': 'Baja'
    }
    
    def __init__(self, categoria, titulo, descripcion, prioridad, es_ai=False, link_externo=None, id=None):
        self.id = id or f"{categoria}_{hash(titulo) % 1000}"
        self.categoria = categoria
        self.titulo = titulo
        self.descripcion = descripcion
        self.prioridad = prioridad
        self.es_ai = es_ai
        self.link_externo = link_externo
    
    def get_categoria_display(self):
        """Retorna el nombre formateado de la categoría"""
        return self.CATEGORY_MAP.get(self.categoria, self.categoria.title())
    
    def get_prioridad_display(self):
        """Retorna el nombre formateado de la prioridad"""
        return self.PRIORITY_MAP.get(self.prioridad, self.prioridad.title())
