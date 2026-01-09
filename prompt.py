"""
prompt.py - Reglas y plantillas de prompts para generación de código
"""

from typing import Dict, List, Optional

class OmegaPrompt:
    """Manejador de prompts para generación de código."""
    
    # Reglas de programación
    CODING_RULES = """
## REGLAS DE PROGRAMACIÓN OMEGA-CODE

1. **CALIDAD PROFESIONAL**
   - Código limpio, modular y mantenible
   - Nombres descriptivos en inglés (snake_case para Python, camelCase para JS)
   - Documentación y comentarios donde sea necesario
   - Manejo de errores robusto

2. **MEJORES PRÁCTICAS**
   - Principio de responsabilidad única
   - Funciones pequeñas y enfocadas
   - Evitar código duplicado (DRY)
   - Separación de preocupaciones

3. **SEGURIDAD**
   - Validar todas las entradas externas
   - No exponer información sensible
   - Usar parámetros preparados para SQL
   - Sanitizar inputs del usuario

4. **PERFORMANCE**
   - Algoritmos eficientes en tiempo y espacio
   - Manejo apropiado de memoria
   - Uso de estructuras de datos adecuadas
   - Optimización cuando sea necesario

5. **ESTILO CONSISTENTE**
   - Seguir las guías de estilo del lenguaje
   - Indentación consistente (4 espacios para Python, 2 para JS)
   - Líneas máximo 80-100 caracteres
   - Espaciado coherente
"""
    
    def get_structure_prompt(self, requirements: str) -> str:
        """
        Genera prompt para planificar estructura del proyecto.
        
        Args:
            requirements: Requerimientos del proyecto
            
        Returns:
            Prompt para estructura
        """
        return f"""{self.CODING_RULES}

## TAREA: PLANIFICAR ESTRUCTURA DE PROYECTO

### REQUERIMIENTOS:
{requirements}

### INSTRUCCIONES:
1. Analiza los requerimientos y diseña una estructura de proyecto profesional
2. Identifica los archivos necesarios con sus rutas y lenguajes
3. Considera arquitectura escalable y mantenible
4. Incluye archivos de configuración necesarios

### FORMATO DE RESPUESTA:
```json
{{
  "name": "nombre_del_proyecto",
  "description": "breve_descripción",
  "architecture": "tipo_de_arquitectura",
  "files": [
    {{
      "path": "ruta/del/archivo.py",
      "language": "python",
      "purpose": "descripción de propósito",
      "dependencies": ["dep1", "dep2"]
    }},
    // ... más archivos
  ]
}}
