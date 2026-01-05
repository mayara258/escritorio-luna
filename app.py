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
    st.markdown("""
    <style>
        div[data-testid="column"] .stButton button {
            height: 130px;
            width: 100%;
            font-size: 22px;
            font-weight: 600;
            border-radius: 12px;
            border: 1px solid #ddd;
            transition: all 0.3s;
        }
        div[data-testid="column"] .stButton button:hover {
            transform: scale(1.02);
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
    aplicar_estilo_menu()
    
    st.title("⚖️ Painel Principal")
    st.write(f"Bem-vindo(a), **{st.session_state['usuario']['nome']}**")
    st.write("") 
    
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("📅 Agendamentos"): st.session_state['page'] = 'agenda'
        if st.button("🔍 Buscar / Editar Cliente"): st.session_state['page'] = 'busca'
        if st.button("💰 Financeiro"): st.session_state['page'] = 'financeiro'
    
    with c2:
        if st.button("➕ Novo Cadastro"): st.session_state['page'] = 'cadastro'
        
        if st.session_state['usuario'].get('perfil') == 'admin':
            if st.button("👥 Gestão de Usuários"): st.session_state['page'] = 'usuarios'
        else:
            pass
        
        if st.button("🔒 Alterar Minha Senha"): st.session_state['page'] = 'senha'

    st.divider()
    
    if st.button("Sair do Sistema", type="primary"): 
        st.session_state.clear()
        st.rerun()

def tela_voltar():
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
                
                st.divider()
                st.write("**Processos**")
                procs = supabase.table('processos').select("*").eq('cliente_id', cli['id']).execute().data
                
                for p in procs:
                    with st.container(border=True):
                        c_p1, c_p2, c_p3 = st.columns([2, 2, 1])
                        c_p1.write(f"**{p['tipo_beneficio']}**")
                        
                        lista_status = ["Em Análise", "Em Exigência", "Concedido", "Indeferido", "Aguardando Perícia", "Judicial"]
                        idx_status = lista_status.index(p['status_processo']) if p['status_processo'] in lista_status else 0
                        
                        novo_status = c_p2.selectbox("Status", lista_status, key=f"st_{p['id']}", index=idx_status)
                        
                        if c_p3.button("Salvar Status", key=f"bt_{p['id']}"):
                            supabase.table('processos').update({"status_processo": novo_status}).eq('id', p['id']).execute()
                            st.toast("Status atualizado!")
                            st.rerun()

                with st.popover("➕ Adicionar Processo"):
                    st.write("Novo Processo para este cliente")
                    with st.form(key=f"form_add_p_{cli['id']}"):
                        serv_novo = st.selectbox("Serviço", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria"], key=f"new_serv_{cli['id']}")
                        nb_novo = st.text_input("Nº Requerimento", key=f"nb_{cli['id']}")
                        
                        if st.form_submit_button("Criar"):
                            supabase.table('processos').insert({
                                "cliente_id": cli['id'], "tipo_beneficio": serv_novo, 
                                "numero_requerimento": nb_novo, "status_processo": "Em Análise"
                            }).execute()
                            st.rerun()

def tela_agenda():
    tela_voltar()
    st.title("📅 Agenda")
    
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
                dados.append(a)
    
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df[['Data', 'Cliente', 'tipo_evento', 'local_cidade']], use_container_width=True)
    else:
        st.info("Nada agendado.")

def tela_financeiro():
    tela_voltar()
    st.title("💰 Financeiro")
    
    abas = st.tabs(["Caixa Diário", "Gestão de Contratos", "Novo Contrato"])
    
    with abas[0]:
        st.subheader("Movimento do Dia")
        data_f = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
        
        with st.expander("➕ Lançamento Avulso"):
            l_tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            l_val = st.number_input("Valor", step=10.0)
            l_desc = st.text_input("Descrição")
            if st.button("Lançar"):
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
            df['Hora'] = pd.to_datetime(df['data_movimentacao']).dt.strftime('%H:%M')
            st.dataframe(df[['Hora', 'tipo', 'descricao', 'valor', 'usuario_responsavel']], use_container_width=True)
            
            if st.button("📄 Baixar PDF do Dia"):
                pdf = gerar_pdf_caixa(filtrados, data_f)
                st.download_button("Download PDF", pdf, f"caixa_{data_f}.pdf", "application/pdf")
        else:
            st.info("Sem movimentos nesta data.")

    with abas[1]:
        st.subheader("Recebimentos Pendentes")
        pendentes = supabase.table('parcelas').select("*, contratos(id, processos(id, clientes(nome)))").is_("data_pagamento", "null").order('data_vencimento').execute()
        
        if pendentes.data:
            for p in pendentes.data:
                try:
                    cli_nome = p['contratos']['processos']['clientes']['nome']
                except: cli_nome = "Desconhecido"
                
                venc = formatar_data(p['data_vencimento'])
                dt_venc = pd.to_datetime(p['data_vencimento']).date()
                atraso = (date.today() - dt_venc).days
                cor = "red" if atraso > 0 else "blue"
                
                with st.expander(f":{cor}[{venc}] | {cli_nome} | R$ {p['valor_parcela']:.2f}"):
                    st.write(f"Parcela {p['numero_parcela']}")
                    forma = st.selectbox("Forma", ["Dinheiro", "Pix"], key=f"f_{p['id']}")
                    
                    if st.button("✅ Receber (Baixar)", key=f"rec_{p['id']}"):
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
                        
                        st.success(f"Baixado por {user_atual}!")
                        st.rerun()

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
                c_val1, c_val2 = st.columns(2)
                valor_total = c_val1.number_input("Valor Total (R$)", min_value=0.0, step=100.0)
                valor_entrada = c_val2.number_input("Entrada (R$)", min_value=0.0, step=50.0)
                
                c_parc1, c_parc2 = st.columns(2)
                qtd_parcelas = c_parc1.number_input("Qtd Parcelas", min_value=1, value=1)
                vencimento_inicial = c_parc2.date_input("Vencimento 1ª Parcela", format="DD/MM/YYYY")
                
                saldo = valor_total - valor_entrada
                if saldo > 0:
                    st.info(f"Serão geradas {qtd_parcelas} parcelas de R$ {saldo/qtd_parcelas:.2f}")
                
                if st.button("Gerar Contrato"):
                    if valor_total <= 0:
                        st.error("Valor inválido.")
                    else:
                        res_cont = supabase.table('contratos').insert({
                            "processo_id": proc_id, "valor_total": valor_total,
                            "valor_entrada": valor_entrada, "qtd_parcelas": qtd_parcelas
                        }).execute()
                        contrato_id = res_cont.data[0]['id']
                        
                        if valor_entrada > 0:
                             supabase.table('caixa').insert({
                                "tipo": "Entrada", "descricao": f"Entrada Honorários - {clientes_dict[cli_selecionado]}",
                                "valor": valor_entrada, "forma_pagamento": "Dinheiro",
                                "usuario_responsavel": st.session_state['usuario']['usuario']
                            }).execute()

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
                        
                        st.success("Contrato Gerado!")
                        st.rerun()
            else:
                st.warning("Este cliente não tem processos cadastrados.")

def tela_usuarios():
    tela_voltar()
    st.title("👥 Gestão de Usuários (Admin)")
    
    if st.session_state['usuario'].get('perfil') != 'admin':
        st.error("Acesso negado.")
        return

    st.subheader("Cadastrar Novo Funcionário")
    with st.form("new_user"):
        u_nome = st.text_input("Nome")
        u_login = st.text_input("Login/Usuário")
        u_senha = st.text_input("Senha Inicial")
        u_perfil = st.selectbox("Perfil", ["comum", "admin"])
        
        if st.form_submit_button("Criar Usuário"):
            try:
                supabase.table('usuarios').insert({
                    "nome": u_nome, "usuario": u_login, "senha": u_senha, "perfil": u_perfil
                }).execute()
                st.success(f"Usuário {u_login} criado!")
            except:
                st.error("Erro. Talvez o login já exista.")

def tela_senha():
    tela_voltar()
    st.title("🔒 Alterar Senha")
    
    senha_nova = st.text_input("Nova Senha", type="password")
    if st.button("Confirmar Alteração"):
        meu_id = st.session_state['usuario']['id']
        supabase.table('usuarios').update({"senha": senha_nova}).eq('id', meu_id).execute()
        st.success("Senha alterada! Faça login novamente.")
        st.session_state.clear()
        st.rerun()

# --- CONTROLE DE NAVEGAÇÃO ---
def main():
    if 'usuario' not in st.session_state:
        # TELA DE LOGIN
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.title("⚖️ Login")
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
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
        elif pg == 'senha': tela_senha()

if __name__ == "__main__":
    main()
