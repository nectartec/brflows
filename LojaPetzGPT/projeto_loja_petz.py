import streamlit as st
import json
import os

from utils_openai import retorna_resposta_assistente
from utils_files import *

# Nome do arquivo onde os feedbacks serão armazenados
FEEDBACK_FILE = "feedbacks.json"

# Função para carregar feedbacks do arquivo JSON
def carregar_feedbacks():
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

# Função para salvar um novo feedback
def salvar_feedback(pergunta, resposta, util, comentario):
    feedbacks = carregar_feedbacks()
    novo_feedback = {
        "pergunta": pergunta,
        "resposta": resposta,
        "util": util,
        "comentario": comentario
    }
    feedbacks.append(novo_feedback)

    with open(FEEDBACK_FILE, "w", encoding="utf-8") as file:
        json.dump(feedbacks, file, indent=4, ensure_ascii=False)

# INICIALIZAÇÃO ==================================================
def inicializacao():
    if 'mensagens' not in st.session_state:
        st.session_state.mensagens = []
    if 'conversa_atual' not in st.session_state:
        st.session_state.conversa_atual = ''
    if 'api_key' not in st.session_state:
        st.session_state.api_key = le_chave()
    if 'assistant_key' not in st.session_state:
        st.session_state.assistant_key = le_assistant_key()
    if 'ultima_pergunta' not in st.session_state:
        st.session_state.ultima_pergunta = '' 
    if 'ultima_resposta' not in st.session_state:
        st.session_state.ultima_resposta = ''
    if 'exibir_feedback' not in st.session_state:
        st.session_state.exibir_feedback = False  # Novo controle para exibir/ocultar feedback

# TABS ==================================================
def tab_conversas(tab):
    tab.button('➕ Nova conversa',
               on_click=seleciona_conversa,
               args=('', ),
               use_container_width=True)
    tab.markdown('')
    conversas = listar_conversas()
    for nome_arquivo in conversas:
        nome_mensagem = desconverte_nome_mensagem(nome_arquivo).capitalize()
        if len(nome_mensagem) == 30:
            nome_mensagem += '...'
        tab.button(nome_mensagem,
                   on_click=seleciona_conversa,
                   args=(nome_arquivo, ),
                   disabled=nome_arquivo == st.session_state['conversa_atual'],
                   use_container_width=True)

def seleciona_conversa(nome_arquivo):
    if nome_arquivo == '':
        st.session_state['mensagens'] = []
    else:
        mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo)
        st.session_state['mensagens'] = mensagem
    st.session_state['conversa_atual'] = nome_arquivo

# PÁGINA PRINCIPAL ==================================================
def pagina_principal():
    mensagens = ler_mensagens(st.session_state['mensagens'])

    st.header('🤖 Petz Atendente Chatbot', divider=True)

    for mensagem in mensagens:
        chat = st.chat_message(mensagem['role'])
        chat.markdown(mensagem['content'])

    prompt = st.chat_input('Fale com o chat')
    if prompt:
        st.session_state.ultima_pergunta = prompt
        st.session_state.exibir_feedback = False  # Resetar flag do feedback

        nova_mensagem = {'role': 'user', 'content': prompt}
        chat = st.chat_message(nova_mensagem['role'])
        chat.markdown(nova_mensagem['content'])
        mensagens.append(nova_mensagem)

        chat = st.chat_message('assistant')
        placeholder = chat.empty()
        placeholder.markdown("▌")
        resposta_completa = ''
        
        respostas = retorna_resposta_assistente(mensagens)

        for resposta in respostas:
            resposta_completa += resposta
            placeholder.markdown(resposta_completa + "▌")
        placeholder.markdown(resposta_completa)

        st.session_state.ultima_resposta = resposta_completa
        st.session_state.exibir_feedback = True  # Agora pode exibir o feedback

        nova_mensagem = {'role': 'assistant', 'content': resposta_completa}
        mensagens.append(nova_mensagem)

        st.session_state['mensagens'] = mensagens
        salvar_mensagens(mensagens)

    # Exibir feedback apenas se a resposta foi dada e ainda não foi enviado
    if st.session_state.exibir_feedback:
        st.subheader("📢 Avalie a Resposta")
        util = st.radio("A resposta foi útil?", ["Sim", "Não"], key="feedback_util")
        comentario = st.text_area("Comentários adicionais:", key="feedback_comentario")

        if st.button("Salvar Feedback"):
            salvar_feedback(
                st.session_state.ultima_pergunta,
                st.session_state.ultima_resposta,
                util,
                comentario
            )

            # Ocultar feedback após o envio
            st.session_state.exibir_feedback = False
            st.success("Feedback salvo com sucesso!")

# MAIN ==================================================
def main():
    inicializacao()
    pagina_principal()
    tab1, tab2 = st.sidebar.tabs(['Conversas', 'Configuração'])
    tab_conversas(tab1)

if __name__ == '__main__':
    main()
