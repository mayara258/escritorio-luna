import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
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
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(35, 10, "Data/Hora", 1)
    pdf.cell(60, 10, "Cliente", 1)
    pdf.cell(50, 10, "Evento", 1)
    pdf.cell(45, 10, "Local", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=9)
    for item in dados_agenda:
        data_fmt = pd.to_datetime(item['data_hora']).strftime('%d/%m %H:%M')
        nome = item['processos']['clientes']['nome'][:28].encode('latin-1', 'replace').decode('latin-1')
        evento = item['tipo_evento'][:25].encode('latin-1', 'replace').decode('latin-1')
        local = item['local_cidade'][:20].encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(35, 10, data_fmt, 1)
        pdf.cell(60, 10, nome, 1)
        pdf.cell(50, 10, evento, 1)
        pdf.cell(45, 10, local, 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

def gerar_pdf_caixa(dados_caixa, data_escolhida):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    data_str = data_escolhida.strftime('%d/%m/%Y')
    pdf.cell(200, 10, txt=f"Movimento de Caixa - {data_str}", ln=True, align='C')
    pdf.ln(5)
    
    # Cabeçalho Tabela
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "Hora", 1)
    pdf.cell(20, 10, "Tipo", 1)
    pdf.cell(80, 10, "Descricao", 1)
    pdf.cell(30, 10, "Forma", 1)
    pdf.cell(30, 10, "Valor", 1)
    pdf.ln()
    
    # Dados
    pdf.set_font("Arial", size=9)
    total_entrada = 0
    total_saida = 0
    
    for item in dados_caixa:
        hora = pd.to_datetime(item['data_movimentacao']).strftime('%H:%M')
        tipo = item['tipo']
        desc = item['descricao'][:40].encode('latin-1', 'replace').decode('latin-1')
        forma = item['forma_pagamento'][:15].encode('latin-1', 'replace').decode('latin-1')
        valor = float(item['valor'])
        
        if tipo == 'Entrada':
            total_entrada += valor
            pdf.set_text_color(0, 100, 0) # Verde
        else:
            total_saida += valor
            pdf.set_text_color(200, 0, 0) # Vermelho
            
        pdf.cell(30, 10, hora, 1)
        pdf.cell(20, 10, tipo, 1)
        pdf.cell(80, 10, desc, 1)
        pdf.cell(30, 10, forma, 1)
        pdf.cell(30, 10, f"R$ {valor:.2f}", 1)
        pdf.ln()
    
    # Resumo
    pdf.set_text_color(0, 0, 0) # Preto
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt="RESUMO DO DIA", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 8, txt=f"Total Entradas: R$ {total_entrada:.2f}", ln=True)
    pdf.cell(200, 8, txt=f"Total Saidas:   R$ {total_saida:.2f}", ln=True)
    
    saldo = total_entrada - total_saida
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"SALDO FINAL: R$ {saldo:.2f}", ln=True)
        
    return pdf.output(dest='S').encode('latin-1')

# --- TELA PRINCIPAL ---
def main():
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

    st.sidebar.title(f"Olá, {st.session_state['usuario']['nome']}")
    menu = st.sidebar.radio("Navegação", ["Agendamentos", "Novo Cadastro (Completo)", "Buscar Cliente", "Financeiro"])
    
    if st.sidebar.button("Sair"):
        del st.session_state['usuario']
        st.rerun()

    # --- TELA 1: AGENDAMENTOS ---
    if menu == "Agendamentos":
        st.title("📅 Agendamentos do Mês")
        c1, c2 = st.columns(2)
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        sel_mes = c1.selectbox("Mês", list(range(1,13)), index=mes_atual-1)
        sel_ano = c2.number_input("Ano", value=ano_atual)
        
        res = supabase.table('agendamentos').select("*, processos(id, clientes(nome))").order('data_hora').execute()
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
            st.dataframe(df[['Data', 'Cliente', 'tipo_evento', 'local_cidade', 'status_comparecimento']], use_container_width=True)
            if st.button("📄 Baixar PDF deste mês"):
                arquivo = gerar_pdf_agenda(lista_final, sel_mes, sel_ano)
                st.download_button("Download PDF", arquivo, f"agenda_{sel_mes}_{sel_ano}.pdf", "application/pdf")
        else:
            st.info("Nenhum agendamento para este mês.")

    # --- TELA 2: CADASTRO COMPLETO ---
    elif menu == "Novo Cadastro (Completo)":
        st.title("➕ Cadastro Unificado")
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
            st.subheader("2. Dados do Processo")
            c3, c4 = st.columns(2)
            servico = c3.selectbox("Serviço/Benefício", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria", "Salário Maternidade", "Pensão", "Outro"])
            num_req = c4.text_input("Número do Requerimento (NB)")
            situacao = c3.selectbox("Situação Atual", ["Em Análise", "Em Exigência", "Concedido", "Indeferido", "Aguardando Perícia"])
            
            st.divider()
            st.subheader("3. Agendamento Inicial (Opcional)")
            c5, c6 = st.columns(2)
            data_pericia = c5.date_input("Data Perícia", value=None)
            hora_pericia = c5.time_input("Hora", value=time(8,0))
            tipo_pericia = c5.selectbox("Tipo", ["Perícia Médica INSS", "Perícia Judicial", "Audiência", "Prorrogação"])
            
            obs = st.text_area("Observações Gerais")
            
            if st.form_submit_button("💾 Salvar Tudo"):
                if not nome or not cpf:
                    st.error("Nome e CPF obrigatórios.")
                else:
                    try:
                        dados_cli = {"nome": nome, "cpf": cpf, "email": email, "senha_meu_inss": senha_inss, "colaborador": colaborador, "observacoes": obs}
                        if data_nasc: dados_cli["data_nascimento"] = str(data_nasc)
                        res_cli = supabase.table('clientes').insert(dados_cli).execute()
                        cli_id = res_cli.data[0]['id']
                        
                        dados_proc = {"cliente_id": cli_id, "tipo_beneficio": servico, "numero_requerimento": num_req, "status_processo": situacao, "esfera": "Administrativo"}
                        res_proc = supabase.table('processos').insert(dados_proc).execute()
                        proc_id = res_proc.data[0]['id']
                        
                        if data_pericia:
                            dt_full = datetime.combine(data_pericia, hora_pericia).isoformat()
                            supabase.table('agendamentos').insert({"processo_id": proc_id, "tipo_evento": tipo_pericia, "data_hora": dt_full, "local_cidade": "A Definir"}).execute()
                            
                        st.success(f"Cadastro realizado! Cliente: {nome}")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    # --- TELA 3: BUSCA COM ADIÇÃO DE PROCESSO ---
    elif menu == "Buscar Cliente":
        st.title("🔍 Base de Clientes")
        termo = st.text_input("Nome ou CPF")
        if termo:
            res = supabase.table('clientes').select("*").ilike('nome', f"%{termo}%").execute()
            for cli in res.data:
                with st.expander(f"{cli['nome']} - {cli['status_geral']}"):
                    st.write(f"CPF: {cli['cpf']} | Colaborador: {cli.get('colaborador', '-')}")
                    st.write(f"Senha INSS: {cli['senha_meu_inss']}")
                    
                    procs = supabase.table('processos').select("*").eq('cliente_id', cli['id']).execute().data
                    if procs:
                        st.caption("Processos Ativos:")
                        for p in procs:
                            st.info(f"📂 {p['tipo_beneficio']} - {p['status_processo']} (NB: {p['numero_requerimento']})")
                    else:
                        st.warning("Nenhum processo cadastrado.")

                    st.markdown("---")
                    st.write("**➕ Adicionar Processo para este Cliente**")
                    with st.form(key=f"add_proc_{cli['id']}"):
                        c_a, c_b = st.columns(2)
                        n_serv = c_a.selectbox("Serviço", ["BPC/LOAS", "Auxílio Doença", "Aposentadoria", "Salário Maternidade"], key=f"s_{cli['id']}")
                        n_req = c_b.text_input("Nº Requerimento", key=f"r_{cli['id']}")
                        if st.form_submit_button("Salvar Processo"):
                            supabase.table('processos').insert({
                                "cliente_id": cli['id'],
                                "tipo_beneficio": n_serv,
                                "numero_requerimento": n_req,
                                "status_processo": "Em Análise",
                                "esfera": "Administrativo"
                            }).execute()
                            st.success("Processo criado! Agora você pode criar o contrato financeiro.")
                            st.rerun()

    # --- TELA 4: FINANCEIRO COMPLETO (AGORA COM PDF) ---
    elif menu == "Financeiro":
        st.title("💰 Financeiro do Escritório")
        
        abas = st.tabs(["Fluxo de Caixa (Diário)", "Contratos & Honorários", "Novo Contrato"])
        
        # --- ABA 1: CAIXA DIÁRIO COM PDF ---
        with abas[0]:
            st.subheader("Movimentação do Dia")
            
            # Filtro de Data
            col_d, col_vazia = st.columns([1,2])
            data_filtro = col_d.date_input("Selecione a Data", value=date.today())
            
            # Novo Lançamento Rápido
            with st.expander("➕ Novo Lançamento Avulso (Entrada/Saída)"):
                c1, c2, c3 = st.columns(3)
                tipo = c1.selectbox("Tipo", ["Entrada", "Saída"])
                valor = c2.number_input("Valor R$", step=10.0)
                forma = c3.selectbox("Forma", ["Dinheiro", "Pix", "Depósito"])
                desc = st.text_input("Descrição (Ex: Compra de Papel)")
                
                if st.button("Lançar no Caixa"):
                    supabase.table('caixa').insert({
                        "tipo": tipo, "descricao": desc, "valor": valor, "forma_pagamento": forma,
                        "usuario_responsavel": st.session_state['usuario']['usuario']
                    }).execute()
                    st.success("Lançado!")
                    st.rerun()
            
            st.divider()
            
            # Tabela Filtrada
            res_caixa = supabase.table('caixa').select("*").order('data_movimentacao', desc=True).execute()
            dados_filtrados = []
            
            # Filtrar no Python (Data do banco vem como timestamp completo)
            if res_caixa.data:
                for item in res_caixa.data:
                    data_item = pd.to_datetime(item['data_movimentacao']).date()
                    if data_item == data_filtro:
                        dados_filtrados.append(item)
            
            if dados_filtrados:
                st.markdown(f"**Movimentações do dia {data_filtro.strftime('%d/%m/%Y')}**")
                df_cx = pd.DataFrame(dados_filtrados)
                
                # Calcular Totais
                tot_ent = sum(d['valor'] for d in dados_filtrados if d['tipo'] == 'Entrada')
                tot_sai = sum(d['valor'] for d in dados_filtrados if d['tipo'] == 'Saída')
                saldo = tot_ent - tot_sai
                
                # Exibir Métricas
                m1, m2, m3 = st.columns(3)
                m1.metric("Entradas", f"R$ {tot_ent:.2f}")
                m2.metric("Saídas", f"R$ {tot_sai:.2f}")
                m3.metric("Saldo do Dia", f"R$ {saldo:.2f}")
                
                st.dataframe(df_cx[['tipo', 'descricao', 'valor', 'forma_pagamento']], use_container_width=True)
                
                # Botão PDF
                if st.button("📄 Baixar Relatório do Dia (PDF)"):
                    arq_pdf = gerar_pdf_caixa(dados_filtrados, data_filtro)
                    st.download_button("Download PDF", arq_pdf, f"caixa_{data_filtro}.pdf", "application/pdf")
            else:
                st.info(f"Nenhuma movimentação registrada no dia {data_filtro.strftime('%d/%m/%Y')}.")

        # --- ABA 2: GESTÃO DE CONTRATOS ---
        with abas[1]:
            st.subheader("Parcelas a Receber / Atrasadas")
            res_parc = supabase.table('parcelas').select("*, contratos(id, valor_total, processos(id, clientes(nome)))").is_("data_pagamento", "null").order('data_vencimento').execute()
            
            if res_parc.data:
                for p in res_parc.data:
                    try:
                        nome_cli = p['contratos']['processos']['clientes']['nome']
                    except:
                        nome_cli = "Cliente Desconhecido"
                    
                    dt_venc = pd.to_datetime(p['data_vencimento']).date()
                    hoje = date.today()
                    atraso = (hoje - dt_venc).days
                    cor_alerta = "red" if atraso > 0 else "blue"
                    
                    with st.expander(f":{cor_alerta}[{dt_venc.strftime('%d/%m/%Y')}] - {nome_cli} - R$ {p['valor_parcela']:.2f}"):
                        c_pag1, c_pag2 = st.columns(2)
                        forma_pag = c_pag1.selectbox("Forma Pagto", ["Dinheiro", "Pix", "Depósito"], key=f"fp_{p['id']}")
                        if c_pag2.button("✅ Receber", key=f"bt_rec_{p['id']}"):
                            supabase.table('parcelas').update({
                                "data_pagamento": str(date.today()),
                                "valor_pago": p['valor_parcela'],
                                "forma_pagamento": forma_pag
                            }).eq('id', p['id']).execute()
                            
                            desc_caixa = f"Recebimento Parc {p['numero_parcela']} - {nome_cli}"
                            supabase.table('caixa').insert({
                                "tipo": "Entrada", "descricao": desc_caixa, 
                                "valor": p['valor_parcela'], "forma_pagamento": forma_pag,
                                "usuario_responsavel": st.session_state['usuario']['usuario']
                            }).execute()
                            st.success("Recebido!")
                            st.rerun()
            else:
                st.info("Nenhuma parcela pendente.")

        # --- ABA 3: NOVO CONTRATO ---
        with abas[2]:
            st.subheader("Novo Contrato de Honorários")
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
                    vencimento_inicial = c_parc2.date_input("Vencimento 1ª Parcela")
                    
                    saldo = valor_total - valor_entrada
                    if saldo > 0:
                        st.info(f"Serão geradas {qtd_parcelas} parcelas de R$ {saldo/qtd_parcelas:.2f}")
                    
                    if st.button("Gerar Contrato"):
                        if valor_total <= 0:
                            st.error("Valor total inválido.")
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
                    st.info("👉 Vá na aba 'Buscar Cliente', pesquise por ele e adicione um processo.")

if __name__ == "__main__":
    main()
