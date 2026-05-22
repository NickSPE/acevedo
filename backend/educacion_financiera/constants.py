"""Datos base para consejos financieros"""

from .models_helpers import TipObject


# Consejos base pre-definidos por categoría
CONSEJOS_BASE = {
    'savings': [
        TipObject('savings', 'Automatiza tus Ahorros', 'Configura transferencias automáticas del 20% de tus ingresos a una cuenta separada el día que cobras.', 'high'),
        TipObject('savings', 'Regla del 50/30/20', 'Destina 50% para necesidades, 30% para deseos y 20% para ahorros e inversiones.', 'medium'),
        TipObject('savings', 'Fondo de Emergencia', 'Mantén al menos 3-6 meses de gastos en una cuenta de fácil acceso para emergencias.', 'high'),
    ],
    'investment': [
        TipObject('investment', 'Diversifica tu Portafolio', 'Invierte en diferentes tipos de activos (acciones, bonos, bienes raíces) para reducir riesgos.', 'high'),
        TipObject('investment', 'Inversión a Largo Plazo', 'El tiempo es tu mejor aliado. Invierte consistentemente y deja que el interés compuesto haga su magia.', 'medium'),
        TipObject('investment', 'Edúcate Antes de Invertir', 'Nunca inviertas en algo que no entiendes. Lee, estudia y consulta con expertos.', 'high'),
    ],
    'budget': [
        TipObject('budget', 'Rastrea Todos tus Gastos', 'Anota cada peso que gastas durante un mes para identificar patrones y áreas de mejora.', 'high'),
        TipObject('budget', 'Presupuesto Base Cero', 'Cada peso debe tener un propósito antes de gastarlo. Asigna todo tu ingreso a categorías específicas.', 'medium'),
        TipObject('budget', 'Revisa Mensualmente', 'Evalúa tu presupuesto cada mes y ajusta según tus necesidades y objetivos cambiantes.', 'medium'),
    ],
    'debt': [
        TipObject('debt', 'Método Avalancha de Deudas', 'Paga primero las deudas con mayor tasa de interés mientras mantienes pagos mínimos en otras.', 'high'),
        TipObject('debt', 'Evita Deudas de Consumo', 'No uses tarjetas de crédito para compras que no puedes pagar inmediatamente.', 'high'),
        TipObject('debt', 'Negocia con Acreedores', 'Si tienes problemas para pagar, contacta a tus acreedores para negociar planes de pago.', 'medium'),
    ],
    'insurance': [
        TipObject('insurance', 'Seguro de Vida', 'Si tienes dependientes, necesitas un seguro de vida equivalente a 10 veces tu ingreso anual.', 'high'),
        TipObject('insurance', 'Seguro de Salud', 'Un seguro médico puede protegerte de gastos catastróficos que podrían arruinar tus finanzas.', 'high'),
        TipObject('insurance', 'Revisa Coberturas Anualmente', 'Evalúa tus seguros cada año para asegurar que cubran tus necesidades actuales.', 'medium'),
    ],
    'retirement': [
        TipObject('retirement', 'Comienza Temprano', 'Incluso $50 mensuales a los 25 años valen más que $500 mensuales a los 45 por el interés compuesto.', 'high'),
        TipObject('retirement', 'Contribuye al Máximo', 'Si tu empleador ofrece plan de jubilación con aportación patronal, contribuye al menos hasta el límite del match.', 'high'),
        TipObject('retirement', 'Calcula tu Número', 'Determina cuánto necesitas para jubilarte cómodamente y trabaja hacia esa meta específica.', 'medium'),
    ]
}
