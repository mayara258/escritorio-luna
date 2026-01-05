import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Sistema Luna Alencar", layout="wide", page_icon="⚖️")

# --- CONEXÃO COM O BANCO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.warning("⚠️ Configuração de banco de dados não detectada.")
    st.stop()

# --- FUNÇÕES DE ESTILO (CSS) ---
def aplicar_estilo_menu():
    # Este estilo só é chamado na tela do Menu Principal
    # Ele afeta apenas botões DENTRO de colunas (o grid do menu)
    st.markdown("""
    <style>
        div[data-testid="column"] .stButton button {
            height: 130px;            /* Altura fixa maior */
            width: 100%;              /* Largura total da coluna */
            font-size: 22px;          /* Fonte maior */
            font-weight: 600;         /* Negrito suave */
            border-radius: 12px;      /* Bordas arredondadas */
            border: 1px solid #ddd;   /* Borda sutil */
            transition: all 0.3s;     /* Efeito suave ao passar o mouse */
        }
        
        div[data-testid="column"] .stButton button:hover {
            transform: scale(1.02);   /* Leve aumento ao passar o mouse */
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

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
    pdf.cell(25, 10, "Hora", 1)
    pdf.cell(20, 10, "Tipo", 1)
    pdf.cell(65, 10, "Descricao", 1)
    pdf.cell(30, 10, "Usuario", 1)
    pdf.cell(25, 10, "Valor", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=9)
    total_ent = 0
    total_sai = 0
    
    for item in dados_caixa:
        hora = pd.to_datetime(item['data_movimentacao']).strftime('%H:%M')
        user = item.get('usuario_responsavel', '')[:12]
        desc = item['descricao'][:35].encode('latin-1', 'replace').decode('latin-1')
        val = float(item['valor'])
        
        if item['tipo'] == 'Entrada':
            total_ent += val
            pdf.set_text_color(0, 100, 0)
        else:
            total_sai += val
            pdf.set_text_color(200, 0, 0)
            
        pdf.cell(25, 10, hora, 1)
        pdf.cell(20, 10, item['tipo'], 1)
        pdf.cell(65, 10, desc, 1)
        pdf.cell(30, 10, user, 1)
        pdf.cell(25, 10, f"{val:.2f}", 1)
        pdf.ln()
    
    pdf.set_text_color(0,0,0)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, f"SALDO DO DIA: R$ {total_ent - total_sai:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- TELAS DO SISTEMA ---

def tela_menu_principal():
    aplicar_estilo_menu() # INJETA O CSS DOS BOTÕES GRANDES AQUI
    
    st.title("⚖️ Painel Principal")
    st.write(f"Bem-vindo(a), **{st.session_state['usuario']['nome']}**")
    st.write("") # Espaço extra
    
    # Layout em Grade (2 Colunas Centralizadas)
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("📅 Agendamentos"): st.session_state['page'] = 'agenda'
        if st.button("🔍 Buscar / Editar Cliente"): st.session_state['page'] = 'busca'
        if st.button("💰 Financeiro"): st.session_state['page'] = 'financeiro'
    
    with c2:
        if st.button("➕ Novo Cadastro"): st.session_state['page'] = 'cadastro'
        
        # Lógica para mostrar botão de admin ou um espaço vazio para manter o grid alinhado
        if st.session_state['usuario'].get('perfil') == 'admin':
            if st.button("👥 Gestão de Usuários"): st.session_state['page'] = 'usuarios'
        else:
            # Botão invisível/desativado apenas para ocupar espaço e alinhar o grid se quiser, 
            # ou simplesmente não colocar nada. Optei por não colocar nada, o grid se ajusta.
            pass
        
        if st.button("🔒 Alterar Minha Senha"): st.session_state['page'] = 'senha'

    st.divider()
    
    # Este botão está FORA das colunas c1/c2, então o CSS não afeta ele (volta ao tamanho normal)
    # Usamos type="primary" para ficar vermelho/destacado
    if st.button("Sair do Sistema", type="primary"): 
        st.session_state.clear()
        st.rerun()

def tela_voltar():
    # Botão padrão pequeno
    if st.button("⬅️ Voltar ao Menu"):
        st.session_state['page'] = 'menu'
        st.rerun()

def tela_cadastro():
    tela_voltar()
    st.title("➕ Novo Cadastro")
    
    with st.form("form_completo"):
        st.subheader("1. Dados do Cliente")
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome Completo")
        cpf = c2.text_input("CPF")
        data_nasc = c1.date_input("Data Nascimento", value=None, format="DD/MM/YYYY")
        email = c2.text_input("Email")
        senha_inss = c1.text_input("Senha Meu INSS")
        colaborador = c2.text_input("Colaborador (Indicação)")
        
        st.divider()
        st.subheader("2. Dados do Processo")
        c3, c4 = st.columns(2)
        servico = c3.selectbox("Serviço", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria", "Salário Maternidade", "Pensão", "Outro"])
        num_req = c4.text_input("Nº Requerimento (NB)")
        situacao = c3.selectbox("Situação", ["Em Análise", "Em Exigência", "Concedido", "Indeferido", "Aguardando Perícia"])
        
        if st.form_submit_button("💾 Salvar Cadastro"):
            if not nome:
                st.error("Nome é obrigatório.")
            else:
                try:
                    d_nasc = str(data_nasc) if data_nasc else None
                    res_cli = supabase.table('clientes').insert({
                        "nome": nome, "cpf": cpf, "email": email, 
                        "senha_meu_inss": senha_inss, "colaborador": colaborador,
                        "data_nascimento": d_nasc
                    }).execute()
                    cli_id = res_cli.data[0]['id']
                    
                    supabase.table('processos').insert({
                        "cliente_id": cli_id, "tipo_beneficio": servico,
                        "numero_requerimento": num_req, "status_processo": situacao
                    }).execute()
                    st.success("Cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro: {e}")

def tela_busca_edicao():
    tela_voltar()
    st.title("🔍 Buscar e Editar")
    
    termo = st.text_input("Pesquisar Cliente (Nome ou CPF)")
    
    if termo:
        res = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").order('nome').execute()
        
        for cli in res.data:
            colab_txt = f" | Indicado por: {cli['colaborador']}" if cli.get('colaborador') else ""
            
            with st.expander(f"👤 {cli['nome']} {colab_txt}"):
                # --- EDIÇÃO DO CLIENTE ---
                with st.form(key=f"edit_cli_{cli['id']}"):
                    st.write("**Dados Pessoais**")
                    c1, c2 = st.columns(2)
                    n_nome = c1.text_input("Nome", value=cli['nome'])
                    n_cpf = c2.text_input("CPF", value=cli['cpf'])
                    n_email = c1.text_input("Email", value=cli['email'])
                    n_senha = c2.text_input("Senha INSS", value=cli['senha_meu_inss'])
                    
                    if st.form_submit_button("Atualizar Dados Pessoais"):
                        supabase.table('clientes').update({
                            "nome": n_nome, "cpf": n_cpf, "email": n_email, "senha_meu_inss": n_senha
                        }).eq('id', cli['id']).execute()
                        st.success("Cliente atualizado!")
                        st.rerun()
                
                # --- LISTA E EDIÇÃO DE PROCESSOS ---
                st.divider()
                st.write("**Processos**")
                procs = supabase.table('processos').select
