# Configuración de velocidad y calidad del RAG

Los valores se cambian en `.env`. Reinicie Flask después de modificar ese archivo.

## Recuperación de contexto

| Variable | Valor inicial | Efecto |
|---|---:|---|
| `RAG_DEFAULT_CONTEXTS` | `3` | Fragmentos recuperados cuando la petición no envía `n_context`. Más fragmentos aportan información, pero aumentan el tiempo. |
| `RAG_MAX_CONTEXTS` | `10` | Límite permitido para `n_context`. |
| `RAG_MAX_CHARS` | `4000` | Máximo de caracteres enviados al modelo. Un valor menor responde más rápido. |
| `RAG_SCORE_THRESHOLD` | `0.8` | Distancia máxima aceptada. Un valor menor es más estricto y puede descartar contexto útil. |

El campo `n_context` de una petición reemplaza temporalmente `RAG_DEFAULT_CONTEXTS`:

```json
{
  "question": "¿Cuál es el tema principal?",
  "n_context": 3
}
```

Para diagnosticar la recuperación, un administrador puede enviar
`"include_context": true`. La respuesta incluirá un extracto de hasta 500 caracteres por
fuente. No habilite esta opción en clientes públicos.

## Generación en Ollama

| Variable | Valor inicial | Efecto |
|---|---:|---|
| `OLLAMA_REASONING` | `false` | Desactiva el razonamiento prolongado. Activarlo puede mejorar preguntas difíciles, pero aumenta mucho el tiempo. |
| `OLLAMA_NUM_CTX` | `4096` | Ventana de contexto en tokens. Aumentarla consume más memoria. |
| `OLLAMA_NUM_PREDICT` | `160` | Máximo aproximado de tokens de salida. Controla la extensión y el tiempo de generación. |
| `OLLAMA_KEEP_ALIVE` | `30m` | Mantiene el modelo cargado para evitar recargarlo entre preguntas. |
| `OLLAMA_TEMPERATURE` | `0.0` | Con `0` las respuestas son más estables. Valores mayores agregan variedad. |
| `OLLAMA_TOP_K` | `20` | Cantidad de tokens candidatos durante la generación. |
| `OLLAMA_TOP_P` | `0.8` | Limita los candidatos por probabilidad acumulada. |

## Perfiles sugeridos

### Rápido

```env
RAG_DEFAULT_CONTEXTS=2
RAG_MAX_CHARS=2500
OLLAMA_REASONING=false
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=100
OLLAMA_KEEP_ALIVE=60m
OLLAMA_TEMPERATURE=0.0
OLLAMA_TOP_K=15
OLLAMA_TOP_P=0.75
```

### Equilibrado

```env
RAG_DEFAULT_CONTEXTS=3
RAG_MAX_CHARS=4000
OLLAMA_REASONING=false
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_PREDICT=160
OLLAMA_KEEP_ALIVE=30m
OLLAMA_TEMPERATURE=0.0
OLLAMA_TOP_K=20
OLLAMA_TOP_P=0.8
```

### Mayor profundidad

```env
RAG_DEFAULT_CONTEXTS=5
RAG_MAX_CHARS=6000
OLLAMA_REASONING=true
OLLAMA_NUM_CTX=8192
OLLAMA_NUM_PREDICT=300
OLLAMA_KEEP_ALIVE=30m
OLLAMA_TEMPERATURE=0.1
OLLAMA_TOP_K=40
OLLAMA_TOP_P=0.9
```

Este último perfil necesita más memoria y será considerablemente más lento.

## Diagnóstico

Ejecute `ollama ps` en el servidor de Ollama. Si el modelo aparece principalmente en CPU, reducir el contexto y la respuesta ayuda, pero el límite principal será el hardware. La primera consulta puede ser más lenta mientras el modelo se carga; `OLLAMA_KEEP_ALIVE` reduce ese costo en las siguientes consultas.
