import os
from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
import pdfplumber
from werkzeug.utils import secure_filename

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro-latest')
def classificar_email(texto_do_email):
    try:
        prompt = f"Analise o texto a seguir e classifique-o respondendo APENAS com a palavra 'Produtivo' ou 'Improdutivo', no contexto de uma empresa. Caso não tenha informações úteis pertinentes a empresa, como por exemplo, 'SPAM', ou um email informal, classifique-o como improdutivo, caso contrário, produtivo. O texto é: '{texto_do_email}'"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao classificar: {e}")
        return "Erro"

def gerar_resposta_automatica(categoria, texto_do_email):
    try:
        prompt = f"O email a seguir foi classificado como '{categoria}'. Baseado nisso, escreva uma resposta profissional e concisa em português do Brasil. O email original é: '{texto_do_email}'"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao gerar resposta: {e}")
        return "Não foi possível gerar uma resposta."

app = Flask(__name__)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/analisar-email', methods=['POST'])
def handle_analise():
    if 'email_arquivo' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files['email_arquivo']
    if arquivo.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado"}), 400

    conteudo = ""
    filename = secure_filename(arquivo.filename)

    if filename.lower().endswith('.pdf'):
        try:
            with pdfplumber.open(arquivo) as pdf:
                for pagina in pdf.pages:
                    conteudo += pagina.extract_text() or ""
        except Exception as e:
            return jsonify({"erro": f"Erro ao ler o arquivo PDF: {e}"}), 500
    elif filename.lower().endswith('.txt'):
        try:
            conteudo = arquivo.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return jsonify({"erro": f"Erro ao ler o arquivo TXT: {e}"}), 500
    elif filename.lower().endswith('.eml'):
        try:
            conteudo = arquivo.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return jsonify({"erro": f"Erro ao ler o arquivo EML: {e}"}), 500
    else:
        return jsonify({"erro": "Formato de arquivo não suportado. Envie .txt ou .pdf"}), 400

    if not conteudo.strip():
        return jsonify({"erro": "O arquivo parece estar vazio ou não foi possível ler o conteúdo."}), 400

    classificacao = classificar_email(conteudo)

    classificacao_normalizada = classificacao.lower().strip().replace(".", "")

    if "produtivo" in classificacao_normalizada or "improdutivo" in classificacao_normalizada:
        resposta_categoria = "Improdutivo" if "improdutivo" in classificacao_normalizada else "Produtivo"
        resposta_automatica = gerar_resposta_automatica(resposta_categoria, conteudo)
        resultado_final = {
            "classificacao": resposta_categoria,
            "resposta_automatica": resposta_automatica
        }
    else:
        resultado_final = {"erro": f"Não foi possível classificar o email. Resposta da IA: {classificacao}"}

    return jsonify(resultado_final)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
