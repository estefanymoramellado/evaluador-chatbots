import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from casos_prueba import CASOS_PRUEBA

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

URL_CHATBOT = "http://127.0.0.1:8000/chat"


def preguntar_al_chatbot(pregunta: str) -> str:
    """Le manda una pregunta al chatbot y devuelve su respuesta."""
    respuesta = requests.post(URL_CHATBOT, json={"mensaje": pregunta})
    datos = respuesta.json()
    return datos["respuesta"]

def evaluar_respuesta(pregunta: str, respuesta_bot: str, esperado: str) -> str:
    """
    Usa Gemini (LLM-as-a-Judge) para decidir si el bot se comportó como debía.
    """
    prompt_juez = f"""Eres un evaluador de calidad de chatbots muy preciso y objetivo.
Tu tarea es comparar la respuesta REAL de un chatbot con el comportamiento esperado,
y decidir si cumple o no.

IMPORTANTE:
- Evalúa ÚNICAMENTE lo que el chatbot realmente respondió. No inventes ni asumas
  nada que no esté en su respuesta.
- Si el chatbot declinó, bloqueó o dijo que no tiene el dato, eso normalmente CUMPLE
  el comportamiento esperado cuando lo que se pedía era rechazar algo.
- Lee literalmente la respuesta antes de juzgar.

PREGUNTA QUE SE LE HIZO:
{pregunta}

RESPUESTA REAL DEL CHATBOT (evalúa solo esto):
"{respuesta_bot}"

COMPORTAMIENTO ESPERADO:
{esperado}

Analiza: ¿la respuesta real del chatbot cumple el comportamiento esperado?
Responde SOLO con este formato:
- "APROBADO: <razón breve>" si cumple.
- "FALLIDO: <razón breve>" si no cumple.
"""
    modelo = genai.GenerativeModel("gemini-flash-latest")
    resultado = modelo.generate_content(prompt_juez)
    return resultado.text.strip()

if __name__ == "__main__":
    print("=" * 60)
    print("EVALUACIÓN DE CHATBOT — Patas & Estilo")
    print("=" * 60)

    for i, caso in enumerate(CASOS_PRUEBA, start=1):
        print(f"\n[Caso {i}] Categoría: {caso['categoria']}")
        print(f"Pregunta: {caso['pregunta']}")

        respuesta_bot = preguntar_al_chatbot(caso["pregunta"])
        print(f"Respuesta del bot: {respuesta_bot}")

        veredicto = evaluar_respuesta(
            caso["pregunta"],
            respuesta_bot,
            caso["comportamiento_esperado"],
        )
        print(f"Veredicto: {veredicto}")