# Cómo agregar documentos oficiales al sistema RAG

Esta carpeta es donde debes colocar los documentos oficiales que el agente usará como base de conocimiento.

## Documentos recomendados

### SISBEN
- [ ] Metodología SISBEN IV (DANE) - PDF oficial
- [ ] Resolución de grupos y subgrupos SISBEN IV
- [ ] Guía ciudadana SISBEN IV
- [ ] Criterios de focalización por programa

### Beneficios sociales
- [ ] Decreto Familias en Acción (DPS)
- [ ] Manual operativo Jóvenes en Acción
- [ ] Decreto Colombia Mayor
- [ ] Guía Mi Casa Ya (MinVivienda)
- [ ] Resoluciones ICBF sobre programas de primera infancia

### Salud
- [ ] Plan de Beneficios en Salud (PBS) - MinSalud
- [ ] Guía afiliación Régimen Subsidiado

### Educación
- [ ] Decreto Matrícula Cero / Generación E
- [ ] Reglamento ICETEX ACCES

## Formatos soportados

| Formato | Soporte |
|---------|---------|
| `.txt`  | ✅ Sí |
| `.md`   | ✅ Sí |
| `.pdf`  | ✅ Sí (requiere PyPDF2) |

## Cómo agregar un documento

1. Descarga el documento oficial del sitio del gobierno
2. Coloca el archivo en esta carpeta (`BeneficiosYA/documents/`)
3. Reinicia el servidor — el índice se construye automáticamente al arrancar

## Dónde encontrar documentos oficiales

- **DANE / SISBEN**: https://www.dane.gov.co / https://www.sisben.gov.co
- **DPS**: https://prosperidadsocial.gov.co
- **MinSalud**: https://www.minsalud.gov.co
- **MinEducación**: https://www.mineducacion.gov.co
- **MinVivienda**: https://www.minvivienda.gov.co
- **ICBF**: https://www.icbf.gov.co
- **Colpensiones**: https://www.colpensiones.gov.co

## Notas

- Los documentos no se suben al repositorio por su tamaño (están en .gitignore)
- Cada integrante del equipo debe descargarlos y colocarlos localmente
- El agente funciona sin documentos (usa solo su knowledge base interna), pero mejora significativamente con documentos oficiales
