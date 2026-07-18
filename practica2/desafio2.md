# Práctica Calificada Individual N°2 – Pruebas Dinámicas

**Curso:** Pruebas de Software (IS04E103)
**Duración:** 1.5 horas (sesión de laboratorio)
**Modalidad:** Individual
**Entrega:** Informe individual (máx 3 páginas) vía Teams

---

## 1. Propósito de la práctica

El estudiante aplicará pruebas dinámicas sobre su proyecto grupal, ejecutando el software para validar su comportamiento real. A diferencia de las pruebas estáticas (donde se analiza el código sin ejecutarlo), las pruebas dinámicas requieren que el software esté en ejecución para observar el comportamiento del sistema y detectar errores de funcionalidad, rendimiento o seguridad que solo aparecen en condiciones reales.

**Objetivos específicos:**

- Ejecutar el software del proyecto grupal en un entorno de pruebas.
- Diseñar y ejecutar casos de prueba funcionales (positivos y negativos).
- Documentar defectos encontrados y proponer correcciones.
- Aplicar al menos una técnica de diseño de casos de prueba (partición de equivalencia, valores límite, tabla de decisión).

---

## 2. Requisitos previos

| Requisito | Descripción |
|---|---|
| Proyecto de software | Proyecto grupal con código fuente y entorno funcional |
| Entorno de ejecución | El sistema debe poder ejecutarse localmente (frontend, backend o ambos) |
| Herramientas | Postman (para APIs), navegador (para frontend), o herramientas de pruebas unitarias |
| Casos de prueba | Al menos 5 casos de prueba diseñados previamente |

---

## 3. Estructura de la práctica (1.5 horas)

| Tiempo | Actividad | Entregable parcial |
|---|---|---|
| 10 min | Preparación del entorno: ejecutar el proyecto, verificar que esté funcional | Captura del sistema en ejecución |
| 30 min | Diseño de casos de prueba (5 casos: 3 funcionales + 2 de límites/negativos) | Tabla de casos de prueba |
| 35 min | Ejecución de pruebas y registro de resultados | Registro de ejecución + capturas |
| 15 min | Análisis de resultados, reporte de defectos y conclusiones | Informe final |

---

## 4. Tipos de pruebas dinámicas a aplicar

Las pruebas dinámicas se ejecutan sobre el software en funcionamiento. Los tipos principales que se aplicarán en esta práctica son:

| Tipo de prueba | Descripción | Ejemplo en el proyecto |
|---|---|---|
| Pruebas funcionales | Verifican que cada función del sistema opere conforme a los requisitos establecidos | Probar que el registro de usuario guarda correctamente los datos |
| Pruebas de regresión | Verifican que cambios recientes no hayan roto funcionalidades existentes | Probar el login después de agregar una nueva funcionalidad |
| Pruebas de integración | Verifican que distintos módulos funcionen correctamente al interactuar | Probar que el módulo de pagos se comunica con el de inventario |

---

## 5. Técnicas de diseño de casos de prueba

Aplica al menos una de las siguientes técnicas para diseñar tus casos de prueba:

| Técnica | Descripción | Ejemplo |
|---|---|---|
| Partición de equivalencia | Dividir los datos de entrada en grupos donde el sistema se comporta igual y probar un valor representativo | Campo "edad": probar 17 (inválido bajo), 30 (válido), 66 (inválido alto) |
| Análisis de valores límite | Probar los valores en los bordes de cada partición | Edad permitida 18-65: probar 17, 18, 19, 64, 65, 66 |
| Tabla de decisión | Probar combinaciones de condiciones que producen resultados diferentes | Monto > 500 Y VIP → descuento 20%; Monto > 500 Y NO VIP → descuento 10% |

---

## 6. Formato del informe individual (aprox. 3 páginas .pdf)

### Carátula (1 página)

- Título: "Práctica Calificada – Pruebas Dinámicas"
- Nombre del estudiante
- Proyecto analizado
- Fecha

### Sección 1: Descripción del proyecto y entorno (½ página)

- Breve descripción del sistema (qué hace, tecnologías usadas).
- Entorno de pruebas: cómo se ejecutó el sistema (local, servidor, etc.).
- Captura de pantalla del sistema en ejecución.

### Sección 2: Casos de prueba diseñados (1 página)

Completar la siguiente tabla con al menos 5 casos de prueba:

| ID | Requisito | Técnica aplicada | Datos de entrada | Resultado esperado | Prioridad |
|---|---|---|---|---|---|
| TC-01 | | | | | Alta |
| TC-02 | | | | | Alta |
| TC-03 | | | | | Media |
| TC-04 | | | | | Media |
| TC-05 | | | | | Baja |

**Requisitos mínimos:**

- Al menos 3 casos funcionales (positivos)
- Al menos 2 casos de límites o negativos (validaciones, errores)

### Sección 3: Ejecución y resultados (½ página)

Completar la siguiente tabla:

| ID | Resultado real | ¿Coincide con esperado? | Defecto encontrado (si aplica) | Severidad (A/M/B) |
|---|---|---|---|---|
| TC-01 | | Sí/No | | |
| TC-02 | | Sí/No | | |
| TC-03 | | Sí/No | | |
| TC-04 | | Sí/No | | |
| TC-05 | | Sí/No | | |

**Incluir capturas de pantalla:**

- Evidencia de la ejecución de al menos 2 casos de prueba.
- Evidencia de algún defecto encontrado (si existe).

### Sección 4: Análisis y conclusiones (½ página)

- Resumen de hallazgos: ¿cuántos casos pasaron? ¿cuántos fallaron?
- Defectos encontrados: descripción, impacto y posible solución.
- Reflexión: ¿qué aprendió sobre la importancia de las pruebas dinámicas?

---

## 7. Herramientas sugeridas

Dependiendo del tipo de proyecto, el estudiante puede usar:

| Tipo de proyecto | Herramienta sugerida | Uso |
|---|---|---|
| API / Backend | Postman | Enviar solicitudes HTTP y validar respuestas |
| Frontend web | Navegador (Chrome DevTools) | Probar flujos de usuario, verificar peticiones |
| Aplicación móvil | Emulador + dispositivo físico | Probar interacciones y flujos completos |
| Pruebas unitarias | JUnit / pytest / Jest | Ejecutar pruebas existentes y verificar resultados |

**Nota:** Si el proyecto no tiene una interfaz gráfica funcional, se pueden ejecutar pruebas de API con Postman o pruebas unitarias con el framework correspondiente.