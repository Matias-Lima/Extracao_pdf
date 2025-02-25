import pdfplumber
import streamlit as st
import re
import pandas as pd
import io
from collections import defaultdict
from io import BytesIO

st.set_page_config(
    page_title="Extração de Dados - REGISTRO DO EMPREGADO - FICHA COMPLETA",
    layout="wide",
    initial_sidebar_state="collapsed"  # Inicia a sidebar recolhida
)

# Função que extrai o texto cru de cada página e retorna em lista
def extract_text_by_page(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        pages_text = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
    return pages_text


def parse_page_1(text):
    data = {}
    
    patterns = {
        "Nome": r'Nome:\s*([^\n]+)',
        "Matrícula": r'Matr[ií]cula:\s*(\d+)',
        "CPF": r'C\.P\.F:\s*([\d\.\-]+)',
        "RG": r'RG:\s*([\w\/\.\-]+)',
        "Data de Nascimento": r'Data Nasc(?:\.|imento):\s*([\d\/]+)',
        "Data de Admissão": r'Data Adm(?:\.|issão):\s*([\d\/]+)',
        "Cargo": r'Cargo:\s*(\d+\s*-\s*[^\n]+?)(?=\s+[A-Z][\w\s/\.]+:|$)',
        "Vínculo": r'V[ií]nculo:\s*(\d+\s*-\s*[^\n]+?)(?=\s+[A-Z][\w\s/\.]+:|$)',
        "PIS/PASEP": r'PIS/PASEP:\s*([\d\.\-]+)',
        "Sexo": r'Sexo:\s*([MF])',
        "Estado Civil": r'Estado Civil:\s*([^\n]+?)(?=\s+N[ií]vel Instru[cç][ãa]o:|$)',
        "Nível de Instrução": r'N[ií]vel Instru[cç][ãa]o:\s*([^\n]+?)(?=\s+[A-Z][\w\s/\.]+:|$)',
        "Órgão": r'Órgão\s*([\d]+\s*-\s*[^\n]+)(?=\s+Regime:|$)',
        "Regime": r'Regime:\s*([^\n]+?)(?=\s+(?:Regime Prev\.|Lotação|[A-Z][\w\s/\.]+:)|$)',
        "Lotação": r'Lotação\s*([\d]+\s*-\s*[^\n]+)',
        "Regime Prev.": r'Regime Prev\.:\s*([^\n]+?)(?=\s+[A-Z][\w\s/\.]+:|$)',
        "Pai": r'Pai:\s*([^\n]+)(?=\s+M[ãa]e:|$)',
        "Mãe": r'M[ãa]e:\s*([^\n]+)',
        "Cônjugue": r'C[ôo]njugue:\s*([^\n]+)(?=\s+Data Nascimento:|$)',
        "Rua/Av": r'Rua/Av:\s*([^\n]+)(?=\s+Número:|$)',
        "Número": r'Número:\s*([^\n]+)(?=\s+Bairro:|$)',
        # Bairro: captura até encontrar "Cidade:" ou o fim da linha
        "Bairro": r'Bairro:\s*([^\n]+?)(?=\s+Cidade:|$)',
        # Cidade: captura até encontrar "UF:" ou o fim da linha
        "Cidade": r'Cidade:\s*([^\n]+?)(?=\s+UF:|$)',
        "UF": r'UF:\s*([A-Z]{2})(?!\w)',
        "C.E.P": r'C\.E\.P:\s*([\d\.\-]+)',
        "Telefone": r'Telefone:\s*([\d]+)',
        "Nº Dependentes Sal. Família": r'Nº Dependentes Sal\. Família:\s*(\d+)',
        "Nº Dependentes IRRF": r'Nº Dependentes IRRF:\s*(\d+)',
        "Dependentes": r'Nome dos Dependentes Sal\. Família:\s*([^\n]+)(?=\s+Data Nascimento:|$)'
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            data[field] = match.group(1).strip()
    
    return data

# Função exemplo para extrair a matrícula de uma página.
    
def extract_id(text):
    """
    Implemente aqui a lógica para extrair o número de matrícula a partir do texto da página.
    Por exemplo, utilizando expressões regulares.
    """
    import re
    # Supondo que a matrícula esteja no formato "Matrícula: 123456"
    match = re.search(r"Nome:\s*([^\n]+)", text)
    if match:
        return match.group(1)
    return None


def main():
    st.title("Extração de Dados REGISTRO DO EMPREGADO - FICHA COMPLETA")
    
    uploaded_file = st.file_uploader("Faça o upload do PDF", type=["pdf"])
    if uploaded_file is not None:
        # 1) Extrair o texto de todas as páginas com tratamento de exceções
        try:
            pages_text = extract_text_by_page(uploaded_file)
        except Exception as e:
            st.error("Erro ao extrair o texto das páginas do PDF.")
            st.exception(e)
            return
        
        num_pages = len(pages_text)
        st.write(f"O PDF possui {num_pages} páginas.")
        
        # 2) Agrupar páginas pelo número de matrícula
        users_pages = {}  # dicionário para agrupar páginas por matrícula
        for idx, page_text in enumerate(pages_text):
            try:
                matricula = extract_id(page_text)
            except Exception as e:
                st.warning(f"Erro ao extrair matrícula na página {idx+1}: {e}")
                continue

            if matricula:
                if matricula not in users_pages:
                    users_pages[matricula] = []
                users_pages[matricula].append(page_text)
            else:
                st.warning(f"Matrícula não encontrada na página {idx+1}. Página ignorada.")
        
        # 3) Processar os dados de cada usuário
        all_users_data = []
        for matricula, pages in users_pages.items():
            user_data = {}
            for page in pages:
                try:
                    data = parse_page_1(page)  # Função para processar cada página
                    user_data.update(data)
                except Exception as e:
                    st.warning(f"Erro ao processar página para matrícula {matricula}: {e}")
                    continue
            
            # Salva a quantidade de páginas associadas a esse usuário
            #user_data["Número_de_Páginas"] = len(pages)
            all_users_data.append(user_data)
        
        # 4) Converter os dados para DataFrame e exibir
        try:
            df = pd.DataFrame(all_users_data)
        except Exception as e:
            st.error("Erro ao converter os dados para DataFrame.")
            st.exception(e)
            return
        
        st.subheader("Dados Extraídos")
        st.dataframe(df)

        st.divider()
        col1, col2 = st.columns(2)

        with col1: 
            st.write("---")
            st.write("### Visualizar e editar dados")

            try:
                edited_df = st.data_editor(df, num_rows="dynamic")
            except Exception as e:
                st.error("Erro ao carregar o editor de dados.")
                st.exception(e)
                edited_df = df  # fallback para o DataFrame original

            # Cria 2 colunas para os botões de exportação
            col_txt, col_xlsx = st.columns(2)

            with col_txt:
                txt_data = edited_df.to_string(index=False)
                st.download_button(
                    label="Exportar TXT",
                    data=txt_data,
                    file_name="dados_extraidos.txt",
                    mime="text/plain"
                )

            with col_xlsx:
                try:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                        edited_df.to_excel(writer, index=False, sheet_name="Dados")
                    excel_data = excel_buffer.getvalue()
                    st.download_button(
                        label="Exportar XLSX",
                        data=excel_data,
                        file_name="dados_extraidos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error("Erro ao exportar para XLSX.")
                    st.exception(e)

        with col2:
            st.write("---")
            st.write("### Visualizar Páginas de um Usuário Específico")
            try:
                pdf = pdfplumber.open(uploaded_file)
            except Exception as e:
                st.error("Erro ao abrir o arquivo PDF para visualização.")
                st.exception(e)
                return

            try:
                page_number = st.number_input(
                    "Selecione a página para visualizar",
                    min_value=1,
                    max_value=len(pdf.pages),
                    value=1,
                    step=1
                )
                selected_page = pdf.pages[page_number - 1]
                page_image = selected_page.to_image(resolution=800)
                st.image(page_image.original, caption=f"Página {page_number}")
            except Exception as e:
                st.error("Erro ao visualizar a página selecionada.")
                st.exception(e)
    else:
        st.info("Por favor, faça o upload de um arquivo PDF.")

if __name__ == "__main__":
    main()
