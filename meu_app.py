import streamlit as st
import pandas as pd

def load_csv(file):
    """Carrega um arquivo CSV."""
    return pd.read_csv(file)

def load_excel(file, sheet_name=0):
    """Carrega um arquivo Excel enviado pelo usuário."""
    return pd.read_excel(file, sheet_name=sheet_name)

def validate_codes(csv_data, excel_data, code_column_csv, code_column_excel):
    """Valida códigos entre o CSV e o Excel."""
    valid_codes = set(excel_data[code_column_excel].astype(str))
    csv_data['Exists'] = csv_data[code_column_csv].astype(str).isin(valid_codes)
    invalid_codes = csv_data[~csv_data['Exists']][[code_column_csv]]
    grouped_invalid_codes = invalid_codes[code_column_csv].value_counts().reset_index()
    grouped_invalid_codes.columns = [code_column_csv, 'Frequência']
    return grouped_invalid_codes

def count_cod_montagem_geral(csv_data, excel_data, code_column_csv, code_column_excel):
    """Conta materiais com base no código de montagem (Geral)."""
    count_csv = csv_data[code_column_csv].value_counts().reset_index()
    count_csv.columns = [code_column_csv, 'Quantidade CSV']
    
    merged_data = count_csv.merge(excel_data, left_on=code_column_csv, right_on=code_column_excel, how='left')
    
    montagem_columns = [col for col in excel_data.columns if "CÓDIGO MONTAGEM" in col.upper()]
    qtde_columns = [col for col in excel_data.columns if "QTDE MONTAGEM" in col.upper()]
    
    for col in qtde_columns:
        merged_data[col] = merged_data[col] * merged_data['Quantidade CSV']
    
    result_columns = []
    for cod_col, qtde_col in zip(montagem_columns, qtde_columns):
        result_columns.append(cod_col)
        result_columns.append(qtde_col)
    
    return merged_data[[code_column_csv, 'Quantidade CSV'] + result_columns]

def count_materials(csv_data, excel_data, code_column_csv, code_column_excel):
    """Calcula a quantidade total de cada componente com base na frequência no CSV e nas quantidades de montagem no Excel."""
    count_csv = csv_data[code_column_csv].value_counts().reset_index()
    count_csv.columns = [code_column_csv, 'Quantidade CSV']
    
    montagem_cols = [col for col in excel_data.columns if "CÓDIGO MONTAGEM" in col.upper()]
    qtde_cols = [col for col in excel_data.columns if "QTDE MONTAGEM" in col.upper()]
    
    if len(montagem_cols) != len(qtde_cols):
        st.error("Número de colunas de 'CÓDIGO MONTAGEM' e 'QTDE MONTAGEM' não correspondem.")
        return None
    
    component_dfs = []
    for cod_col, qtde_col in zip(montagem_cols, qtde_cols):
        temp_df = excel_data[[code_column_excel, cod_col, qtde_col]].copy()
        temp_df.columns = ['codigo_montagem', 'codigo_componente', 'quantidade']
        temp_df = temp_df.merge(count_csv, left_on='codigo_montagem', right_on=code_column_csv, how='inner')
        temp_df['quantidade_total'] = temp_df['quantidade'] * temp_df['Quantidade CSV']
        component_dfs.append(temp_df[['codigo_componente', 'quantidade_total']])
    
    all_components = pd.concat(component_dfs, ignore_index=True)
    result = all_components.groupby('codigo_componente')['quantidade_total'].sum().reset_index()
    result.columns = ['Codigo', 'Quantidade total']
    
    return result

def main():
    st.markdown("### Validação de Códigos e Contagem de Materiais entre CSV e Banco de Dados.")
    
    uploaded_csv = st.file_uploader("Envie o arquivo CSV", type=["csv"])
    uploaded_excel = st.file_uploader("Envie o arquivo Excel", type=["xlsx", "xls"])
    
    if uploaded_excel:
        try:
            excel_data = load_excel(uploaded_excel)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo Excel: {e}")
            return
    else:
        return
    
    if uploaded_csv:
        try:
            csv_data = load_csv(uploaded_csv)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo CSV: {e}")
            return

        default_csv_column = "CODIGO MONTAGEM" if "CODIGO MONTAGEM" in csv_data.columns else None
        default_excel_column = "CODIGO INSTÂNCIA" if "CODIGO INSTÂNCIA" in excel_data.columns else None
        
        code_column_csv = st.selectbox("Selecione a coluna do CSV com os códigos", 
                                       csv_data.columns, 
                                       index=csv_data.columns.get_loc(default_csv_column) if default_csv_column else 0)
        code_column_excel = st.selectbox("Selecione a coluna do Excel com os códigos", 
                                         excel_data.columns, 
                                         index=excel_data.columns.get_loc(default_excel_column) if default_excel_column else 0)
        
        if st.button("Validar Códigos"):
            grouped_invalid_codes = validate_codes(csv_data, excel_data, code_column_csv, code_column_excel)
            st.write("Códigos não encontrados no Banco de Dados (agrupados):")
            st.dataframe(grouped_invalid_codes)
            csv_invalid = grouped_invalid_codes.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar CSV com códigos inválidos agrupados", csv_invalid, "codigos_invalidos_agrupados.csv", "text/csv")
        
        if st.button("Contagem cod. montagem geral"):
            material_count = count_cod_montagem_geral(csv_data, excel_data, code_column_csv, code_column_excel)
            st.write("Contagem de materiais por código de montagem:")
            st.dataframe(material_count)
            csv_material = material_count.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar CSV com contagem de materiais", csv_material, "contagem_materiais.csv", "text/csv")
        
        if st.button("Contar Materiais"):
            material_components = count_materials(csv_data, excel_data, code_column_csv, code_column_excel)
            if material_components is not None:
                st.write("Contagem de materiais por código de componente:")
                st.dataframe(material_components)
                csv_components = material_components.to_csv(index=False).encode('utf-8')
                st.download_button("Baixar CSV com contagem de materiais", csv_components, "contagem_materiais.csv", "text/csv")

if __name__ == "__main__":
    main()