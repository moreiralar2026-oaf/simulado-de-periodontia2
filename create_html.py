
import re
import json

def parse_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Regex para extrair os componentes de cada questão
    # Formato esperado:
    # QUESTAO: [Enunciado]
    # A) [Alt A]
    # B) [Alt B]
    # C) [Alt C]
    # D) [Alt D]
    # E) [Alt E]
    # GABARITO: [Letra]
    # COMENTARIO: [Comentário]
    # ---
    
    questions = []
    raw_blocks = re.split(r'---', content)
    
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
            
        try:
            # Extrair enunciado
            enunciado_match = re.search(r'QUESTAO:\s*(.*?)(?=\n[A-E]\))', block, re.DOTALL)
            if not enunciado_match:
                continue
            enunciado = enunciado_match.group(1).strip()
            
            # Extrair alternativas
            alternativas = {}
            for letter in ['A', 'B', 'C', 'D', 'E']:
                alt_match = re.search(fr'{letter}\)\s*(.*?)(?=\n[A-E]\)|\nGABARITO:)', block, re.DOTALL)
                if alt_match:
                    alternativas[letter] = alt_match.group(1).strip()
                else:
                    # Tentar encontrar a última alternativa (E) que pode ser seguida pelo GABARITO
                    alt_match = re.search(fr'{letter}\)\s*(.*?)(?=\nGABARITO:)', block, re.DOTALL)
                    if alt_match:
                        alternativas[letter] = alt_match.group(1).strip()

            # Extrair gabarito
            gabarito_match = re.search(r'GABARITO:\s*([A-E])', block)
            if not gabarito_match:
                continue
            gabarito = gabarito_match.group(1)
            
            # Extrair comentário
            comentario_match = re.search(r'COMENTARIO:\s*(.*)', block, re.DOTALL)
            if not comentario_match:
                continue
            comentario = comentario_match.group(1).strip()
            
            questions.append({
                'enunciado': enunciado,
                'alternativas': alternativas,
                'gabarito': gabarito,
                'comentario': comentario
            })
        except Exception as e:
            print(f"Erro ao processar bloco: {e}")
            continue
            
    return questions

def generate_html(questions, output_file):
    questions_json = json.dumps(questions, ensure_ascii=False)
    
    html_template = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulado Interativo de Periodontia - 500 Questões</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .container {{ max-width: 800px; margin-top: 50px; margin-bottom: 50px; }}
        .card {{ border: none; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .card-header {{ background-color: #007bff; color: white; border-radius: 15px 15px 0 0 !important; font-weight: bold; }}
        .option {{ cursor: pointer; transition: background-color 0.2s; padding: 10px; border: 1px solid #dee2e6; border-radius: 8px; margin-bottom: 10px; }}
        .option:hover {{ background-color: #e9ecef; }}
        .option.selected {{ background-color: #007bff; color: white; border-color: #007bff; }}
        .option.correct {{ background-color: #28a745 !important; color: white; border-color: #28a745; }}
        .option.incorrect {{ background-color: #dc3545 !important; color: white; border-color: #dc3545; }}
        .feedback {{ display: none; margin-top: 20px; padding: 15px; border-radius: 8px; }}
        .feedback.show {{ display: block; }}
        .feedback-correct {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .feedback-incorrect {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .progress {{ height: 10px; margin-bottom: 20px; }}
        #stats {{ font-size: 0.9rem; color: #6c757d; }}
        .btn-navigation {{ min-width: 100px; }}
        .comentario-box {{ margin-top: 15px; font-size: 0.95rem; line-height: 1.6; border-left: 4px solid #007bff; padding-left: 15px; }}
    </style>
</head>
<body>

<div class="container">
    <div class="text-center mb-4">
        <h1>Simulado de Periodontia</h1>
        <p class="lead">500 Questões de Concurso com Comentários e Dicas</p>
        <div id="stats">Questão <span id="current-q-num">1</span> de <span id="total-q-num">0</span> | Acertos: <span id="score">0</span></div>
    </div>

    <div class="progress">
        <div id="progress-bar" class="progress-bar" role="progressbar" style="width: 0%;"></div>
    </div>

    <div id="quiz-container">
        <div class="card">
            <div class="card-header" id="question-header">
                Questão #1
            </div>
            <div class="card-body">
                <p id="question-text" class="fw-bold mb-4"></p>
                <div id="options-container">
                    <!-- Alternativas serão inseridas aqui -->
                </div>
                
                <div id="feedback" class="feedback">
                    <div id="feedback-message" class="fw-bold"></div>
                    <div id="comentario-text" class="comentario-box"></div>
                </div>
            </div>
            <div class="card-footer d-flex justify-content-between">
                <button id="prev-btn" class="btn btn-outline-secondary btn-navigation" disabled>Anterior</button>
                <button id="check-btn" class="btn btn-primary btn-navigation">Verificar</button>
                <button id="next-btn" class="btn btn-outline-primary btn-navigation" style="display: none;">Próxima</button>
            </div>
        </div>
    </div>
</div>

<script>
    const questions = {questions_json};
    let currentIndex = 0;
    let score = 0;
    let answered = new Array(questions.length).fill(false);
    let userAnswers = new Array(questions.length).fill(null);

    const questionHeader = document.getElementById('question-header');
    const questionText = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    const feedback = document.getElementById('feedback');
    const feedbackMessage = document.getElementById('feedback-message');
    const comentarioText = document.getElementById('comentario-text');
    const currentQNum = document.getElementById('current-q-num');
    const totalQNum = document.getElementById('total-q-num');
    const scoreDisplay = document.getElementById('score');
    const progressBar = document.getElementById('progress-bar');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const checkBtn = document.getElementById('check-btn');

    totalQNum.textContent = questions.length;

    function loadQuestion(index) {{
        const q = questions[index];
        questionHeader.textContent = `Questão #${{index + 1}}`;
        questionText.textContent = q.enunciado;
        currentQNum.textContent = index + 1;
        
        optionsContainer.innerHTML = '';
        for (const [letter, text] of Object.entries(q.alternativas)) {{
            const div = document.createElement('div');
            div.className = 'option';
            div.innerHTML = `<strong>${{letter}})</strong> ${{text}}`;
            div.dataset.letter = letter;
            
            if (!answered[index]) {{
                div.onclick = () => selectOption(div);
            }} else {{
                if (letter === q.gabarito) div.classList.add('correct');
                if (letter === userAnswers[index] && letter !== q.gabarito) div.classList.add('incorrect');
                if (letter === userAnswers[index]) div.classList.add('selected');
            }}
            
            optionsContainer.appendChild(div);
        }}

        if (answered[index]) {{
            showFeedback(index);
            checkBtn.style.display = 'none';
            nextBtn.style.display = 'block';
        }} else {{
            feedback.classList.remove('show');
            checkBtn.style.display = 'block';
            nextBtn.style.display = 'none';
            checkBtn.disabled = true;
        }}

        prevBtn.disabled = index === 0;
        nextBtn.disabled = index === questions.length - 1;
        
        updateProgress();
    }}

    function selectOption(element) {{
        const options = optionsContainer.querySelectorAll('.option');
        options.forEach(opt => opt.classList.remove('selected'));
        element.classList.add('selected');
        userAnswers[currentIndex] = element.dataset.letter;
        checkBtn.disabled = false;
    }}

    function checkAnswer() {{
        const q = questions[currentIndex];
        const selectedLetter = userAnswers[currentIndex];
        answered[currentIndex] = true;

        if (selectedLetter === q.gabarito) {{
            score++;
            scoreDisplay.textContent = score;
        }}

        loadQuestion(currentIndex);
    }}

    function showFeedback(index) {{
        const q = questions[index];
        const selectedLetter = userAnswers[index];
        
        feedback.classList.add('show');
        if (selectedLetter === q.gabarito) {{
            feedback.className = 'feedback show feedback-correct';
            feedbackMessage.textContent = 'Correto!';
        }} else {{
            feedback.className = 'feedback show feedback-incorrect';
            feedbackMessage.textContent = `Incorreto. A resposta certa é a letra ${{q.gabarito}}.`;
        }}
        comentarioText.innerHTML = `<strong>Comentário:</strong><br>${{q.comentario.replace(/\\n/g, '<br>')}}`;
    }}

    function updateProgress() {{
        const progress = ((currentIndex + 1) / questions.length) * 100;
        progressBar.style.width = `${{progress}}%`;
    }}

    prevBtn.onclick = () => {{
        if (currentIndex > 0) {{
            currentIndex--;
            loadQuestion(currentIndex);
        }}
    }};

    nextBtn.onclick = () => {{
        if (currentIndex < questions.length - 1) {{
            currentIndex++;
            loadQuestion(currentIndex);
        }}
    }};

    checkBtn.onclick = checkAnswer;

    loadQuestion(currentIndex);
</script>

</body>
</html>
    """
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    questoes = parse_questions("/home/ubuntu/questoes_periodontia.txt")
    print(f"Total de questões processadas: {len(questoes)}")
    generate_html(questoes, "/home/ubuntu/simulado_periodontia.html")
    print("Arquivo simulado_periodontia.html gerado com sucesso.")
