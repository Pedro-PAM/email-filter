import os 
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import pdfplumber
from werkzeug.utils import secure_filename

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def classificar_email(texto_do_email):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente de IA especialista em classificar emails. Sua única função é analisar o texto do email e responder APENAS com a palavra 'Produtivo' ou 'Improdutivo'."},
                {"role": "user", "content": texto_do_email}
            ],
            temperature=0,
            max_tokens=5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao classificar: {e}")
        return "Erro"

def gerar_resposta_automatica(categoria, texto_do_email):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente de IA que escreve respostas para emails de forma profissional e concisa em português do Brasil. Baseado na categoria do email fornecida, gere uma sugestão de resposta adequada."},
                {"role": "user", "content": f"O email a seguir foi classificado como '{categoria}'. Por favor, escreva uma resposta adequada para este email: '{texto_do_email}'"}
            ],
            temperature=0.5,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao gerar resposta: {e}")
        return "Não foi possível gerar uma resposta."

app = Flask(__name__)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

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
    else:
        return jsonify({"erro": "Formato de arquivo não suportado. Envie .txt ou .pdf"}), 400
    
    if not conteudo.strip():
        return jsonify({"erro": "O arquivo parece estar vazio ou não foi possível ler o conteúdo."}), 400

    classificacao = classificar_email(conteudo)

    classificacao_normalizada = classificacao.lower().strip().replace(".", "") 

    if classificacao_normalizada in ["produtivo", "improdutivo"]:
        resposta_automatica = gerar_resposta_automatica(classificacao_normalizada, conteudo)
        resultado_final = {
            "classificacao": classificacao,
            "resposta_automatica": resposta_automatica
        }
    else:
        resultado_final = {"erro": f"Não foi possível classificar o email. Resposta da IA: {classificacao}"}

    return jsonify(resultado_final)

if __name__ == '__main__':
    app.run(debug=True)