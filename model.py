"""
model.py - Carga y gestión del modelo de lenguaje
"""

import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Optional, Tuple

class OmegaModel:
    def __init__(self, model_name: str = "deepseek-coder-6.7b-instruct"):
        """
        Inicializa el modelo de lenguaje para generación de código.
        
        Args:
            model_name: Nombre o ruta del modelo a cargar
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        
    def _get_device(self) -> torch.device:
        """Determina el dispositivo a utilizar (GPU/CPU)."""
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    
    def load(self, quantize: bool = True):
        """
        Carga el modelo y tokenizer.
        
        Args:
            quantize: Si True, usa cuantización 4-bit para reducir memoria
        """
        print(f"🔄 Cargando modelo {self.model_name} en {self.device}...")
        
        # Configuración de tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Configuración de cuantización
        bnb_config = None
        if quantize and self.device.type == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
        
        # Cargar modelo
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config if quantize else None,
            device_map="auto" if quantize else None,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        if not quantize:
            self.model.to(self.device)
        
        self.model.eval()
        print("✅ Modelo cargado exitosamente")
    
    def generate(
        self,
        prompt: str,
        max_length: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop_sequences: Optional[list] = None
    ) -> str:
        """
        Genera texto a partir de un prompt.
        
        Args:
            prompt: Texto de entrada
            max_length: Longitud máxima de generación
            temperature: Controla la aleatoriedad (0 = determinístico)
            top_p: Muestreo de núcleo
            stop_sequences: Secuencias donde detener la generación
            
        Returns:
            Texto generado
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Modelo no cargado. Llama a load() primero.")
        
        # Tokenizar entrada
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=1024
        ).to(self.device)
        
        # Configurar secuencias de parada
        stopping_criteria = None
        if stop_sequences:
            stop_token_ids = self.tokenizer(
                stop_sequences,
                add_special_tokens=False
            ).input_ids
            stopping_criteria = self._create_stopping_criteria(stop_token_ids)
        
        # Generar
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                stopping_criteria=stopping_criteria,
                repetition_penalty=1.1
            )
        
        # Decodificar
        generated = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return generated.strip()
    
    def _create_stopping_criteria(self, stop_token_ids):
        """Crea criterios de parada personalizados."""
        from transformers import StoppingCriteria, StoppingCriteriaList
        
        class StopSequenceCriteria(StoppingCriteria):
            def __init__(self, stop_ids):
                self.stop_ids = stop_ids
            
            def __call__(self, input_ids, scores, **kwargs):
                for stop_id in self.stop_ids:
                    if input_ids[0][-len(stop_id):].tolist() == stop_id:
                        return True
                return False
        
        return StoppingCriteriaList([StopSequenceCriteria(stop_token_ids)])
