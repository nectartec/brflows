import openai

# API OPENAI ================================================
#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
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


def retorna_resposta_assistente(openai_key, assistant_id, mensagens):
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


