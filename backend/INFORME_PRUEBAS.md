CARATULA
Nombre del proyecto: FinGest - Sistema de Gestion Financiera
Integrantes: (Completar)
Fecha: 03/05/2026
Curso: (Completar)
Docente: (Completar)

PROPOSITO DEL TRABAJO
Ampliar las pruebas del proyecto grupal real aplicando los cuatro niveles de prueba (unitario, integracion, sistema y aceptacion) y documentar su relacion con el modelo en V del desarrollo de software. El proyecto ya cuenta con pruebas unitarias del trabajo anterior; en este informe se agregan los niveles superiores.

1. DESCRIPCION DEL PROYECTO (1/2 pagina)
Nombre del proyecto: FinGest - Sistema de Gestion Financiera
Tecnologias usadas:
- Lenguaje: Python 3.12.7
- Framework: Django 5.2
- Base de datos: PostgreSQL (SQLite en desarrollo)
- Frontend: HTML, CSS, JavaScript, Bootstrap/Tailwind
- Reportes: ReportLab, openpyxl
Breve descripcion funcional:
FinGest es una plataforma web de gestion y educacion financiera. Permite registrar ingresos y gastos, administrar cuentas y subcuentas, crear metas de ahorro, generar reportes financieros y recibir alertas y notificaciones. Esta orientada a usuarios que necesitan controlar su economia personal y mejorar su alfabetizacion financiera.
Pruebas unitarias existentes (trabajo anterior):
- Validaciones y logica de modelos y formularios de usuarios, cuentas, movimientos y metas de ahorro.

2. PRUEBAS DE INTEGRACION (1.5 paginas)
Objetivo: Validar la comunicacion entre dos o mas componentes del proyecto.

INTERACCION 1
Tabla de caso de prueba
Campo | Valor
Nombre de la prueba | INT-01: Movimiento financiero -> Notificacion
Componentes que interactuan | gestion_financiera_basica (Movimiento) -> alertas_notificaciones (Notificacion)
Descripcion | Verificar que al registrar un movimiento financiero se crea una notificacion para el usuario.
Precondiciones | Usuario autenticado, cuenta activa, tipo de notificacion "movimiento_financiero" habilitado.
Datos de prueba | {"nombre":"Ingreso de prueba","tipo":"ingreso","monto":250.00}
Resultado esperado | Se crea una notificacion asociada al movimiento con datos adicionales (movimiento_id).
Herramienta sugerida | Django TestCase (tests_integration.py)
Anexo | Codigo en gestion_financiera_basica/tests_integration.py

INTERACCION 2
Tabla de caso de prueba
Campo | Valor
Nombre de la prueba | INT-02: Reporte basado en movimientos
Componentes que interactuan | analisis_reportes (Reporte) -> gestion_financiera_basica (Movimiento)
Descripcion | Verificar que al generar un reporte de ingresos vs egresos se usan los movimientos del periodo.
Precondiciones | Usuario autenticado con movimientos registrados.
Datos de prueba | {"tipo_reporte":"ingresos_egresos","fecha_inicio":"2026-05-01","fecha_fin":"2026-05-03"}
Resultado esperado | Se crea un reporte con datos json que incluyen labels, ingresos y gastos.
Herramienta sugerida | Django TestCase (tests_integration.py)
Anexo | Codigo en analisis_reportes/tests_integration.py

3. PRUEBAS DE SISTEMA (1.5 paginas)
Objetivo: Validar un flujo completo del sistema, de principio a fin.

FLUJO 1
Tabla de caso de prueba
Campo | Valor
ID del caso | SYS-01
Nombre del flujo | Registrar ingreso y visualizar dashboard
Pasos | 1) Usuario inicia sesion. 2) Registra un ingreso en una cuenta. 3) El sistema actualiza el saldo. 4) El usuario accede al dashboard.
Resultado esperado | Movimiento registrado, saldo actualizado y dashboard carga sin errores.
Prioridad | Alta
Anexo | Evidencia en core/tests_system.py

FLUJO 2
Tabla de caso de prueba
Campo | Valor
ID del caso | SYS-02
Nombre del flujo | Generar y ver reporte financiero
Pasos | 1) Usuario inicia sesion. 2) Genera un reporte de ingresos vs egresos. 3) El sistema guarda el reporte. 4) El usuario visualiza el reporte.
Resultado esperado | Reporte creado y vista de reporte renderiza correctamente.
Prioridad | Media
Anexo | Evidencia en core/tests_system.py

4. PRUEBAS DE ACEPTACION (1 pagina)
Objetivo: Verificar que el sistema cumple con las necesidades del negocio.

Escenario: Registro de ingreso actualiza balance
Given el usuario esta autenticado y tiene una cuenta activa
When registra un ingreso de 250.00 en la cuenta principal
Then el saldo de la cuenta aumenta en 250.00
And el dashboard muestra el nuevo total
Como se prueba: Manual (interfaz web) o automatizada E2E.

Escenario: Generacion de reporte de ingresos vs egresos
Given el usuario tiene movimientos registrados en el periodo
When solicita un reporte de ingresos vs egresos
Then el sistema genera el reporte
And permite visualizar o exportar el archivo
Como se prueba: Manual (descarga PDF/Excel) o automatizada E2E.

5. MODELO EN V APLICADO AL PROYECTO (1 pagina)
Diagrama (modelo en V):

REQUISITOS/HU  ------------------------>  PRUEBAS DE ACEPTACION
  |                                               |
  v                                               v
ESPECIFICACION ------------------------>  PRUEBAS DE SISTEMA
  |                                               |
  v                                               v
DISENO        ------------------------>  PRUEBAS DE INTEGRACION
  |                                               |
  v                                               v
CODIFICACION  ------------------------>  PRUEBAS UNITARIAS (ya tienen)

Explicacion aplicada a FinGest:
- Requisitos/HU: necesidades del usuario (gestionar ingresos, gastos, metas y reportes). Se validan con pruebas de aceptacion.
- Especificacion: flujos completos (registro de movimientos, generacion de reportes). Se validan con pruebas de sistema.
- Diseno: interaccion entre modulos (movimientos y notificaciones, movimientos y reportes). Se validan con pruebas de integracion.
- Codificacion: metodos de modelos, validaciones y formularios. Se validan con pruebas unitarias existentes.

6. CONCLUSIONES (1/2 pagina)
1) Nivel mas dificil: pruebas de sistema, porque requieren orquestar varios pasos reales con datos coherentes.
2) Cascada vs agil: en cascada las pruebas se planifican al final con documentacion fija; en agil se automatizan por iteracion y se ajustan con feedback continuo.
3) Aprendizajes: la calidad se fortalece cuando cada fase del desarrollo tiene su nivel de prueba asociado; esto reduce errores y valida el valor de negocio.

ANEXOS (opcional)
- Capturas de ejecucion de pruebas.
- Fragmentos de codigo en archivos de tests.
