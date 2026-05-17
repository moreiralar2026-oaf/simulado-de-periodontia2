
import os
from openai import OpenAI
import re
import time

# Configura a chave da API (já configurada no ambiente)
client = OpenAI()

def generate_questions_batch(text_chunk, num_questions_target):
    prompt = f"""Com base no texto a seguir, crie {num_questions_target} questões de múltipla escolha para concurso público sobre Periodontia. Para cada questão, forneça:
1. O enunciado da questão.
2. 5 alternativas (A, B, C, D, E), sendo apenas uma correta.
3. O gabarito (letra da alternativa correta).
4. Um comentário detalhado explicando a resposta correta e por que as outras estão erradas, além de dicas relevantes para o tema da questão.

Formato de saída esperado para cada questão:
QUESTAO:
[Enunciado da questão]
A) [Alternativa A]
B) [Alternativa B]
C) [Alternativa C]
D) [Alternativa D]
E) [Alternativa E]
GABARITO: [Letra da alternativa correta]
COMENTARIO: [Comentário detalhado e dicas]
---

TEXTO:
{text_chunk}
"""

    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": "Você é um especialista em Periodontia e em elaboração de questões para concursos públicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8192,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao gerar questões: {e}")
        return None

def main():
    apostila_file = "/home/ubuntu/periodontia_apostila.txt"
    output_file = "/home/ubuntu/questoes_periodontia.txt"
    target_questions = 500
    questions_per_api_call = 20 # Reduzido para gerar um número mais gerenciável por chamada
    max_chunk_length = 2000

    with open(apostila_file, "r", encoding="utf-8") as f:
        apostila_content = f.read()

    chunks = []
    current_chunk = []
    current_length = 0

    for line in apostila_content.splitlines():
        line_length = len(line.split())
        if current_length + line_length > max_chunk_length and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(line)
        current_length += line_length
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    all_questions = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing_questions_raw = f.read()
        all_questions = re.findall(r"QUESTAO:.*?COMENTARIO:.*?\n---", existing_questions_raw, re.DOTALL)
        print(f"[LOG] Encontradas {len(all_questions)} questões existentes no arquivo \'{output_file}\'.")

    total_generated_questions = len(all_questions)
    chunk_index = 0
    generation_attempts = 0
    max_total_attempts = 500 # Aumentado o limite de tentativas para garantir 500 questões

    while total_generated_questions < target_questions and generation_attempts < max_total_attempts:
        if chunk_index >= len(chunks):
            chunk_index = 0 # Reiniciar do primeiro chunk se todos foram usados

        chunk = chunks[chunk_index]
        print(f"[LOG] Gerando questões do chunk {chunk_index+1}/{len(chunks)}. Total atual: {total_generated_questions}/{target_questions}")

        generated_text = generate_questions_batch(chunk, questions_per_api_call)
        if generated_text:
            found_questions = re.findall(r"QUESTAO:.*?COMENTARIO:.*?\n---", generated_text, re.DOTALL)
            new_questions_count = 0
            for q_text in found_questions:
                q_text = q_text.strip()
                if q_text and q_text.startswith("QUESTAO:"):
                    all_questions.append(q_text)
                    new_questions_count += 1

            all_questions = list(dict.fromkeys(all_questions)) # Remover duplicatas

            total_generated_questions = len(all_questions)
            print(f"[LOG] Adicionadas {new_questions_count} questões. Total agora: {total_generated_questions}")
        else:
            print(f"[LOG] Não foi possível gerar questões para o chunk {chunk_index+1}. Tentando o próximo...")

        chunk_index += 1
        generation_attempts += 1

    with open(output_file, "w", encoding="utf-8") as f:
        for q in all_questions:
            f.write(q + "\n")

    print(f"[LOG] Geração de questões concluída. Total de questões: {total_generated_questions}")

if __name__ == "__main__":
    main()
