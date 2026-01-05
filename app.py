import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, time
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Luna Alencar", layout="wide", page_icon="⚖️")

# --- CONEXÃO COM O BANCO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.warning("⚠️ Configuração de banco de dados não detectada.")
    st.stop()

# --- FUNÇÕES ÚTEIS ---
def upload_arquivo(arquivo, nome_arquivo):
    try:
        file_bytes = arquivo.getvalue()
        path = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nome_arquivo}"
        supabase.storage.from_("documentos").upload(path, file_bytes, {"content-type": arquivo.type})
        return path
    except Exception as e:
        return None

def gerar_pdf_agenda(dados_agenda, mes, ano):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"Agendamentos - {mes}/{ano}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(35, 10, "Data/Hora", 1)
    pdf.cell(60, 10, "Cliente", 1)
    pdf.cell(50, 10, "Evento", 1)
    pdf.cell(45, 10, "Local", 1)
    pdf.ln()
    
    # Linhas
    pdf.set_font("Arial", size=9)
    for item in dados_agenda:
        data_fmt = pd.to_datetime(item['data_hora']).strftime('%d/%m %H:%M')
        # Tratamento de erro de caractere (remove acentos pro PDF não quebrar se não tiver fonte instalada)
        nome = item['processos']['clientes']['nome'][:28].encode('latin-1', 'replace').decode('latin-1')
        evento = item['tipo_evento'][:25].encode('latin-1', 'replace').decode('latin-1')
        local = item['local_cidade'][:20].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(35, 10, data_fmt, 1)
        pdf.cell(60, 10, nome, 1)
        pdf.cell(50, 10, evento, 1)
        pdf.cell(45, 10, local, 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- TELA PRINCIPAL ---
def main():
    # Login Simples
    if 'usuario' not in st.session_state:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.title("⚖️ Acesso Restrito")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                try:
                    user = supabase.table('usuarios').select("*").eq('usuario', usuario).eq('senha', senha).execute()
                    if user.data:
                        st.session_state['usuario'] = user.data[0]
                        st.rerun()
                    else:
                        st.error("Dados incorretos")
                except:
                    st.error("Erro de conexão")
        return

    # Menu Lateral
    st.sidebar.title(f"Olá, {st.session_state['usuario']['nome']}")
    menu = st.sidebar.radio("Navegação", ["Agendamentos", "Novo Cadastro (Completo)", "Buscar Cliente", "Financeiro"])
    
    if st.sidebar.button("Sair"):
        del st.session_state['usuario']
        st.rerun()

    # ---------------------------------------------------------
    # TELA 1: AGENDAMENTOS (A antiga Agenda & PDF)
    # ---------------------------------------------------------
    if menu == "Agendamentos":
        st.title("📅 Agendamentos do Mês")
        
        # Filtro de Data
        c1, c2 = st.columns(2)
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        sel_mes = c1.selectbox("Mês", list(range(1,13)), index=mes_atual-1)
        sel_ano = c2.number_input("Ano", value=ano_atual)
        
        # Buscar agendamentos
        res = supabase.table('agendamentos').select("*, processos(id, clientes(nome))").order('data_hora').execute()
        
        # Filtrar no Python (por simplicidade)
        lista_final = []
        if res.data:
            for ag in res.data:
                dt = pd.to_datetime(ag['data_hora'])
                if dt.month == sel_mes and dt.year == sel_ano:
                    lista_final.append(ag)
        
        if lista_final:
            df = pd.DataFrame(lista_final)
            df['Data'] = pd.to_datetime(df['data_hora']).dt.strftime('%d/%m/%Y %H:%M')
            df['Cliente'] = df['processos'].apply(lambda x: x['clientes']['nome'])
            
            # Exibir Tabela Limpa
            st.dataframe(df[['Data', 'Cliente', 'tipo_evento', 'local_cidade', 'status_comparecimento']], use_container_width=True)
            
            if st.button("📄 Baixar PDF deste mês"):
                arquivo = gerar_pdf_agenda(lista_final, sel_mes, sel_ano)
                st.download_button("Download PDF", arquivo, f"agenda_{sel_mes}_{sel_ano}.pdf", "application/pdf")
        else:
            st.info("Nenhum agendamento encontrado para este mês.")

    # ---------------------------------------------------------
    # TELA 2: NOVO CADASTRO (COMPLETO - ONE STOP SHOP)
    # ---------------------------------------------------------
    elif menu == "Novo Cadastro (Completo)":
        st.title("➕ Cadastro Unificado")
        st.info("Preencha os dados do Cliente e do Processo de uma vez.")
        
        with st.form("form_completo"):
            st.subheader("1. Dados do Cliente")
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo")
            cpf = c2.text_input("CPF")
            data_nasc = c1.date_input("Data Nascimento", value=None)
            email = c2.text_input("Email")
            senha_inss = c1.text_input("Senha Meu INSS")
            colaborador = c2.text_input("Colaborador (Indicação)")
            
            st.divider()
            st.subheader("2. Dados do Processo/Requerimento")
            c3, c4 = st.columns(2)
            servico = c3.selectbox("Qual o Serviço/Benefício?", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria", "Salário Maternidade", "Pensão", "Outro"])
            num_req = c4.text_input("Número do Requerimento (NB)")
            situacao = c3.selectbox("Situação Atual", ["Em Análise", "Em Exigência", "Concedido", "Indeferido", "Aguardando Perícia"])
            
            st.divider()
            st.subheader("3. Agendamentos Iniciais (Opcional)")
            c5, c6 = st.columns(2)
            
            # Perícia
            data_pericia = c5.date_input("Data da Perícia (Médica/Judicial)", value=None)
            hora_pericia = c5.time_input("Hora Perícia", value=time(8,0))
            tipo_pericia = c5.selectbox("Tipo de Perícia", ["Perícia Médica INSS", "Perícia Judicial", "Audiência", "Prorrogação"])
            compareceu_pericia = c5.checkbox("Cliente JÁ compareceu a esta perícia?")
            
            # Avaliação Social
            data_social = c6.date_input("Data Avaliação Social", value=None)
            hora_social = c6.time_input("Hora Av. Social", value=time(8,0))
            compareceu_social = c6.checkbox("Cliente JÁ compareceu a esta avaliação?")
            
            obs = st.text_area("Observações Gerais")
            
            if st.form_submit_button("💾 Salvar Tudo"):
                if not nome or not cpf:
                    st.error("Nome e CPF são obrigatórios.")
                else:
                    try:
                        # 1. Salvar Cliente
                        dados_cli = {
                            "nome": nome, "cpf": cpf, "email": email, 
                            "senha_meu_inss": senha_inss, "colaborador": colaborador,
                            "observacoes": obs
                        }
                        if data_nasc: dados_cli["data_nascimento"] = str(data_nasc)
                        
                        res_cli = supabase.table('clientes').insert(dados_cli).execute()
                        cli_id = res_cli.data[0]['id']
                        
                        # 2. Salvar Processo vinculado
                        dados_proc = {
                            "cliente_id": cli_id,
                            "tipo_beneficio": servico,
                            "numero_requerimento": num_req,
                            "status_processo": situacao,
                            "esfera": "Administrativo" # Padrão inicial
                        }
                        res_proc = supabase.table('processos').insert(dados_proc).execute()
                        proc_id = res_proc.data[0]['id']
                        
                        # 3. Salvar Agendamentos (se houver)
                        # Perícia
                        if data_pericia:
                            dt_full = datetime.combine(data_pericia, hora_pericia).isoformat()
                            status_p = "Compareceu" if compareceu_pericia else "Pendente"
                            supabase.table('agendamentos').insert({
                                "processo_id": proc_id,
                                "tipo_evento": tipo_pericia,
                                "data_hora": dt_full,
                                "local_cidade": "A Definir", # Pode editar depois
                                "status_comparecimento": status_p
                            }).execute()
                            
                        # Avaliação Social
                        if data_social:
                            dt_full_s = datetime.combine(data_social, hora_social).isoformat()
                            status_s = "Compareceu" if compareceu_social else "Pendente"
                            supabase.table('agendamentos').insert({
                                "processo_id": proc_id,
                                "tipo_evento": "Avaliação Social",
                                "data_hora": dt_full_s,
                                "local_cidade": "A Definir",
                                "status_comparecimento": status_s
                            }).execute()
                            
                        st.success(f"Cadastro Completo Realizado! Cliente: {nome}")
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # ---------------------------------------------------------
    # TELA 3: BUSCA (MANTIDA MAS SIMPLIFICADA)
    # ---------------------------------------------------------
    elif menu == "Buscar Cliente":
        st.title("🔍 Base de Clientes")
        termo = st.text_input("Nome ou CPF")
        if termo:
            res = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").execute()
            for cli in res.data:
                with st.expander(f"{cli['nome']} - {cli['status_geral']}"):
                    st.write(f"CPF: {cli['cpf']} | Colaborador: {cli.get('colaborador', '-')}")
                    st.write(f"Senha INSS: {cli['senha_meu_inss']}")
                    
                    # Processos
                    procs = supabase.table('processos').select("*").eq('cliente_id', cli['id']).execute().data
                    st.caption("Processos:")
                    for p in procs:
                        st.info(f"{p['tipo_beneficio']} - Status: {p['status_processo']} (NB: {p['numero_requerimento']})")

    # ---------------------------------------------------------
    # TELA 4: FINANCEIRO (SEM CARTÃO)
    # ---------------------------------------------------------
    elif menu == "Financeiro":
        st.title("💰 Financeiro")
        abas = st.tabs(["Lançar", "Caixa Diário"])
        
        with abas[0]:
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo", ["Entrada", "Saída"])
            valor = c2.number_input("Valor", step=10.0)
            desc = st.text_input("Descrição")
            # REMOVIDO CARTÃO
            forma = st.selectbox("Forma de Pagamento", ["Dinheiro", "Pix", "Depósito"])
            
            if st.button("Lançar Movimentação"):
                supabase.table('caixa').insert({
                    "tipo": tipo, "descricao": desc, "valor": valor, "forma_pagamento": forma,
                    "usuario_responsavel": st.session_state['usuario']['usuario']
                }).execute()
                st.success("Registrado!")
        
        with abas[1]:
            st.write("Últimas movimentações")
            res = supabase.table('caixa').select("*").order('data_movimentacao', desc=True).limit(20).execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data)[['data_movimentacao', 'tipo', 'descricao', 'valor', 'forma_pagamento']])

if __name__ == "__main__":
    main()
