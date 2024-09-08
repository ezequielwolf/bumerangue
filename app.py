from flask import Flask, render_template, request, redirect, url_for, send_file
import fitz  # PyMuPDF
import re
import os

app = Flask(__name__)

# Função para garantir que o diretório "uploads" e "outputs" existam
def garantir_diretorio_upload():
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

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

# Função para aplicar a lógica de encontrar a letra "C" e valores no TXT
def ler_valores_txt(texto):
    padrao = re.compile(r'(?<!\S)(\d{1,3}(?:\.\d{3})*,\d{2})\sC\s-\s(\d+ ok)')
    valores_direita = padrao.findall(texto)
    return valores_direita

# Função para modificar o PDF e inserir os valores do TXT
def modificar_pdf(caminho_pdf, informacoes, salvar_como):
    doc = fitz.open(caminho_pdf)
    for page_num in range(len(doc)):
        page = doc[page_num]
        texto_pdf = page.get_text("text")
        for valor, codigo in informacoes:
            print(f"Procurando: Valor: {valor}, Código: {codigo}")
            areas_valor = page.search_for(valor)
            if areas_valor:
                for area in areas_valor:
                    x_insercao = area.x1 + 7  # Um pequeno deslocamento para direita da posição do valor
                    y_insercao = area.y0 + 10  # Ajustar o valor mais para baixo (incrementar y_insercao)
                    page.insert_text((x_insercao, y_insercao), f" {codigo}", fontsize=10, color=(0, 0, 0))
                    print(f"Inserido '{codigo}' ao lado de '{valor}' no PDF.")
            else:
                print(f"Valor '{valor}' não encontrado no PDF.")
    
    # Salvar o novo arquivo PDF no caminho especificado
    doc.save(salvar_como)
    doc.close()
    print(f"PDF modificado salvo como: {salvar_como}")

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar os arquivos
@app.route('/executar', methods=['POST'])
def executar():
    if 'arquivo_txt' not in request.files or 'arquivo_pdf' not in request.files:
        return "Por favor, envie os arquivos TXT e PDF", 400
    
    arquivo_txt = request.files['arquivo_txt']
    arquivo_pdf = request.files['arquivo_pdf']

    # Garantir que o diretório 'uploads' e 'outputs' existam
    garantir_diretorio_upload()

    # Salvar os arquivos no servidor temporariamente
    caminho_txt = os.path.join("uploads", arquivo_txt.filename)
    caminho_pdf = os.path.join("uploads", arquivo_pdf.filename)
    
    arquivo_txt.save(caminho_txt)
    arquivo_pdf.save(caminho_pdf)

    # Ler o conteúdo dos arquivos
    texto_txt = ler_txt(caminho_txt)
    valores_e_direita = ler_valores_txt(texto_txt)

    # Caminho para salvar o arquivo modificado
    nome_pdf_modificado = arquivo_pdf.filename.replace(".pdf", "_modificado.pdf")
    caminho_pdf_modificado = os.path.join("outputs", nome_pdf_modificado)

    # Modificar o arquivo PDF
    modificar_pdf(caminho_pdf, valores_e_direita, caminho_pdf_modificado)

    # Enviar o arquivo modificado para o download
    return send_file(caminho_pdf_modificado, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
