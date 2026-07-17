---
name: fingest_project_assistant
description: Guidelines and references for the FinGest project documentation, including requirements, visual identity, test plans, and peer reviews.
---

# FinGest Project Assistant Skill

This skill assists in maintaining, updating, and ensuring consistency across all LaTeX documentation for the **FinGest (Sistema de Gestión Financiera Personal)** project.

## Project Documents Directory

All LaTeX source documents are located in:
`c:/Users/ZUZUKA/acevedo/docs/latex/`

### 1. Unified Requirements Document
- **File**: [req_unificado.tex](file:///c:/Users/ZUZUKA/acevedo/docs/latex/req_unificado.tex)
- **Description**: Consolidates Elicitation, Functional Specifications, and Non-Functional Requirements.
- **Key Reference**: Use this as the source of truth for requirement codes (e.g., `R-6`, `R-7`, `R-41`) and descriptions when designing test cases or verifying feature scope.

### 2. Test Plan
- **File**: [plan_pruebas_bonos.tex](file:///c:/Users/ZUZUKA/acevedo/docs/latex/plan_pruebas_bonos.tex)
- **Description**: Software test plan covering component, integration, and system testing for FinGest modules (Accounts & Transactions, Financial Education).
- **Guidelines**: Keep this aligned with the requirements specified in the unified requirements document.

### 3. Visual Identity Manual
- **Files**: [identidad.tex](file:///c:/Users/ZUZUKA/acevedo/docs/latex/identidad.tex) / [document.tex](file:///c:/Users/ZUZUKA/acevedo/docs/latex/document.tex)
- **Description**: Manual de Identidad Visual y Experiencia de Usuario para el Sistema FINGEST.
- **Key Colors**:
  - Primary: `#227C91` (Teal) or `#1A365D` (Dark Blue)
  - Secondary: `#605952` (Muted Brown/Gray) or `#2B6CB0` (Bright Blue)
  - Accent: `#ECEBE9` / `#D69E2E`
  - Background: `#FAFAFA`
  - Destructive: `#EF4444`

### 4. Data Flow Analysis & Peer Review Guide
- **File**: [guia_analisis_flujo_datos_peer_review.tex](file:///c:/Users/ZUZUKA/acevedo/docs/latex/guia_analisis_flujo_datos_peer_review.tex)
- **Description**: white-box testing documentation and static inspection guidelines using the `procesar_transferencia_a_principal` function as a case study.

## Core Rules for Modification

1. **Style and Color Consistency**: Ensure new table headers, list bullets, and sections match the palette defined in [identidad.tex](file:///c:/Users/ZUZUKA/acevedo/docs/latex/identidad.tex) and the style established in the target document.
2. **Cross-Referencing**: When a requirement is added or modified in the Requirements document, check if it affects the Test Plan or the Data Flow analysis.
3. **Escaping LaTeX**: Ensure all special LaTeX characters (such as `%` for values, `_` in names, `#` etc.) are properly escaped when writing text.
4. **Non-destructive updates**: Preserve all preambles, packages, and custom commands (like `\concepto` or `\elemento`) already defined in the files.
