import openai

# API OPENAI ================================================
def retorna_resposta_modelo(mensagens,
                            openai_key,
                            modelo='gpt-3.5-turbo',
                            temperatura=0,
                            stream=False):
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model=modelo,
        messages=mensagens,
        temperature=temperatura,
        stream=stream
    )
    return response


def retorna_resposta_assistente(mensagens):
    openai_key = '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'
    assistant_id = 'asst_cbtwXlzPuCXZloblRXpg0Urb'
    openai.api_key = openai_key
    
    # Cria uma nova thread para a conversa
    thread = openai.beta.threads.create()

    # Adiciona as mensagens do usuário na thread
    for mensagem in mensagens:
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role=mensagem['role'],
            content=mensagem['content']
        )

    # Inicia a execução do assistente
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Verifica o status do run até que ele esteja concluído
    import time
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        time.sleep(1)  # Aguarda um segundo antes de verificar novamente

    # Recupera a resposta do assistente
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    
    # Retorna a última mensagem do assistente
    resposta = messages.data[0].content[0].text.value
    return resposta


