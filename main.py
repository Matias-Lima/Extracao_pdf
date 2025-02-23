import pdfplumber
import io
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import base64
import pandas as pd
import re
from io import BytesIO
import pandas as pd

st.set_page_config(layout="wide", page_title="Extração de Dados de PDF")


def parse_table(table):
    """
    Extrai os dados do OCR e organiza-os em um dicionário.
    O processamento é dividido em três partes:
      1. Dados superiores (identificação: Matrícula, Nome, CPF, etc.)
      2. Dados da tabela (cabeçalho e linha de valores)
      3. Totais (Total de Vencimentos, Total de Descontos, Valor Líquido a Receber)
    """
    result = {
        'Matrícula': None,
        'Nome': None,
        'CPF': None,
        'PIS/PASEP': None,
        'Banco': None,
        'Agência': None,
        'Conta': None,
        'Órgão/Secretaria': None,
        'Unid. Trabalho/Lotação': None,
        'Data Admissão': None,
        'Cargo/Benefício': None,
        'Carga Horária': None,
        'Tempo de Serviço': None,
        'Margem Consignável': None,
        'Tempo de Serviço Anterior': None,
        'Código': None,
        'Descrição': None,
        'Limite': None,
        'Vantagens': None,
        'Descontos': None,
        'Total de Vencimentos': None,
        'Total de Descontos': None,
        'Valor Líquido a Receber': None
    }

    # Parte 1: Processar as linhas superiores (primeiras 7 linhas)
    for row in table[:7]:
        for cell in row:
            if cell is None:
                continue
            lines = cell.split('\n')
            if lines[0] == 'Matrícula' and len(lines) > 1:
                result['Matrícula'] = lines[1].strip()
            elif lines[0] == 'Nome' and len(lines) > 1:
                result['Nome'] = lines[1].strip()
            elif lines[0] == 'CPF' and len(lines) > 1:
                result['CPF'] = lines[1].strip()
            elif lines[0] == 'PIS/PASEP' and len(lines) > 1:
                result['PIS/PASEP'] = lines[1].strip()
            elif lines[0] == 'Banco' and len(lines) > 1:
                result['Banco'] = lines[1].strip()
            elif lines[0] == 'Agência' and len(lines) > 1:
                result['Agência'] = lines[1].strip()
            elif lines[0] == 'Conta' and len(lines) > 1:
                result['Conta'] = lines[1].strip()
            elif lines[0] == 'Órgão/Secretaria' and len(lines) > 1:
                result['Órgão/Secretaria'] = lines[1].strip()
            elif lines[0] == 'Unid. Trabalho/Lotação' and len(lines) > 1:
                result['Unid. Trabalho/Lotação'] = lines[1].strip()
            elif lines[0] == 'Data Admissão' and len(lines) > 1:
                result['Data Admissão'] = lines[1].strip()
            elif lines[0] == 'Cargo/Benefício' and len(lines) > 1:
                result['Cargo/Benefício'] = lines[1].strip()
            elif lines[0] == 'Carga Horária' and len(lines) > 1:
                result['Carga Horária'] = lines[1].strip()
            elif lines[0] == 'Tempo de Serviço' and len(lines) > 1:
                result['Tempo de Serviço'] = lines[1].strip()
            elif lines[0] == 'Margem Consignável' and len(lines) > 1:
                result['Margem Consignável'] = lines[1].strip()
            elif 'Tempo de Serviço Anterior' in lines[0]:
                if len(lines) > 1:
                    result['Tempo de Serviço Anterior'] = lines[1].strip()
                else:
                    result['Tempo de Serviço Anterior'] = ''

    # Parte 2: Processar a parte da tabela (cabeçalho e linha de valores)
    header_row = None
    data_row = None
    for idx, row in enumerate(table):
        if row[0] == 'Código':
            header_row = row
            # Supomos que a linha seguinte contenha os dados correspondentes
            if idx + 1 < len(table):
                data_row = table[idx + 1]
            break

    if header_row and data_row:
        for i, header in enumerate(header_row):
            if header is None:
                continue
            value = data_row[i] if i < len(data_row) else None
            if value is None:
                continue
            # Extração baseada no rótulo da coluna
            if header == 'Código':
                # Junta valores separados por quebra de linha com vírgula
                result['Código'] = '; '.join([v.strip() for v in value.split('\n')])
            elif header == 'Descrição':
                # Junta com " - " para melhor legibilidade
                result['Descrição'] = '; '.join([v.strip() for v in value.split('\n')])
            elif header == 'Limite':
                result['Limite'] = '; '.join([v.strip() for v in value.split('\n')])
            elif header == 'Vantagens':
                result['Vantagens'] = '; '.join([v.strip() for v in value.split('\n')])
            elif header == 'Descontos':
                result['Descontos'] = '; '.join([v.strip() for v in value.split('\n')])
            # O rótulo "Ref." pode ser ignorado ou tratado se necessário

    # Parte 3: Processar as linhas de totais
    for row in table:
        for cell in row:
            if cell is None:
                continue
            if cell.startswith('Total de Vencimentos'):
                lines = cell.split('\n')
                if len(lines) > 1:
                    result['Total de Vencimentos'] = lines[1].strip()
            elif cell.startswith('Total de Descontos'):
                lines = cell.split('\n')
                if len(lines) > 1:
                    result['Total de Descontos'] = lines[1].strip()
            elif cell.startswith('Valor Líquido a Receber'):
                lines = cell.split('\n')
                if len(lines) > 1:
                    result['Valor Líquido a Receber'] = lines[1].strip()

    return result


# Função para extrair o texto de todas as páginas do PDF
def extract_pdf_text(file):
    with pdfplumber.open(file) as pdf:
        raw_text = [page.extract_text() for page in pdf.pages if page.extract_text()]
    return "\n".join(raw_text)

# Função para extrair todas as tabelas do PDF
def extract_pdf_tables(file):
    tables_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    tables_data.append(table)
    return tables_data

# Função para criar o DataFrame a partir de uma tabela extraída
# OBS.: Certifique-se de ter implementado a função 'parse_table' que transforma a tabela no dicionário desejado.
def create_dataframe_from_table(table):
    parsed_dict = parse_table(table)  # Função que você deve implementar
    return pd.DataFrame([parsed_dict])


def main():
    st.title("Extração de Dados de PDF em Streamlit")

    # Upload do arquivo PDF
    uploaded_file = st.file_uploader("Faça o upload de um PDF", type=["pdf"])

    if uploaded_file is not None:
        # Extração de texto
        pdf_text = extract_pdf_text(uploaded_file)
        st.subheader("Texto Extraído")
        st.text_area("Conteúdo do PDF", pdf_text, height=200)

        # Extração de tabelas
        tables = extract_pdf_tables(uploaded_file)
        if tables:
            data_rows = []
            for idx, table in enumerate(tables):
                # Converte a tabela em um dicionário usando a função parse_table
                parsed_dict = parse_table(table)  # Implemente essa função conforme a estrutura dos seus dados
                data_rows.append(parsed_dict)

            # Cria um DataFrame onde cada linha representa os dados de uma tabela extraída
            df = pd.DataFrame(data_rows)

            # Lista de colunas desejadas na ordem definida
            desired_columns = [
                'Matrícula', 'Nome', 'CPF', 'PIS/PASEP', 'Banco', 'Agência', 'Conta',
                'Órgão/Secretaria', 'Unid. Trabalho/Lotação', 'Data Admissão',
                'Cargo/Benefício', 'Carga Horária', 'Tempo de Serviço',
                'Margem Consignável', 'Tempo de Serviço Anterior', 'Código', 'Descrição',
                'Limite', 'Vantagens', 'Descontos', 'Total de Vencimentos',
                'Total de Descontos', 'Valor Líquido a Receber'
            ]
            # Seleciona apenas as colunas que realmente existem no DataFrame
            available_columns = [col for col in desired_columns if col in df.columns]

            # Permite que o usuário escolha as colunas a serem exibidas
            user_columns = st.sidebar.multiselect(
                "Escolha as colunas para serem extraídas",
                options=available_columns,
                default=available_columns
            )

            df_final = df[user_columns] if user_columns else df

            st.subheader("Dados Extraídos")
            st.dataframe(df_final)

            # Geração do botão de download para o Excel
            towrite = BytesIO()
            df_final.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button(
                label="Download Excel",
                data=towrite,
                file_name="demonstrativo_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Nenhuma tabela foi encontrada no PDF.")

        st.write("### Comparação e Edição dos Dados")

        # Cria duas colunas
        col1, col2 = st.columns(2)

        with col1:
            # 4. Edição dos Dados
            # Usando st.data_editor para permitir edição dos dados
            edited_df = st.data_editor(df, num_rows="dynamic")

        with col2:
            # Exibição da visualização (imagem da página)
            if uploaded_file is not None:
                # Reinicia o ponteiro do arquivo para garantir que ele seja lido do início
                uploaded_file.seek(0)
                pdf_bytes = uploaded_file.read()
                # Converte o PDF para base64
                base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                # Cria um iframe para exibir o PDF
                pdf_display = f"""
                <iframe src="data:application/pdf;base64,{base64_pdf}#zoom=100" width="100%" height="600" type="application/pdf"></iframe>
                """
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.write("Não foi possível carregar o PDF.")

        # 5. Exportar para CSV
        if st.button("Exportar CSV"):
            csv_buffer = io.StringIO()
            edited_df.to_csv(csv_buffer, index=False, sep=';')
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="Baixar CSV",
                data=csv_data,
                file_name="dados_extraidos.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
