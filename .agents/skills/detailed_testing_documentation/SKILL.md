---
name: detailed_testing_documentation
description: Guidelines for generating detailed testing documentation in LaTeX, ensuring blocks of code, image placeholders/references, descriptions, and contextual information are properly documented.
---

# Pautas para la Documentación Detallada de Pruebas

Este Skill define las directrices y estándares para redactar de forma exhaustiva, clara y estructurada cada una de las subsecciones del Plan de Pruebas en LaTeX, asegurando el uso correcto de bloques de código, imágenes y descripciones contextuales.

## Principios Fundamentales

1. **Proceder Paso a Paso (Poco a Poco)**:
   - No realizar cambios masivos sin alinear previamente con el usuario.
   - Detallar cada punto discutiendo su propósito funcional antes de escribir el código LaTeX correspondiente.

2. **Contextualización y Descripción**:
   - Cada sección debe iniciar con una introducción breve pero clara que explique el *por qué* y *cómo* de la actividad o componente a documentar.
   - Evitar secciones vacías o con explicaciones genéricas; cada punto debe estar adaptado al contexto del sistema **FinGest**.

3. **Inclusión de Bloques de Código**:
   - Cuando se requiera ilustrar código (ej. pruebas unitarias en Python, configuración de entornos, scripts SQL, o lógica en JavaScript/HTML), se deben usar bloques formateados.
   - En LaTeX, utilizar el comando `\codigo{...}` para nombres de archivos, variables o pequeñas expresiones de código.
   - Para bloques de código más extensos, estructurar mediante el entorno de código adecuado o un formato estilizado y legible.

4. **Inclusión de Imágenes y Diagramas**:
   - Donde se requieran imágenes, diagramas de flujo, diagramas de secuencia, casos de uso o capturas de pantalla, estructurar usando el entorno `\begin{figure}` de LaTeX.
   - Asegurarse de proveer un `\caption{...}` descriptivo e incluir comentarios de ayuda o marcadores de posición (`[Marcador de Imagen: Descripción de lo que debe ir aquí]`) cuando la imagen deba ser provista o cargada por el usuario.

5. **Consistencia de Estilos**:
   - Todo nuevo contenido debe respetar los colores corporativos de FinGest (`primarycolor`, `secondarycolor`, `accentcolor`, etc.) y mantener el mismo nivel de formalidad y formato de tablas (`tabularx`, `longtable`, `rowcolors`) establecido en el documento.
