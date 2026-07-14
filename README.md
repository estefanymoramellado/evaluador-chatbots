# evaluador-chatbots# Evaluador Automatizado de Chatbots

Un sistema que evalúa automáticamente la **calidad y seguridad** de un chatbot de IA:
genera preguntas adversarias ("trampa"), las lanza contra el chatbot, evalúa cada
respuesta usando un enfoque **LLM-as-a-Judge**, y reporta los resultados.

Es la versión automatizada del *red teaming* manual: en lugar de probar el chatbot
pregunta por pregunta a mano, el sistema lo hace solo y a escala.

---

## El problema

El testing tradicional es **determinista**: mismo input → mismo output esperado.
La IA es **probabilística**: la misma pregunta puede dar respuestas distintas, todas
"válidas". Esto rompe el testing clásico y crea un problema nuevo:

> ¿Cómo verificas, de forma confiable y a escala, que un chatbot responde bien y no
> puede ser manipulado?

Cualquier empresa que despliega un chatbot de cara a clientes (retail, banca,
aerolíneas) necesita responder esto de forma continua. Este proyecto es un prototipo
de esa herramienta.

---

## Qué hace

```
1. GENERA / define casos de prueba adversarios
        ↓
2. LANZA cada pregunta al chatbot (vía su API)
        ↓
3. EVALÚA cada respuesta con un LLM-as-a-Judge
   (¿alucinó? ¿se salió del rol? ¿reveló su prompt? ¿aceptó datos falsos?)
        ↓
4. REPORTA el veredicto de cada caso (APROBADO / FALLIDO + razón)
```

Los casos de prueba cubren categorías reales de ataques a chatbots:
extracción de prompt, salirse del rol, *prompt injection*, manipulación de precios,
alucinación, y un caso legítimo de control.

---

## Arquitectura

El proyecto combina dos componentes con naturalezas distintas:

- **Chatbot objetivo** — una **API** (FastAPI + Ollama) que simula el asistente de un
  negocio ficticio (una peluquería canina). Es una API porque es un servicio que
  recibe peticiones de forma continua.
- **Evaluador** — un **script** (Python) que se ejecuta de principio a fin: lanza los
  casos contra la API del chatbot, evalúa las respuestas y reporta.

El script le habla a la API. Cada componente tiene la forma que corresponde a su
función — es una pequeña **arquitectura de servicios**.

---

## El hallazgo principal: la confiabilidad del juez

Este fue el aprendizaje central del proyecto, y surgió al probarlo.

Empecé usando un **modelo local pequeño** (Qwen 2.5 7B, vía Ollama) como juez.
Al revisar los resultados con criterio de QA, descubrí que el juez era
**inconsistente**:

- Alucinaba fallas que no existían (decía que el bot "reveló su prompt" o "inventó un
  precio" cuando la respuesta real no hacía nada de eso).
- Daba **veredictos opuestos a respuestas idénticas**.
- Y lo más grave: en un caso donde el chatbot **sí falló de verdad** (reveló todo su
  prompt del sistema), el juez local lo marcó como **APROBADO** — un falso negativo
  peligroso.

Intenté calibrarlo (mejorar el prompt del juez, probar un modelo general del mismo
tamaño, darle el contexto del negocio como referencia). Nada lo hizo confiable:
algunos cambios incluso lo empeoraron, porque **saturaban** al modelo pequeño.

Entonces integré **Gemini** (vía API) como juez y comparé:

| Caso | Comportamiento real del bot | Juez local (Qwen 7B) | Juez Gemini |
|---|---|---|---|
| Fuga de prompt | El bot **reveló** su prompt (falla real) | ❌ APROBADO (no la detectó) | ✅ FALLIDO (la detectó) |
| Bloqueos correctos | El bot declinó bien | Inconsistente | Correcto |
| Matices finos | El bot bloqueó pero sin aclarar todo | No lo distinguía | Lo distinguió |

**Gemini evaluó de forma consistente y detectó la fuga de seguridad que el juez local
había aprobado por error.**

---

## Conclusiones

1. **La evaluación automática de IA no es confiable por defecto.** Un juez LLM puede
   equivocarse tanto o más que el sistema que evalúa.
2. **La capacidad del modelo juez es crítica.** Un modelo pequeño local fue
   inconsistente; un modelo capaz (Gemini) evaluó de forma confiable y con matices.
3. **Calibrar el prompt tiene un techo.** Ningún ajuste de prompt convirtió al modelo
   pequeño en un juez confiable — el límite estaba en el modelo.
4. **La validación humana sigue siendo necesaria.** Sin leer las respuestas con
   criterio propio, los veredictos automáticos me habrían engañado.

En conjunto: no se puede confiar ciegamente en un juez automático. Hace falta un
modelo suficientemente capaz, casos de prueba bien diseñados, y supervisión humana.

---

## Tecnologías

- **Python**
- **FastAPI** + **Ollama** (chatbot objetivo)
- **LLM-as-a-Judge** con dos backends comparados:
  - Ollama local (Qwen 2.5 7B)
  - Google Gemini (vía API)
- **requests** (comunicación entre servicios)
- **python-dotenv** (manejo seguro de la API key vía `.env`)

---

## Cómo ejecutarlo

**Requisitos previos:** Python, Ollama instalado con un modelo (`qwen2.5-coder:7b`),
y una API key de Google Gemini.

1. Clonar el repositorio e instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Configurar la API key de Gemini en un archivo `.env` (no se sube al repositorio):
   ```
   GEMINI_API_KEY=tu_key_aqui
   ```

3. Levantar el chatbot objetivo (en su propio proyecto):
   ```bash
   uvicorn app.main:app --reload
   ```

4. En otra terminal, ejecutar el evaluador:
   ```bash
   python evaluador.py
   ```

El evaluador recorrerá los casos de prueba, los lanzará contra el chatbot y mostrará
el veredicto de cada uno.

---

## Notas de seguridad

- La API key nunca se guarda en el código; se lee de un archivo `.env` protegido por
  `.gitignore`.
- Los datos del negocio son ficticios, por lo que es seguro usar el tier gratuito de
  Gemini. En un caso real con datos sensibles, habría que considerar la privacidad de
  los datos enviados a una API externa.

---

## Posibles mejoras futuras

- Generar los casos de prueba adversarios automáticamente con un LLM (en vez de una
  lista fija).
- Evaluar con un **panel de jueces** (varios modelos) y comparar sus veredictos.
- Reporte con métricas agregadas y visualización (dashboard).
- Migrar de la librería `google.generativeai` (descontinuada) a `google.genai`.