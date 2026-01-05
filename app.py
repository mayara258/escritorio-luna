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

# --- ESTILO CSS (BOTÕES GIGANTES, QUADRADOS E ALINHADOS) ---
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
            color: #E0E0E0;
        }

        /* --- BOTÕES DO MENU (GIGANTES E ALINHADOS) --- */
        div[data-testid="column"] .stButton button {
            width: 100% !important;
            height: 240px !important;     /* ALTURA GIGANTE FIXA */
            
            background-color: #C5A065 !important; /* DOURADO */
            color: #1E1B18 !important;            /* PRETO */
            
            font-size: 24px !important;
            font-weight: 800 !important;
            border: none !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.6) !important;
            
            /* Centralização Total */
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            
            transition: all 0.3s ease !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            white-space: pre-wrap !important;
            margin-bottom: 25px !important;
        }
        
        div[data-testid="column"] .stButton button:hover {
            background-color: #D4AF37 !important; 
            transform: scale(1.02) !important;
            box-shadow: 0 15px 40px rgba(197, 160, 101, 0.4) !important;
            color: #000000 !important;
            z-index: 999;
        }

        /* --- BOTÕES DE AÇÃO (Sair, Salvar) --- */
        button[kind="primary"] {
            background-color: #C5A065 !important;
            color: #1E1B18 !important;
            border: none !important;
            font-weight: bold !important;
            text-transform: uppercase;
            height: 50px !important;
            border-radius: 6px !important;
        }
        button[kind="primary"]:hover {
            background-color: #E6CFA0 !important;
        }
        
        button[kind="secondary"] {
            background-color: transparent !important;
            color: #C5A065 !important;
            border: 1px solid #C5A065 !important;
            height: 50px !important;
        }

        /* --- INPUTS --- */
        .stTextInput input, .stSelectbox div, .stDateInput input, .stTimeInput input, .stTextArea textarea, .stNumberInput input {
            background-color: #3A302C !important; 
            color: #FFFFFF !important;
            border: 1px solid #5C4B3C !important;
            border-radius: 6px !important;
        }
        
        /* --- TEXTOS BRANCOS --- */
        .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label {
            color: #FFFFFF !important;
            font-size: 16px !important;
        }
        
        /* --- TÍTULOS --- */
        h1, h2, h3 {
            color: #C5A065 !important;
        }
        
        /* --- CARDS --- */
        [data-testid="stExpander"] {
            background-color: #3A302C !important;
            border: 1px solid #5C4B3C !important;
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
            st.markdown("<h1 style='text-align:center; color:#C5A065;'>LUNA ALENCAR</h1>", unsafe_allow_html=True)
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
    total_ent = 0
    total_sai = 0
    
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
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, f"SALDO DO DIA: R$ {total_ent - total_sai:.2f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- TELAS DO SISTEMA ---

def tela_menu_principal():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    
    st.markdown(f"<h4 style='text-align: center; color: #E0E0E0; font-weight: 300;'>Bem-vindo(a), {st.session_state['usuario']['nome']}</h4>", unsafe_allow_html=True)
    st.write("") 
    
    # --- LAYOUT EM GRADES 3x2 ---
    # Colunas: [Espaço, Botão, Botão, Espaço]
    c_esq, c1, c2, c_dir = st.columns([1, 3, 3, 1], gap="large")
    
    # LINHA 1
    with c1:
        if st.button("📅\n\nAGENDAMENTOS", key="bt_age"): 
            st.session_state['page'] = 'agenda'
            st.rerun()
    with c2:
        if st.button("🔍\n\nBUSCAR / EDITAR", key="bt_bus"): 
            st.session_state['page'] = 'busca'
            st.rerun()
            
    # LINHA 2
    with c1:
        if st.button("💰\n\nFINANCEIRO", key="bt_fin"): 
            st.session_state['page'] = 'financeiro'
            st.rerun()
    with c2:
        if st.button("➕\n\nNOVO CADASTRO", key="bt_cad"): 
            st.session_state['page'] = 'cadastro'
            st.rerun()
            
    # LINHA 3 (Usuários e Senha)
    with c1:
        if st.session_state['usuario'].get('perfil') == 'admin':
            if st.button("👥\n\nUSUÁRIOS", key="bt_user"): 
                st.session_state['page'] = 'usuarios'
                st.rerun()
        else:
            # Espaço vazio mantendo o layout
            st.markdown("<div style='height: 240px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    with c2:
        if st.button("🔒\n\nMEUS DADOS", key="bt_pass"): 
            st.session_state['page'] = 'meus_dados'
            st.rerun()

    st.write("")
    st.write("")
    st.divider()
    
    # Botão Sair menor e centralizado
    col_s1, col_s2, col_s3 = st.columns([1,1,1])
    with col_s2:
        if st.button("SAIR DO SISTEMA", type="primary", use_container_width=True): 
            st.session_state.clear()
            st.rerun()

def tela_voltar():
    if st.button("⬅️ VOLTAR AO MENU", type="secondary"):
        st.session_state['page'] = 'menu'
        st.rerun()

def tela_cadastro():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    tela_voltar()
    
    st.markdown("<h2 style='text-align: center;'>Novo Cadastro</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
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
            
            st.divider()
            st.markdown("### 3. Agendamentos Iniciais")
            
            col_p, col_s = st.columns(2)
            
            with col_p:
                st.info("🩺 **Perícia / Audiência**")
                tipo_pericia = st.selectbox("Tipo", ["Perícia Médica INSS", "Perícia Judicial", "Audiência", "Prorrogação"])
                local_pericia = st.text_input("Local da Perícia", value="Agência INSS")
                data_pericia = st.date_input("Data Perícia", value=None, format="DD/MM/YYYY")
                hora_pericia = st.time_input("Hora Perícia", value=time(8,0))
                check_pericia = st.checkbox("Já compareceu nesta Perícia?")
                
            with col_s:
                st.info("📋 **Avaliação Social**")
                tipo_social = st.selectbox("Tipo da Avaliação", ["Avaliação Social INSS", "Avaliação Social Judicial"])
                local_social = st.text_input("Local da Avaliação", value="Agência INSS")
                data_social = st.date_input("Data Avaliação", value=None, format="DD/MM/YYYY")
                hora_social = st.time_input("Hora Avaliação", value=time(8,0))
                check_social = st.checkbox("Já compareceu na Avaliação?")

            st.write("")
            if st.form_submit_button("💾 SALVAR CADASTRO", type="primary", use_container_width=True):
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
                        
                        res_proc = supabase.table('processos').insert({
                            "cliente_id": cli_id, "tipo_beneficio": servico,
                            "numero_requerimento": num_req, "status_processo": situacao,
                            "esfera": esfera
                        }).execute()
                        proc_id = res_proc.data[0]['id']

                        if data_pericia:
                            dt_full = datetime.combine(data_pericia, hora_pericia).isoformat()
                            status_p = "Compareceu" if check_pericia else "Pendente"
                            supabase.table('agendamentos').insert({
                                "processo_id": proc_id, "tipo_evento": tipo_pericia,
                                "data_hora": dt_full, "local_cidade": local_pericia,
                                "status_comparecimento": status_p
                            }).execute()
                            
                        if data_social:
                            dt_full_s = datetime.combine(data_social, hora_social).isoformat()
                            status_s = "Compareceu" if check_social else "Pendente"
                            supabase.table('agendamentos').insert({
                                "processo_id": proc_id, "tipo_evento": tipo_social,
                                "data_hora": dt_full_s, "local_cidade": local_social,
                                "status_comparecimento": status_s
                            }).execute()

                        st.success(f"Cadastro realizado! Cliente: {nome}")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

def tela_busca_edicao():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    tela_voltar()
    
    st.markdown("<h2 style='text-align: center;'>Buscar e Editar</h2>", unsafe_allow_html=True)
    
    termo = st.text_input("Pesquisar Cliente (Nome ou CPF)", placeholder="Digite aqui...")
    
    if termo:
        res = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").order('nome').execute()
        
        for cli in res.data:
            status_geral = cli.get('status_geral', 'Ativo')
            cor_status = "red" if status_geral == 'Arquivado' else "green"
            
            with st.expander(f":{cor_status}[{status_geral}] - 👤 {cli['nome']}"):
                
                if status_geral == 'Ativo':
                    c_arq1, c_arq2 = st.columns([3, 1])
                    c_arq2.write("") 
                    with c_arq2.popover("🗑️ Arquivar"):
                        motivo = st.text_input("Motivo", key=f"mot_{cli['id']}")
                        if st.button("Confirmar", key=f"arq_{cli['id']}"):
                            supabase.table('clientes').update({'status_geral': 'Arquivado', 'motivo_arquivamento': motivo}).eq('id', cli['id']).execute()
                            st.success("Arquivado!")
                            st.rerun()
                else:
                    st.warning(f"Motivo: {cli.get('motivo_arquivamento', '-')}")
                    if st.button("Reativar", key=f"react_{cli['id']}"):
                         supabase.table('clientes').update({'status_geral': 'Ativo', 'motivo_arquivamento': None}).eq('id', cli['id']).execute()
                         st.rerun()

                with st.form(key=f"edit_cli_{cli['id']}"):
                    st.markdown("**Dados Pessoais**")
                    c1, c2 = st.columns(2)
                    n_nome = c1.text_input("Nome", value=cli['nome'])
                    n_cpf = c2.text_input("CPF", value=cli['cpf'])
                    n_email = c1.text_input("Email", value=cli['email'])
                    n_senha = c2.text_input("Senha INSS", value=cli['senha_meu_inss'])
                    
                    if st.form_submit_button("ATUALIZAR DADOS", type="primary"):
                        supabase.table('clientes').update({
                            "nome": n_nome, "cpf": n_cpf, "email": n_email, "senha_meu_inss": n_senha
                        }).eq('id', cli['id']).execute()
                        st.success("Atualizado!")
                        st.rerun()
                
                st.divider()
                st.markdown("**Processos**")
                procs = supabase.table('processos').select("*").eq('cliente_id', cli['id']).execute().data
                
                for p in procs:
                    with st.container(border=True):
                        c_p1, c_p2, c_p3, c_p4 = st.columns([2, 1.5, 1.5, 1])
                        c_p1.write(f"📂 **{p['tipo_beneficio']}**")
                        
                        esfera_atual = p.get('esfera', 'Administrativo')
                        if not esfera_atual: esfera_atual = 'Administrativo'
                        nova_esfera = c_p2.selectbox("Esfera", ["Administrativo", "Judicial"], key=f"esf_{p['id']}", index=["Administrativo", "Judicial"].index(esfera_atual))
                        
                        lista_status = ["Em Análise", "Em Exigência", "Concedido", "Indeferido", "Aguardando Perícia", "Judicial"]
                        idx_status = lista_status.index(p['status_processo']) if p['status_processo'] in lista_status else 0
                        novo_status = c_p3.selectbox("Status", lista_status, key=f"st_{p['id']}", index=idx_status)
                        
                        if c_p4.button("💾", key=f"bt_{p['id']}"):
                            supabase.table('processos').update({
                                "status_processo": novo_status,
                                "esfera": nova_esfera
                            }).eq('id', p['id']).execute()
                            st.toast("Salvo!")
                            st.rerun()

                with st.popover("➕ Adicionar Processo"):
                    with st.form(key=f"form_add_p_{cli['id']}"):
                        serv_novo = st.selectbox("Serviço", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria"], key=f"new_serv_{cli['id']}")
                        esfera_novo = st.selectbox("Esfera", ["Administrativo", "Judicial"], key=f"new_esf_{cli['id']}")
                        nb_novo = st.text_input("Nº Requerimento", key=f"nb_{cli['id']}")
                        
                        if st.form_submit_button("Criar"):
                            supabase.table('processos').insert({
                                "cliente_id": cli['id'], "tipo_beneficio": serv_novo, 
                                "numero_requerimento": nb_novo, "status_processo": "Em Análise",
                                "esfera": esfera_novo
                            }).execute()
                            st.rerun()

def tela_agenda():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    tela_voltar()
    st.markdown("<h2 style='text-align: center;'>Agenda</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        mes = c1.selectbox("Mês", range(1,13), index=datetime.now().month-1)
        ano = c2.number_input("Ano", value=datetime.now().year)
    
    res = supabase.table('agendamentos').select("*, processos(id, clientes(nome))").order('data_hora').execute()
    
    dados = []
    if res.data:
        for a in res.data:
            dt = pd.to_datetime(a['data_hora'])
            if dt.month == mes and dt.year == ano:
                a['Data'] = formatar_data_hora(a['data_hora'])
                a['Cliente'] = a['processos']['clientes']['nome']
                a['Status'] = a.get('status_comparecimento', 'Pendente') 
                dados.append(a)
    
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df[['Data', 'Cliente', 'tipo_evento', 'Status', 'local_cidade']], use_container_width=True)
    else:
        st.info("Nada agendado para este período.")

def tela_financeiro():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    tela_voltar()
    st.markdown("<h2 style='text-align: center;'>Financeiro</h2>", unsafe_allow_html=True)
    
    abas = st.tabs(["Fluxo de Caixa", "Gestão & Recibos", "Novo Contrato"])
    
    # ABA 1: CAIXA
    with abas[0]:
        st.subheader("Movimento do Dia")
        data_f = st.date_input("Filtrar Data", value=date.today(), format="DD/MM/YYYY")
        
        with st.expander("➕ Lançamento Avulso (Entrada/Saída)"):
            c1, c2 = st.columns(2)
            l_tipo = c1.selectbox("Tipo", ["Entrada", "Saída"])
            l_val = c2.number_input("Valor R$", step=10.0)
            l_desc = st.text_input("Descrição")
            if st.button("Lançar Movimentação", type="primary"):
                supabase.table('caixa').insert({
                    "tipo": l_tipo, "valor": l_val, "descricao": l_desc,
                    "usuario_responsavel": st.session_state['usuario']['usuario'],
                    "data_movimentacao": datetime.now().isoformat()
                }).execute()
                st.rerun()
        
        res = supabase.table('caixa').select("*").order('data_movimentacao', desc=True).execute()
        filtrados = [x for x in res.data if pd.to_datetime(x['data_movimentacao']).date() == data_f]
        
        if filtrados:
            df = pd.DataFrame(filtrados)
            df['Data'] = pd.to_datetime(df['data_movimentacao']).dt.strftime('%d/%m/%Y')
            
            tot_ent = sum(x['valor'] for x in filtrados if x['tipo']=='Entrada')
            tot_sai = sum(x['valor'] for x in filtrados if x['tipo']=='Saída')
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Entradas", f"R$ {tot_ent:.2f}")
            m2.metric("Saídas", f"R$ {tot_sai:.2f}")
            m3.metric("Saldo", f"R$ {tot_ent-tot_sai:.2f}")

            st.dataframe(df[['Data', 'tipo', 'descricao', 'valor', 'usuario_responsavel']], use_container_width=True)
            
            if st.button("📄 Baixar PDF do Dia"):
                pdf = gerar_pdf_caixa(filtrados, data_f)
                st.download_button("Download PDF", pdf, f"caixa_{data_f}.pdf", "application/pdf")
        else:
            st.info("Sem movimentos nesta data.")

    # ABA 2: GESTÃO (Parcelas e Recibos)
    with abas[1]:
        tipo_gestao = st.radio("Selecione o tipo de cobrança:", ["Parcelas Fixas (Promissórias)", "Recibos 30% (Auxílio/Recorrente)"], horizontal=True)
        
        if tipo_gestao == "Parcelas Fixas (Promissórias)":
            st.subheader("Parcelas Pendentes")
            pendentes = supabase.table('parcelas').select("*, contratos(id, processos(id, clientes(nome)))").is_("data_pagamento", "null").order('data_vencimento').execute()
            
            if pendentes.data:
                for p in pendentes.data:
                    try:
                        cli_nome = p['contratos']['processos']['clientes']['nome']
                    except: cli_nome = "Desconhecido"
                    
                    venc = formatar_data(p['data_vencimento'])
                    cor = "red" if (date.today() - pd.to_datetime(p['data_vencimento']).date()).days > 0 else "blue"
                    
                    with st.expander(f":{cor}[{venc}] | {cli_nome} | R$ {p['valor_parcela']:.2f}"):
                        c1, c2 = st.columns([2,1])
                        c1.write(f"Parcela {p['numero_parcela']}")
                        forma = c1.selectbox("Forma", ["Dinheiro", "Pix"], key=f"f_{p['id']}")
                        
                        if c2.button("✅ Baixar", key=f"rec_{p['id']}"):
                            supabase.table('parcelas').update({
                                "data_pagamento": date.today().isoformat(),
                                "valor_pago": p['valor_parcela'],
                                "forma_pagamento": forma
                            }).eq('id', p['id']).execute()
                            
                            user_atual = st.session_state['usuario']['usuario']
                            desc = f"Receb. Parc {p['numero_parcela']} - {cli_nome}"
                            supabase.table('caixa').insert({
                                "tipo": "Entrada", "descricao": desc, "valor": p['valor_parcela'],
                                "usuario_responsavel": user_atual,
                                "data_movimentacao": datetime.now().isoformat()
                            }).execute()
                            st.success("Baixado!")
                            st.rerun()
            else:
                st.info("Nenhuma parcela fixa pendente.")
        
        else:
            # GESTÃO DE RECIBOS 30%
            st.subheader("Cálculo e Baixa de Honorários (30%)")
            
            # Buscar clientes com contratos Recorrentes (onde qtd_parcelas = 0 ou tipo_cobranca = Recorrente)
            # Para simplificar, buscaremos todos os clientes ativos e o usuário seleciona
            cli_res = supabase.table('clientes').select("id, nome").order('nome').execute()
            clientes_dict = {c['id']: c['nome'] for c in cli_res.data}
            cli_sel = st.selectbox("Selecione o Cliente (Auxílio Doença)", options=list(clientes_dict.keys()), format_func=lambda x: clientes_dict[x])
            
            if cli_sel:
                st.write(f"Cliente: **{clientes_dict[cli_sel]}**")
                
                col_v1, col_v2 = st.columns(2)
                valor_recebido = col_v1.number_input("Valor Recebido pelo Cliente (R$)", min_value=0.0, step=100.0)
                
                if valor_recebido > 0:
                    valor_honorario = valor_recebido * 0.30
                    col_v2.metric("Honorários (30%)", f"R$ {valor_honorario:.2f}")
                    
                    forma_rec = st.selectbox("Forma de Pagamento", ["Dinheiro", "Pix", "Transferência"])
                    
                    if st.button("💰 Lançar e Baixar no Caixa", type="primary"):
                        user_atual = st.session_state['usuario']['usuario']
                        mes_atual = datetime.now().strftime('%m/%Y')
                        desc = f"Honorários 30% - {clientes_dict[cli_sel]} ({mes_atual})"
                        
                        supabase.table('caixa').insert({
                            "tipo": "Entrada", "descricao": desc, "valor": valor_honorario,
                            "usuario_responsavel": user_atual,
                            "forma_pagamento": forma_rec,
                            "data_movimentacao": datetime.now().isoformat()
                        }).execute()
                        st.success(f"Recebimento de R$ {valor_honorario:.2f} lançado!")
                        st.rerun()

    # ABA 3: NOVO CONTRATO (ATUALIZADO)
    with abas[2]:
        st.subheader("Novo Contrato")
        
        cli_res = supabase.table('clientes').select("id, nome").order('nome').execute()
        clientes_dict = {c['id']: c['nome'] for c in cli_res.data}
        cli_selecionado = st.selectbox("Selecione o Cliente", options=list(clientes_dict.keys()), format_func=lambda x: clientes_dict[x])
        
        if cli_selecionado:
            proc_res = supabase.table('processos').select("id, tipo_beneficio, numero_requerimento").eq('cliente_id', cli_selecionado).execute()
            if proc_res.data:
                proc_dict = {p['id']: f"{p['tipo_beneficio']} (NB: {p.get('numero_requerimento', '-')})" for p in proc_res.data}
                proc_id = st.selectbox("Vincular ao Processo:", options=list(proc_dict.keys()), format_func=lambda x: proc_dict[x])
                
                st.divider()
                
                # SELETOR DE TIPO DE CONTRATO
                tipo_contrato = st.radio("Tipo de Cobrança", ["Valor Fixo (Promissórias)", "Recorrente (30% do Benefício/Recibo)"])
                
                if tipo_contrato == "Valor Fixo (Promissórias)":
                    c_val1, c_val2 = st.columns(2)
                    valor_total = c_val1.number_input("Valor Total (R$)", min_value=0.0, step=100.0)
                    valor_entrada = c_val2.number_input("Entrada (R$)", min_value=0.0, step=50.0)
                    
                    c_parc1, c_parc2 = st.columns(2)
                    qtd_parcelas = c_parc1.number_input("Qtd Parcelas", min_value=1, value=1)
                    vencimento_inicial = c_parc2.date_input("Vencimento 1ª Parcela", format="DD/MM/YYYY")
                    
                    saldo = valor_total - valor_entrada
                    if saldo > 0:
                        st.info(f"Serão geradas {qtd_parcelas} parcelas de R$ {saldo/qtd_parcelas:.2f}")
                    
                    if st.button("Gerar Contrato Fixo", type="primary"):
                        if valor_total <= 0:
                            st.error("Valor inválido.")
                        else:
                            res_cont = supabase.table('contratos').insert({
                                "processo_id": proc_id, "valor_total": valor_total,
                                "valor_entrada": valor_entrada, "qtd_parcelas": qtd_parcelas,
                                "tipo_cobranca": "Fixa"
                            }).execute()
                            contrato_id = res_cont.data[0]['id']
                            
                            # Lança Entrada
                            if valor_entrada > 0:
                                 supabase.table('caixa').insert({
                                    "tipo": "Entrada", "descricao": f"Entrada Honorários - {clientes_dict[cli_selecionado]}",
                                    "valor": valor_entrada, "forma_pagamento": "Dinheiro",
                                    "usuario_responsavel": st.session_state['usuario']['usuario']
                                }).execute()

                            # Gera Parcelas
                            if saldo > 0:
                                val_p = round(saldo / qtd_parcelas, 2)
                                diff = round(saldo - (val_p * qtd_parcelas), 2)
                                for i in range(qtd_parcelas):
                                    valor_desta = val_p + diff if i == qtd_parcelas - 1 else val_p
                                    data_venc = vencimento_inicial + relativedelta(months=i)
                                    supabase.table('parcelas').insert({
                                        "contrato_id": contrato_id, "numero_parcela": i+1,
                                        "valor_parcela": valor_desta, "data_vencimento": str(data_venc),
                                        "forma_pagamento": "Pendente"
                                    }).execute()
                            
                            st.success("Contrato de Promissórias Gerado!")
                            st.rerun()
                
                else: # CONTRATO RECORRENTE 30%
                    st.info("ℹ️ Este contrato não gera parcelas fixas. Todo mês você deverá lançar o valor recebido na aba 'Gestão & Recibos'.")
                    if st.button("Salvar Contrato de 30%", type="primary"):
                        supabase.table('contratos').insert({
                            "processo_id": proc_id, 
                            "valor_total": 0, # Indefinido
                            "valor_entrada": 0,
                            "qtd_parcelas": 0,
                            "tipo_cobranca": "Recorrente"
                        }).execute()
                        st.success("Contrato de 30% Salvo! Vá em 'Gestão & Recibos' para lançar pagamentos.")
                        st.rerun()
            else:
                st.warning("Este cliente não tem processos cadastrados.")

def tela_usuarios():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    tela_voltar()
    st.title("👥 Gestão de Usuários")
    
    if st.session_state['usuario'].get('perfil') != 'admin':
        st.error("Acesso negado.")
        return

    with st.form("new_user"):
        st.subheader("Novo Funcionário")
        u_nome = st.text_input("Nome")
        u_login = st.text_input("Login/Usuário")
        u_senha = st.text_input("Senha Inicial")
        u_perfil = st.selectbox("Perfil", ["comum", "admin"])
        
        if st.form_submit_button("Criar Usuário", type="primary"):
            try:
                supabase.table('usuarios').insert({
                    "nome": u_nome, "usuario": u_login, "senha": u_senha, "perfil": u_perfil
                }).execute()
                st.success(f"Usuário {u_login} criado!")
            except:
                st.error("Erro. Talvez o login já exista.")

def tela_meus_dados():
    aplicar_estilo_visual()
    mostrar_cabecalho()
    tela_voltar()
    st.title("🔒 Meus Dados")
    
    # Carregar dados atuais
    meu_id = st.session_state['usuario']['id']
    dados_atuais = supabase.table('usuarios').select("*").eq('id', meu_id).execute().data[0]
    
    with st.form("form_meus_dados"):
        st.write("Atualize seus dados abaixo:")
        novo_nome = st.text_input("Meu Nome", value=dados_atuais['nome'])
        nova_senha = st.text_input("Nova Senha", type="password", value=dados_atuais['senha'])
        
        if st.form_submit_button("💾 Salvar Alterações", type="primary"):
            supabase.table('usuarios').update({
                "nome": novo_nome, 
                "senha": nova_senha
            }).eq('id', meu_id).execute()
            
            # Atualiza sessão
            st.session_state['usuario']['nome'] = novo_nome
            st.success("Dados atualizados com sucesso!")
            st.rerun()

# --- CONTROLE DE NAVEGAÇÃO ---
def main():
    if 'usuario' not in st.session_state:
        # TELA DE LOGIN ESTILIZADA
        aplicar_estilo_visual()
        
        st.write("")
        st.write("")
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.image("LOGO lUNA ALENCAR.png", use_container_width=True)
            st.markdown("<h3 style='text-align: center; color: #C5A065;'>ACESSO</h3>", unsafe_allow_html=True)
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.button("ENTRAR", use_container_width=True, type="primary"):
                res = supabase.table('usuarios').select("*").eq('usuario', u).eq('senha', s).execute()
                if res.data:
                    st.session_state['usuario'] = res.data[0]
                    st.session_state['page'] = 'menu'
                    st.rerun()
                else:
                    st.error("Login inválido")
    else:
        # ROTEADOR DE PÁGINAS
        pg = st.session_state.get('page', 'menu')
        
        if pg == 'menu': tela_menu_principal()
        elif pg == 'cadastro': tela_cadastro()
        elif pg == 'busca': tela_busca_edicao()
        elif pg == 'agenda': tela_agenda()
        elif pg == 'financeiro': tela_financeiro()
        elif pg == 'usuarios': tela_usuarios()
        elif pg == 'meus_dados': tela_meus_dados() # Nova rota
        elif pg == 'senha': tela_meus_dados()      # Retrocompatibilidade

if __name__ == "__main__":
    main()
