import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Jurídica", layout="wide", page_icon="⚖️")

# --- CONEXÃO COM O BANCO (SUPABASE) ---
# O Streamlit vai buscar essas chaves nos "Segredos" (não coloque a senha aqui!)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.warning("⚠️ Configuração de banco de dados não detectada.")
    st.stop()

# --- FUNÇÕES DE LOGIN ---
def check_login(usuario, senha):
    try:
        response = supabase.table('usuarios').select("*").eq('usuario', usuario).eq('senha', senha).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

# --- TELAS DO SISTEMA ---

def tela_login():
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("⚖️ Acesso Restrito")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            user_data = check_login(usuario, senha)
            if user_data:
                st.session_state['logado'] = True
                st.session_state['usuario'] = user_data
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

def tela_dashboard():
    st.sidebar.title(f"Olá, {st.session_state['usuario']['nome']}")
    menu = st.sidebar.radio("Navegação", ["Início/Busca", "Cadastrar Cliente", "Agenda/Perícias", "Financeiro & Caixa"])
    
    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    if menu == "Início/Busca":
        st.title("🗂️ Gestão de Clientes")
        
        # Busca inteligente
        termo = st.text_input("🔍 Pesquisar Cliente (Nome ou CPF)", placeholder="Digite para buscar...")
        
        if termo:
            # Busca clientes
            response = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").execute()
            clientes = response.data
            
            if not clientes:
                st.info("Nenhum cliente encontrado.")
            
            for cli in clientes:
                with st.expander(f"👤 {cli['nome']} (CPF: {cli['cpf']}) - Status: {cli['status_geral']}"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Email:** {cli['email']}")
                    c1.write(f"**Telefone:** {cli['telefone']}")
                    c2.write(f"**Meu INSS:** {cli['senha_meu_inss']}")
                    c2.write(f"**Obs:** {cli['observacoes']}")
                    
                    # Buscar Processos deste cliente
                    procs = supabase.table('processos').select("*").eq('cliente_id', cli['id']).execute().data
                    if procs:
                        st.markdown("---")
                        st.subheader("📂 Processos / Requerimentos")
                        for p in procs:
                            st.info(f"**{p['tipo_beneficio']}** ({p['esfera']}) - Status: **{p['status_processo']}**")
                            # Buscar Agendamentos deste processo
                            agendas = supabase.table('agendamentos').select("*").eq('processo_id', p['id']).execute().data
                            if agendas:
                                for a in agendas:
                                    st.warning(f"📅 **{a['tipo_evento']}**: {a['data_hora']} em {a['local_cidade']}. Situação: {a['status_comparecimento']}")

    elif menu == "Cadastrar Cliente":
        st.title("➕ Novo Cliente")
        with st.form("form_cliente"):
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF")
            nasc = st.date_input("Data Nascimento", value=None)
            tel = st.text_input("Telefone")
            email = st.text_input("Email")
            senha_inss = st.text_input("Senha Meu INSS")
            obs = st.text_area("Observações Iniciais")
            submitted = st.form_submit_button("Salvar Cliente")
            
            if submitted:
                try:
                    data = {"nome": nome, "cpf": cpf, "telefone": tel, "email": email, "senha_meu_inss": senha_inss, "observacoes": obs}
                    if nasc: data["data_nascimento"] = str(nasc)
                    supabase.table('clientes').insert(data).execute()
                    st.success("Cliente cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    elif menu == "Agenda/Perícias":
        st.title("📅 Agenda Geral")
        # Listar agendamentos futuros
        # (Aqui faremos uma query para trazer agendamentos ordenados)
        agendas = supabase.table('agendamentos').select("*, processos(id, tipo_beneficio, clientes(nome))").order('data_hora').execute().data
        
        if agendas:
            df = pd.DataFrame(agendas)
            # Tratamento simples para exibir na tabela
            st.dataframe(df)
        else:
            st.info("Nenhum agendamento futuro encontrado.")

    elif menu == "Financeiro & Caixa":
        st.title("💰 Financeiro")
        abas = st.tabs(["Livro Caixa (Diário)", "Lançar Entrada/Saída"])
        
        with abas[0]:
            st.write("Movimentações Recentes")
            cx = supabase.table('caixa').select("*").order('data_movimentacao', desc=True).limit(20).execute().data
            if cx:
                st.dataframe(pd.DataFrame(cx))
                
        with abas[1]:
            st.subheader("Novo Lançamento")
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            desc = st.text_input("Descrição (Ex: Honorários Dona Maria)")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            forma = st.selectbox("Forma", ["Dinheiro", "Pix", "Depósito", "Cartão"])
            
            if st.button("Lançar no Caixa"):
                supabase.table('caixa').insert({
                    "tipo": tipo, "descricao": desc, "valor": valor, 
                    "forma_pagamento": forma, "usuario_responsavel": st.session_state['usuario']['usuario']
                }).execute()
                st.success("Lançado!")

# --- CONTROLE DE FLUXO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    tela_login()
else:
    tela_dashboard()
