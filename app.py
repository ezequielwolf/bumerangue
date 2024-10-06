import fitz  # PyMuPDF
import re
import os
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Função para garantir que o diretório "uploads" exista
def garantir_diretorio_upload():
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

# Função para extrair texto de arquivos PDF
def ler_pdf(caminho_pdf):
    doc = fitz.open(caminho_pdf)
    texto_pdf = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        texto_pdf += page.get_text()
    doc.close()
    return texto_pdf

# Função para extrair texto de arquivos TXT
def ler_txt(caminho_txt):
    with open(caminho_txt, 'r', encoding='utf-8') as file:
        conteudo_txt = file.read()
    return conteudo_txt

# Função para aplicar a lógica de encontrar valores contábeis no TXT
def ler_valores_txt(texto):
    padrao = re.compile(r'(\d{1,3}(?:\.\d{3})*,\d{2})\sC\s-\s(\d+ ok)')
    valores_direita = padrao.findall(texto)
    return valores_direita

# Função para modificar o PDF e inserir os valores do TXT
def modificar_pdf(caminho_pdf, informacoes):
    doc = fitz.open(caminho_pdf)
    valores_inseridos = set()  # Criar um conjunto para armazenar valores já inseridos
    for page_num in range(len(doc)):
        page = doc[page_num]
        texto_pdf = page.get_text("text")
        for valor, codigo in informacoes:
            if valor in valores_inseridos:  # Pular se o valor já foi processado
                continue

            print(f"Procurando: Valor: {valor}, Código: {codigo}")
            areas_valor = page.search_for(valor)
            if areas_valor:
                for area in areas_valor:
                    x_insercao = area.x1 + 7  # Um pequeno deslocamento para direita da posição do valor
                    y_insercao = area.y0 + 10  # Ajustar o valor mais para baixo (incrementar y_insercao)
                    page.insert_text((x_insercao, y_insercao), f" {codigo}", fontsize=10, color=(0, 0, 0))
                    print(f"Inserido '{codigo}' ao lado de '{valor}' no PDF.")
                    valores_inseridos.add(valor)  # Adicionar o valor ao conjunto para evitar duplicação
            else:
                print(f"Valor '{valor}' não encontrado no PDF.")
    
    # Salvar o novo arquivo PDF no diretório temporário para download
    caminho_final = os.path.join("uploads", os.path.basename(caminho_pdf).replace(".pdf", "_modificado.pdf"))
    doc.save(caminho_final)
    doc.close()
    print(f"PDF modificado salvo como: {caminho_final}")
    return caminho_final

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar os arquivos e permitir download
@app.route('/executar', methods=['POST'])
def executar():
    if 'arquivo_txt' not in request.files or 'arquivo_pdf' not in request.files:
        return "Por favor, envie os arquivos TXT e PDF", 400
    
    arquivo_txt = request.files['arquivo_txt']
    arquivo_pdf = request.files['arquivo_pdf']

    # Garantir que o diretório 'uploads' exista
    garantir_diretorio_upload()

    # Salvar os arquivos no servidor temporariamente
    caminho_txt = os.path.join("uploads", secure_filename(arquivo_txt.filename))
    caminho_pdf = os.path.join("uploads", secure_filename(arquivo_pdf.filename))
    
    arquivo_txt.save(caminho_txt)
    arquivo_pdf.save(caminho_pdf)

    # Ler o conteúdo dos arquivos
    texto_txt = ler_txt(caminho_txt)
    valores_e_direita = ler_valores_txt(texto_txt)

    # Modificar o arquivo PDF
    caminho_final_pdf = modificar_pdf(caminho_pdf, valores_e_direita)

    # Oferecer o download do PDF modificado para o usuário
    return send_file(caminho_final_pdf, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
