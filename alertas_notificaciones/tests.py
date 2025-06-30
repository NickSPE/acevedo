import os
from google import genai

def ask_ai(api_key, question):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=question
    )
    return response.text

if __name__ == "__main__":
    api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyDnWhyD5zCArmmEzmRkQH4zuB2NxgtuEHc")
    print("Escribe tu pregunta para la IA (o 'salir' para terminar):")
    while True:
        user_input = input("> ")
        if user_input.lower() == "salir":
            break
        respuesta = ask_ai(api_key, user_input)
        print(respuesta)