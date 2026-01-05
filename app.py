import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Jurídica - Luna Alencar", layout="wide", page_icon="⚖️")

# --- CONEXÃO COM O BANCO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.warning("⚠️ Configuração de banco de dados não detectada.")
    st.stop()

# --- FUNÇÕES ÚTEIS ---
def check_login(usuario, senha):
    try:
        response = supabase.table('usuarios').select("*").eq('usuario', usuario).eq('senha', senha).execute()
        return response.data[0] if response.data else None
    except:
        return None

def upload_arquivo(arquivo, nome_arquivo):
    # Envia arquivo para o bucket 'documentos' no Supabase
    try:
        # Lê o arquivo em bytes
        file_bytes = arquivo.getvalue()
        path = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{nome_arquivo}"
        supabase.storage.from_("documentos").upload(path, file_bytes, {"content-type": arquivo.type})
        return path
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return None

def gerar_pdf_agenda(dados_agenda):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Relatório de Agendamentos - Luna Alencar Advogados", ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho da tabela
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Data/Hora", 1)
    pdf.cell(50, 10, "Cliente", 1)
    pdf.cell(50, 10, "Evento", 1)
    pdf.cell(50, 10, "Local", 1)
    pdf.ln()
    
    # Dados
    pdf.set_font("Arial", size=10)
    for item in dados_agenda:
        # Tratamento de caracteres para evitar erro no PDF (latin-1)
        data_fmt = pd.to_datetime(item['data_hora']).strftime('%d/%m/%Y %H:%M')
        cliente = item['processos']['clientes']['nome'][:25].encode('latin-1', 'replace').decode('latin-1')
        evento = item['tipo_evento'][:25].encode('latin-1', 'replace').decode('latin-1')
        local = item['local_cidade'][:25].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(40, 10, data_fmt, 1)
        pdf.cell(50, 10, cliente, 1)
        pdf.cell(50, 10, evento, 1)
        pdf.cell(50, 10, local, 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- TELAS DO SISTEMA ---

def tela_login():
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("⚖️ Luna Alencar")
        st.write("Acesso Restrito ao Sistema")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            user = check_login(usuario, senha)
            if user:
                st.session_state['logado'] = True
                st.session_state['usuario'] = user
                st.rerun()
            else:
                st.error("Dados incorretos.")

def tela_dashboard():
    st.sidebar.title(f"👤 {st.session_state['usuario']['nome']}")
    menu = st.sidebar.radio("Menu", ["🔍 Busca & Clientes", "➕ Novo Cliente", "📅 Agenda & PDF", "💰 Financeiro"])
    
    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    # --- TELA 1: BUSCA E GESTÃO DE CLIENTES ---
    if menu == "🔍 Busca & Clientes":
        st.title("🗂️ Gestão de Clientes")
        termo = st.text_input("Pesquisar (Nome ou CPF)", placeholder="Digite...")
        
        if termo:
            res = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").order('nome').execute()
            clientes = res.data
            
            if not clientes: st.info("Nada encontrado.")
            
            for cli in clientes:
                cor_status = "red" if cli['status_geral'] == 'Arquivado' else "green"
                with st.expander(f":{cor_status}[{cli['status_geral']}] - {cli['nome']} (CPF: {cli['cpf']})"):
                    # Detalhes do Cliente
                    c1, c2 = st.columns(2)
                    c1.write(f"**Email:** {cli['email']}")
                    c1.write(f"**Tel:** {cli['telefone']}")
                    c2.write(f"**Senha INSS:** {cli['senha_meu_inss']}")
                    c2.write(f"**Obs:** {cli['observacoes']}")
                    
                    # Botão de Arquivar
                    if cli['status_geral'] == 'Ativo':
                        with st.popover("📁 Arquivar Cliente"):
                            motivo = st.text_input("Motivo do arquivamento")
                            if st.button("Confirmar Arquivamento"):
                                supabase.table('clientes').update({'status_geral': 'Arquivado', 'motivo_arquivamento': motivo}).eq('id', cli['id']).execute()
                                st.success("Cliente arquivado!")
                                st.rerun()
                    else:
                        st.warning(f"Cliente Arquivado. Motivo: {cli.get('motivo_arquivamento', '-')}")

                    st.divider()
                    
                    # Gestão de Processos
                    st.subheader("Processos")
                    procs = supabase.table('processos').select("*").eq('cliente_id', cli['id']).execute().data
                    
                    for p in procs:
                        st.info(f"📌 **{p['tipo_beneficio']}** ({p['esfera']}) - Status: **{p['status_processo']}**")
                        # Botão para atualizar status do processo
                        novo_status = st.selectbox("Atualizar Status:", ["Em Análise", "Exigência", "Perícia Agendada", "Concedido", "Indeferido"], key=f"st_{p['id']}")
                        if st.button("Salvar Status", key=f"bt_{p['id']}"):
                            supabase.table('processos').update({'status_processo': novo_status}).eq('id', p['id']).execute()
                            st.success("Atualizado!")
                            st.rerun()

                    # Adicionar Novo Processo (Rápido)
                    with st.form(key=f"novo_proc_{cli['id']}"):
                        st.write("➕ **Adicionar Novo Processo para este cliente**")
                        col_a, col_b = st.columns(2)
                        tipo = col_a.selectbox("Benefício", ["BPC/LOAS", "Aposentadoria", "Auxílio Doença", "Salário Maternidade"])
                        esfera = col_b.selectbox("Esfera", ["Administrativo", "Judicial", "Ambos"])
                        if st.form_submit_button("Criar Processo"):
                            supabase.table('processos').insert({'cliente_id': cli['id'], 'tipo_beneficio': tipo, 'esfera': esfera}).execute()
                            st.rerun()

    # --- TELA 2: CADASTRO ---
    elif menu == "➕ Novo Cliente":
        st.title("Novo Cadastro")
        with st.form("cad_cli"):
            nome = st.text_input("Nome *")
            cpf = st.text_input("CPF")
            tel = st.text_input("Telefone")
            email = st.text_input("Email")
            senha_inss = st.text_input("Senha Meu INSS")
            obs = st.text_area("Observações")
            if st.form_submit_button("Salvar"):
                supabase.table('clientes').insert({"nome": nome, "cpf": cpf, "telefone": tel, "email": email, "senha_meu_inss": senha_inss, "observacoes": obs}).execute()
                st.success("Salvo com sucesso!")

    # --- TELA 3: AGENDA E PDF ---
    elif menu == "📅 Agenda & PDF":
        st.title("Agenda de Perícias e Prazos")
        
        # Filtros
        col_f1, col_f2 = st.columns(2)
        mes = col_f1.selectbox("Filtrar Mês", [1,2,3,4,5,6,7,8,9,10,11,12], index=datetime.now().month-1)
        ano = col_f2.number_input("Ano", value=2026)
        
        # Buscar dados filtrados (Query mais complexa)
        # Nota: O Supabase Free tem limites de query, vamos trazer tudo e filtrar no python por simplicidade
        res = supabase.table('agendamentos').select("*, processos(id, clientes(nome))").order('data_hora').execute()
        todos_agendamentos = res.data
        
        # Filtrar no Python
        agendas_filtradas = [a for a in todos_agendamentos if pd.to_datetime(a['data_hora']).month == mes and pd.to_datetime(a['data_hora']).year == ano]
        
        if agendas_filtradas:
            st.write(f"Found {len(agendas_filtradas)} agendamentos.")
            df = pd.DataFrame(agendas_filtradas)
            df['Cliente'] = df['processos'].apply(lambda x: x['clientes']['nome'] if x and x['clientes'] else 'Desconhecido')
            st.dataframe(df[['data_hora', 'Cliente', 'tipo_evento', 'local_cidade', 'status_comparecimento']])
            
            # Botão Gerar PDF
            if st.button("📄 Baixar PDF Deste Mês"):
                pdf_bytes = gerar_pdf_agenda(agendas_filtradas)
                st.download_button(label="Download PDF", data=pdf_bytes, file_name=f"agenda_{mes}_{ano}.pdf", mime='application/pdf')
        else:
            st.info("Nenhum agendamento para este mês.")

        # Novo Agendamento
        st.divider()
        st.subheader("Novo Agendamento")
        # Precisa selecionar um processo primeiro. Listamos os últimos 20 processos ativos.
        procs_ativos = supabase.table('processos').select("id, tipo_beneficio, clientes(nome)").limit(20).execute().data
        opcoes = {p['id']: f"{p['clientes']['nome']} - {p['tipo_beneficio']}" for p in procs_ativos}
        
        pid = st.selectbox("Selecione o Processo", options=list(opcoes.keys()), format_func=lambda x: opcoes[x])
        c1, c2, c3 = st.columns(3)
        evento = c1.selectbox("Tipo", ["Perícia Médica", "Avaliação Social", "Prorrogação", "Audiência"])
        data = c2.date_input("Data")
        hora = c3.time_input("Hora")
        local = st.text_input("Local (Cidade/Endereço)")
        
        if st.button("Agendar"):
            dt_full = datetime.combine(data, hora).isoformat()
            supabase.table('agendamentos').insert({'processo_id': pid, 'tipo_evento': evento, 'data_hora': dt_full, 'local_cidade': local}).execute()
            st.success("Agendado!")
            st.rerun()

    # --- TELA 4: FINANCEIRO ---
    elif menu == "💰 Financeiro":
        st.title("Fluxo de Caixa")
        
        tab1, tab2 = st.tabs(["Lançamentos", "Histórico"])
        
        with tab1:
            st.subheader("Registrar Entrada/Saída")
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor R$", step=10.0)
            forma = st.selectbox("Forma", ["Dinheiro", "Pix", "Depósito"])
            arquivo = st.file_uploader("Comprovante (Opcional)", type=['png', 'jpg', 'pdf'])
            
            if st.button("Lançar"):
                path_arquivo = None
                if arquivo:
                    path_arquivo = upload_arquivo(arquivo, arquivo.name)
                
                supabase.table('caixa').insert({
                    'tipo': tipo, 'descricao': desc, 'valor': val, 
                    'forma_pagamento': forma, 'usuario_responsavel': st.session_state['usuario']['usuario']
                    # Futuro: salvar link do comprovante se criarmos coluna na tabela caixa
                }).execute()
                st.success("Lançamento registrado!")
        
        with tab2:
            cx = supabase.table('caixa').select("*").order('data_movimentacao', desc=True).limit(50).execute().data
            if cx:
                st.dataframe(pd.DataFrame(cx))
                total = sum([c['valor'] if c['tipo'] == 'Entrada' else -c['valor'] for c in cx])
                st.metric("Saldo do Período (Visualizado)", f"R$ {total:.2f}")

# --- CONTROLE DE LOGIN ---
if 'logado' not in st.session_state: st.session_state['logado'] = False

if st.session_state['logado']:
    tela_dashboard()
else:
    tela_login()
