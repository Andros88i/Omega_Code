
## 4. main.py
```python
"""
main.py - Interfaz principal de Omega-Code
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Importar módulos internos
from model import OmegaModel
from coder import OmegaCoder
from prompt import OmegaPrompt

class OmegaCLI:
    """Interfaz de línea de comandos para Omega-Code."""
    
    def __init__(self):
        self.model = None
        self.coder = None
        
    def initialize(self, model_name: Optional[str] = None, quantize: bool = True):
        """
        Inicializa el sistema Omega-Code.
        
        Args:
            model_name: Nombre del modelo a usar (opcional)
            quantize: Si True, usa cuantización 4-bit
        """
        print("""
╔══════════════════════════════════════════╗
║           OMEGA-CODE v1.0                ║
║    Generador de Código Inteligente       ║
╚══════════════════════════════════════════╝
        """)
        
        # Configurar modelo
        default_model = "deepseek-coder-6.7b-instruct"
        model_to_use = model_name or default_model
        
        print(f"🔧 Configurando modelo: {model_to_use}")
        
        try:
            self.model = OmegaModel(model_to_use)
            self.model.load(quantize=quantize)
            self.coder = OmegaCoder(self.model)
            
            print("🚀 Omega-Code inicializado y listo")
            
        except Exception as e:
            print(f"❌ Error inicializando: {e}")
            sys.exit(1)
    
    def run_interactive(self):
        """Ejecuta modo interactivo."""
        print("\n📝 MODO INTERACTIVO")
        print("Escribe 'exit' para salir, 'project' para crear proyecto")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n🎯 Omega > ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'salir']:
                    print("👋 ¡Hasta luego!")
                    break
                
                elif user_input.lower() == 'project':
                    self._create_project_interactive()
                
                elif user_input.lower() == 'help':
                    self._show_help()
                
                else:
                    # Asumir que es un requerimiento para archivo único
                    filename = input("📝 Nombre del archivo (ej: app.py): ").strip()
                    if not filename:
                        print("⚠️ Se requiere nombre de archivo")
                        continue
                    
                    print(f"⚙️ Generando {filename}...")
                    code_file = self.coder.generate_single_file(user_input, filename)
                    
                    print(f"\n✅ Archivo generado: {code_file.filename}")
                    print(f"📏 Lenguaje: {code_file.language}")
                    print(f"📦 Dependencias: {', '.join(code_file.dependencies) if code_file.dependencies else 'Ninguna'}")
                    
                    save = input("\n💾 ¿Guardar archivo? (s/n): ").strip().lower()
                    if save == 's':
                        output_dir = input("📁 Directorio de salida (./output): ").strip() or "./output"
                        self.coder._save_file(code_file, output_dir)
                    
                    preview = input("\n👁️ ¿Mostrar código? (s/n): ").strip().lower()
                    if preview == 's':
                        print("\n" + "="*80)
                        print(code_file.content[:500])
                        if len(code_file.content) > 500:
                            print("... [truncado]")
                        print("="*80)
            
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrumpido por usuario")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _create_project_interactive(self):
        """Crea proyecto en modo interactivo."""
        print("\n🏗️  CREACIÓN DE PROYECTO")
        
        requirements = input("📋 Describe tu proyecto:\n> ")
        
        if not requirements:
            print("⚠️ Se requiere descripción del proyecto")
            return
        
        output_dir = input("📁 Directorio de salida (./generated_project): ").strip() or "./generated_project"
        
        print("\n⚙️ Generando proyecto...")
        
        try:
            result = self.coder.generate_project(requirements, output_dir)
            
            print(f"\n🎉 PROYECTO GENERADO EXITOSAMENTE")
            print(f"📁 Directorio: {output_dir}")
            print(f"📊 Archivos: {len(result['files'])}")
            print(f"🏷️  Nombre: {result['project_name']}")
            
            # Mostrar estructura
            print("\n📂 ESTRUCTURA:")
            for file_path in result['files']:
                print(f"  📄 {file_path}")
        
        except Exception as e:
            print(f"❌ Error generando proyecto: {e}")
    
    def _show_help(self):
        """Muestra ayuda del sistema."""
        help_text = """
📖 AYUDA DE OMEGA-CODE

COMANDOS INTERACTIVOS:
  project       - Crear un nuevo proyecto completo
  exit/quit     - Salir del programa
  help          - Mostrar esta ayuda

EJEMPLOS DE USO:
  > Crear API REST con FastAPI
  > Generar componente React con TypeScript
  > Implementar script de procesamiento de datos

MODOS DE OPERACIÓN:
  1. Proyecto completo: Genera estructura completa con múltiples archivos
  2. Archivo único: Genera un archivo específico basado en requerimientos

CONFIGURACIÓN:
  - Modelo: deepseek-coder-6.7b-instruct (configurable)
  - Cuantización: Activada por defecto para eficiencia
  - Reglas: Seguridad, calidad y mejores prácticas
        """
        print(help_text)
    
    def run_from_file(self, requirements_file: str, output_dir: str):
        """
        Ejecuta generación desde archivo de requerimientos.
        
        Args:
            requirements_file: Ruta al archivo con requerimientos
            output_dir: Directorio de salida
        """
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                requirements = f.read()
            
            print(f"📖 Leyendo requerimientos de: {requirements_file}")
            print(f"📁 Salida en: {output_dir}")
            
            result = self.coder.generate_project(requirements, output_dir)
            
            print(f"\n✅ Proyecto generado exitosamente")
            print(f"📊 Archivos creados: {len(result['files'])}")
            
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {requirements_file}")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Omega-Code - Generador de Código Inteligente")
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "file", "single"],
        default="interactive",
        help="Modo de operación"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-coder-6.7b-instruct",
        help="Nombre del modelo a usar"
    )
    
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Desactivar cuantización (usa más memoria)"
    )
    
    parser.add_argument(
        "--requirements",
        type=str,
        help="Archivo con requerimientos (para modo file)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./generated_project",
        help="Directorio de salida"
    )
    
    parser.add_argument(
        "--single-file",
        type=str,
        help="Generar solo un archivo específico"
    )
    
    parser.add_argument(
        "--single-requirements",
        type=str,
        help="Requerimientos para archivo único"
    )
    
    args = parser.parse_args()
    
    # Inicializar CLI
    cli = OmegaCLI()
    cli.initialize(args.model, quantize=not args.no_quantize)
    
    # Ejecutar según modo
    if args.mode == "interactive":
        cli.run_interactive()
    
    elif args.mode == "file":
        if not args.requirements:
            print("❌ Se requiere --requirements en modo file")
            sys.exit(1)
        cli.run_from_file(args.requirements, args.output)
    
    elif args.mode == "single":
        if not args.single_file or not args.single_requirements:
            print("❌ Se requiere --single-file y --single-requirements")
            sys.exit(1)
        
        print(f"⚙️ Generando archivo único: {args.single_file}")
        code_file = cli.coder.generate_single_file(args.single_requirements, args.single_file)
        
        # Guardar
        output_path = Path(args.output) / args.single_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code_file.content)
        
        print(f"✅ Archivo guardado: {output_path}")

if __name__ == "__main__":
    main()
