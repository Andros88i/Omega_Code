"""
coder.py - Lógica principal del agente generador de código
"""

import re
import ast
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from .model import OmegaModel
from .prompt import OmegaPrompt

@dataclass
class CodeFile:
    """Estructura para archivos de código generados."""
    filename: str
    content: str
    language: str
    dependencies: List[str]
    
class OmegaCoder:
    def __init__(self, model: OmegaModel):
        """
        Inicializa el generador de código.
        
        Args:
            model: Modelo de lenguaje cargado
        """
        self.model = model
        self.prompt_builder = OmegaPrompt()
        self.project_structure = {}
        
    def generate_project(self, requirements: str, output_dir: str = "./generated_project") -> Dict:
        """
        Genera un proyecto completo basado en requerimientos.
        
        Args:
            requirements: Descripción del proyecto a generar
            output_dir: Directorio de salida
            
        Returns:
            Diccionario con estructura del proyecto generado
        """
        print(f"🚀 Generando proyecto: {requirements[:50]}...")
        
        # Paso 1: Analizar requerimientos y planificar estructura
        structure_prompt = self.prompt_builder.get_structure_prompt(requirements)
        structure_response = self.model.generate(structure_prompt)
        project_structure = self._parse_structure_response(structure_response)
        
        # Paso 2: Generar cada archivo
        generated_files = []
        for file_info in project_structure["files"]:
            print(f"📄 Generando: {file_info['path']}")
            
            # Construir prompt específico para este archivo
            file_prompt = self.prompt_builder.get_file_prompt(
                requirements=requirements,
                file_info=file_info,
                project_context=project_structure
            )
            
            # Generar código
            code = self.model.generate(file_prompt)
            
            # Validar y limpiar código
            cleaned_code = self._clean_generated_code(code, file_info["language"])
            
            # Crear objeto de archivo
            code_file = CodeFile(
                filename=file_info["path"],
                content=cleaned_code,
                language=file_info["language"],
                dependencies=file_info.get("dependencies", [])
            )
            
            generated_files.append(code_file)
            
            # Guardar archivo
            self._save_file(code_file, output_dir)
        
        # Paso 3: Generar archivos de configuración
        config_files = self._generate_config_files(project_structure, requirements)
        for config_file in config_files:
            self._save_file(config_file, output_dir)
        
        print(f"✅ Proyecto generado en: {output_dir}")
        
        return {
            "project_name": project_structure.get("name", "generated_project"),
            "files": [f.filename for f in generated_files + config_files],
            "structure": project_structure
        }
    
    def generate_single_file(self, requirements: str, filename: str) -> CodeFile:
        """
        Genera un único archivo de código.
        
        Args:
            requirements: Especificaciones del archivo
            filename: Nombre del archivo con extensión
            
        Returns:
            Objeto CodeFile con el contenido generado
        """
        # Determinar lenguaje por extensión
        language = self._detect_language(filename)
        
        # Construir prompt
        prompt = self.prompt_builder.get_single_file_prompt(
            requirements=requirements,
            filename=filename,
            language=language
        )
        
        # Generar código
        raw_code = self.model.generate(prompt)
        
        # Limpiar y validar
        cleaned_code = self._clean_generated_code(raw_code, language)
        
        # Analizar dependencias
        dependencies = self._extract_dependencies(cleaned_code, language)
        
        return CodeFile(
            filename=filename,
            content=cleaned_code,
            language=language,
            dependencies=dependencies
        )
    
    def _parse_structure_response(self, response: str) -> Dict:
        """
        Parsea la respuesta de estructura del proyecto.
        
        Args:
            response: Respuesta del modelo con estructura
            
        Returns:
            Diccionario con estructura organizada
        """
        try:
            # Intentar extraer JSON
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Fallback: parsear manualmente
            structure = {"name": "project", "files": []}
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.rs', '.go')):
                    structure["files"].append({
                        "path": line.strip('- '),
                        "language": self._detect_language(line)
                    })
            
            return structure
            
        except Exception as e:
            print(f"⚠️ Error parseando estructura: {e}")
            # Estructura por defecto
            return {
                "name": "project",
                "files": [
                    {"path": "main.py", "language": "python"},
                    {"path": "README.md", "language": "markdown"}
                ]
            }
    
    def _clean_generated_code(self, code: str, language: str) -> str:
        """
        Limpia y formatea el código generado.
        
        Args:
            code: Código crudo generado
            language: Lenguaje de programación
            
        Returns:
            Código limpio y formateado
        """
        # Remover markdown code blocks si existen
        code = re.sub(r'```[a-z]*\n', '', code)
        code = code.replace('```', '')
        
        # Remover prompts residuales
        code = re.sub(r'# Response:.*?\n', '', code, flags=re.IGNORECASE)
        code = re.sub(r'// Response:.*?\n', '', code, flags=re.IGNORECASE)
        
        # Validar sintaxis básica para Python
        if language == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                print(f"⚠️ Error de sintaxis detectado, intentando corregir...")
                code = self._fix_python_syntax(code, str(e))
        
        return code.strip()
    
    def _fix_python_syntax(self, code: str, error_msg: str) -> str:
        """
        Intenta corregir errores de sintaxis en Python.
        
        Args:
            code: Código con error
            error_msg: Mensaje de error
            
        Returns:
            Código corregido
        """
        # Corregir indentación común
        lines = code.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Remover indentación inconsistente
            line = line.rstrip()
            if line and not line.startswith(' ') and not line.startswith('\t'):
                # Agregar indentación consistente
                if i > 0 and lines[i-1].endswith(':'):
                    line = '    ' + line
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _detect_language(self, filename: str) -> str:
        """
        Detecta el lenguaje por extensión del archivo.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Identificador del lenguaje
        """
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-ts',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.html': 'html',
            '.css': 'css',
            '.md': 'markdown',
            '.json': 'json',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.toml': 'toml',
            '.sh': 'bash',
            '.sql': 'sql'
        }
        
        ext = Path(filename).suffix.lower()
        return extensions.get(ext, 'text')
    
    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """
        Extrae dependencias del código.
        
        Args:
            code: Código a analizar
            language: Lenguaje del código
            
        Returns:
            Lista de dependencias
        """
        dependencies = []
        
        if language == "python":
            # Buscar imports
            import_pattern = r'^\s*(?:import|from)\s+(\S+)'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                dep = match.group(1).split('.')[0]
                if dep not in dependencies and not dep.startswith('_'):
                    dependencies.append(dep)
        
        elif language == "javascript":
            # Buscar requires e imports
            patterns = [
                r"require\(['\"](\S+?)['\"]\)",
                r"import.*from\s+['\"](\S+?)['\"]",
                r"import\s+['\"](\S+?)['\"]"
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    dep = match.group(1)
                    if dep not in dependencies and not dep.startswith('.'):
                        dependencies.append(dep.split('/')[0])
        
        return dependencies
    
    def _generate_config_files(self, structure: Dict, requirements: str) -> List[CodeFile]:
        """
        Genera archivos de configuración del proyecto.
        
        Args:
            structure: Estructura del proyecto
            requirements: Requerimientos originales
            
        Returns:
            Lista de archivos de configuración
        """
        config_files = []
        
        # Generar README.md
        readme_content = f"""# {structure.get('name', 'Generated Project')}

## Descripción
Proyecto generado automáticamente por Omega-Code.

## Requerimientos Originales
