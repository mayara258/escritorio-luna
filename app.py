import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Luna Alencar Advogados", layout="wide", page_icon="⚖️")

# --- CONEXÃO COM O BANCO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.warning("⚠️ Configuração de banco de dados não detectada.")
    st.stop()

# --- ESTILO CSS (TEXTO BRANCO E BOTÕES CENTRALIZADOS) ---
def aplicar_estilo_visual():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif;
        }

        /* --- FUNDO GERAL --- */
        .stApp {
            background-color: #2E2522; 
            color: #FFFFFF !important;
        }

        /* --- BOTÕES DO MENU (GIGANTES E COM TEXTO BRANCO) --- */
        div[data-testid="column"] .stButton button {
            width: 100% !important;
            height: 220px !important; 
            
            background-color: #C5A065 !important; /* DOURADO */
            color: #FFFFFF !important;            /* TEXTO BRANCO FORÇADO */
            
            font-size: 22px !important;
            font-weight: 800 !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 15px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
            
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase;
            white-space: pre-wrap !important;
            margin-bottom: 20px !important;
        }
        
        div[data-testid="column"] .stButton button:hover {
            background-color: #D4AF37 !important; 
            transform: translateY(-5px) !important;
            box-shadow: 0 15px 35px rgba(197, 160, 101, 0.4) !important;
        }

        /* --- FORÇAR COR BRANCA EM TODOS OS TEXTOS E LABELS --- */
        .stTextInput label, .stSelectbox label, .stDateInput label, 
        .stNumberInput label, .stTextArea label, p, span, .stMarkdown {
            color: #FFFFFF !important;
        }

        /* Cor do texto dentro dos campos de entrada */
        input, select, textarea, div[data-baseweb="select"] {
            color: #FFFFFF !important;
            background-color: #3A302C !important;
        }

        /* --- TÍTULOS --- */
        h1, h2, h3, h4 {
            color: #FFFFFF !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        /* --- BOTÕES DE AÇÃO --- */
        button[kind="primary"] {
            background-color: #C5A065 !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
def mostrar_cabecalho():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        try:
            st.image("LOGO lUNA ALENCAR.png", use_container_width=True) 
        except:
            st.markdown("<h1 style='text-align:center;'>LUNA ALENCAR</h1>", unsafe_allow_html=True)
    st.write("")

# --- FUNÇÕES ÚTEIS ---
def formatar_data(data_iso):
    if not data_iso: return ""
    return pd.to_datetime(data_iso).strftime('%d/%m/%Y')

def formatar_data_hora(data_iso):
    if not data_iso: return ""
    return pd.to_datetime(data_iso).strftime('%d/%m/%Y %H:%M')

def gerar_pdf_caixa(dados_caixa, data_escolhida):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    data_str = data_escolhida.strftime('%d/%m/%Y')
    pdf.cell(200, 10, txt=f"Movimento de Caixa - {data_str}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(25, 10, "Data", 1) 
    pdf.cell(20, 10, "Tipo", 1)
    pdf.cell(65, 10, "Descricao", 1)
    pdf.cell(30, 10, "Usuario", 1)
    pdf.cell(25, 10, "Valor", 1)
    pdf.ln()
    pdf.set_font("Arial", size=9)
    total_ent, total_sai = 0, 0
    for item in dados_caixa:
        data_mov = pd.to_datetime(item['data_movimentacao']).strftime('%d/%m/%Y')
        user = item.get('usuario_responsavel', '')[:12]
        desc = item['descricao'][:35].encode('latin-1', 'replace').decode('latin-1')
        val = float(item['valor'])
        if item['tipo'] == 'Entrada':
            total_ent += val
            pdf.set_text_color(0, 100, 0)
        else:
            total_sai += val
            pdf.set_text_color(200, 0, 0)
        pdf.cell(25, 10, data_mov, 1) 
        pdf.cell(20, 10, item['tipo'], 1)
        pdf.cell(65, 10, desc, 1)
        pdf.cell(30, 10, user, 1)
        pdf.cell(25, 10, f"{val:.2f}", 1)
        pdf.ln()
    pdf.set_text_color(0,0,0)
    pdf.ln(10)
    pdf.cell(200, 10, f"SALDO DO DIA: R$ {total_ent - total_sai:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- TELAS ---
def tela_menu_principal():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    st.markdown(f"<h4 style='text-align: center;'>Bem-vindo(a), {st.session_state['usuario']['nome']}</h4>", unsafe_allow_html=True)
    
    # Grade centralizada [2,3,3,2] aproxima os botões
    c_esq, c1, c2, c_dir = st.columns([2, 3, 3, 2], gap="medium")
    
    with c1:
        if st.button("📅\n\nAGENDAMENTOS", key="bt_age"): 
            st.session_state['page'] = 'agenda'; st.rerun()
        if st.button("💰\n\nFINANCEIRO", key="bt_fin"): 
            st.session_state['page'] = 'financeiro'; st.rerun()
        if st.session_state['usuario'].get('perfil') == 'admin':
            if st.button("👥\n\nUSUÁRIOS", key="bt_user"): 
                st.session_state['page'] = 'usuarios'; st.rerun()

    with c2:
        if st.button("🔍\n\nBUSCAR / EDITAR", key="bt_bus"): 
            st.session_state['page'] = 'busca'; st.rerun()
        if st.button("➕\n\nNOVO CADASTRO", key="bt_cad"): 
            st.session_state['page'] = 'cadastro'; st.rerun()
        if st.button("🔒\n\nMEUS DADOS", key="bt_pass"): 
            st.session_state['page'] = 'meus_dados'; st.rerun()

    st.divider()
    col_s1, col_s2, col_s3 = st.columns([1,1,1])
    with col_s2:
        if st.button("SAIR DO SISTEMA", type="primary", use_container_width=True): 
            st.session_state.clear(); st.rerun()

def tela_voltar():
    if st.button("⬅️ VOLTAR AO MENU"):
        st.session_state['page'] = 'menu'; st.rerun()

def tela_cadastro():
    aplicar_estilo_visual(); mostrar_cabecalho(); tela_voltar()
    st.markdown("<h2 style='text-align: center;'>Novo Cadastro</h2>", unsafe_allow_html=True)
    with st.form("form_completo"):
        st.markdown("### 1. Dados do Cliente")
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome Completo")
        cpf = c2.text_input("CPF")
        data_nasc = c1.date_input("Data Nascimento", value=None, format="DD/MM/YYYY")
        email = c2.text_input("Email")
        senha_inss = c1.text_input("Senha Meu INSS")
        colaborador = c2.text_input("Colaborador (Indicação)")
        
        st.divider()
        st.markdown("### 2. Dados do Processo")
        c3, c4, c5 = st.columns(3)
        servico = c3.selectbox("Serviço", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria", "Salário Maternidade", "Pensão", "Outro"])
        num_req = c4.text_input("Nº Requerimento (NB)")
        esfera = c5.selectbox("Esfera", ["Administrativo", "Judicial"])
        situacao = st.selectbox("Situação Atual", ["Em Análise", "Em Exigência", "Concedido", "Indeferido", "Aguardando Perícia"])
        
        if st.form_submit_button("💾 SALVAR CADASTRO", type="primary", use_container_width=True):
            if not nome: st.error("Nome é obrigatório.")
            else:
                try:
                    res_cli = supabase.table('clientes').insert({"nome": nome, "cpf": cpf, "email": email, "senha_meu_inss": senha_inss, "colaborador": colaborador, "data_nascimento": str(data_nasc) if data_nasc else None}).execute()
                    cli_id = res_cli.data[0]['id']
                    supabase.table('processos').insert({"cliente_id": cli_id, "tipo_beneficio": servico, "numero_requerimento": num_req, "status_processo": situacao, "esfera": esfera}).execute()
                    st.success(f"Cadastro realizado: {nome}"); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

def tela_busca_edicao():
    aplicar_estilo_visual(); mostrar_cabecalho(); tela_voltar()
    st.markdown("<h2 style='text-align: center;'>Buscar e Editar</h2>", unsafe_allow_html=True)
    termo = st.text_input("Pesquisar Cliente (Nome ou CPF)")
    if termo:
        res = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").execute()
        for cli in res.data:
            with st.expander(f"👤 {cli['nome']}"):
                with st.form(key=f"ed_{cli['id']}"):
                    n_nome = st.text_input("Nome", value=cli['nome'])
                    n_cpf = st.text_input("CPF", value=cli['cpf'])
                    if st.form_submit_button("ATUALIZAR"):
                        supabase.table('clientes').update({"nome": n_nome, "cpf": n_cpf}).eq('id', cli['id']).execute()
                        st.success("Atualizado!"); st.rerun()

def tela_agenda():
    aplicar_estilo_visual(); mostrar_cabecalho(); tela_voltar()
    st.markdown("<h2 style='text-align: center;'>Agenda</h2>", unsafe_allow_html=True)
    res = supabase.table('agendamentos').select("*, processos(clientes(nome))").execute()
    if res.data:
        df = pd.DataFrame([{"Data": formatar_data_hora(a['data_hora']), "Cliente": a['processos']['clientes']['nome'], "Evento": a['tipo_evento']} for a in res.data])
        st.dataframe(df, use_container_width=True)
    else: st.info("Sem agendamentos.")

def tela_financeiro():
    aplicar_estilo_visual(); mostrar_cabecalho(); tela_voltar()
    st.markdown("<h2 style='text-align: center;'>Financeiro</h2>", unsafe_allow_html=True)
    aba1, aba2 = st.tabs(["Caixa", "Honorários"])
    with aba1:
        st.subheader("Movimento do Dia")
        l_tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
        l_val = st.number_input("Valor", step=10.0)
        l_desc = st.text_input("Descrição")
        if st.button("Lançar"):
            supabase.table('caixa').insert({"tipo": l_tipo, "valor": l_val, "descricao": l_desc, "usuario_responsavel": st.session_state['usuario']['usuario'], "data_movimentacao": datetime.now().isoformat()}).execute()
            st.rerun()

def tela_usuarios():
    aplicar_estilo_visual(); mostrar_cabecalho(); tela_voltar()
    st.title("Gestão de Usuários")
    with st.form("u"):
        un = st.text_input("Nome"); ul = st.text_input("Login"); us = st.text_input("Senha")
        if st.form_submit_button("Criar"):
            supabase.table('usuarios').insert({"nome": un, "usuario": ul, "senha": us, "perfil": "comum"}).execute()
            st.success("Criado!")

def tela_meus_dados():
    aplicar_estilo_visual(); mostrar_cabecalho(); tela_voltar()
    st.title("Meus Dados")
    meu_id = st.session_state['usuario']['id']
    with st.form("m"):
        n_n = st.text_input("Nome", value=st.session_state['usuario']['nome'])
        n_s = st.text_input("Nova Senha", type="password")
        if st.form_submit_button("Salvar"):
            supabase.table('usuarios').update({"nome": n_n, "senha": n_s}).eq('id', meu_id).execute()
            st.session_state['usuario']['nome'] = n_n
            st.success("Alterado!")

def main():
    if 'usuario' not in st.session_state:
        aplicar_estilo_visual()
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("<h2 style='text-align:center;'>ACESSO</h2>", unsafe_allow_html=True)
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.button("ENTRAR", use_container_width=True, type="primary"):
                res = supabase.table('usuarios').select("*").eq('usuario', u).eq('senha', s).execute()
                if res.data:
                    st.session_state['usuario'] = res.data[0]
                    st.session_state['page'] = 'menu'; st.rerun()
                else: st.error("Incorreto")
    else:
        pg = st.session_state.get('page', 'menu')
        if pg == 'menu': tela_menu_principal()
        elif pg == 'cadastro': tela_cadastro()
        elif pg == 'busca': tela_busca_edicao()
        elif pg == 'agenda': tela_agenda()
        elif pg == 'financeiro': tela_financeiro()
        elif pg == 'usuarios': tela_usuarios()
        elif pg == 'meus_dados': tela_meus_dados()

if __name__ == "__main__":
    main()
