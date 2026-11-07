"""Textos fixos em pt-BR do bot. Curtos, pensados para o Telegram; o resto da conversa é o agente."""

MSG_GREETING = (
    "Oi! Eu sou o Solano. Te ajudo a se orientar na rede pública de saúde: onde se vacinar, "
    "como marcar consulta na UBS, que documentos levar.\n\n"
    "Pode perguntar do seu jeito, por exemplo: \"onde me vacino em Recife?\"\n\n"
    "Não faço diagnóstico nem indico remédio. Se quiser, compartilhe seu telefone pelo botão abaixo (opcional)."
)

MSG_PHONE_SAVED = "Telefone salvo, obrigado! Pode perguntar o que precisar."

MSG_INVALID_PHONE = "Esse telefone não parece um número brasileiro. Sem problema: dá para usar o Solano sem ele."

MSG_ASK_LOCATION = "Pra te orientar, me diz a cidade e o estado (ex.: Recife, PE)."

MSG_LOCATION_SAVED = (
    "Anotado! Você está com o {agent_name}. Pode perguntar coisas como "
    "\"onde consigo me vacinar?\" ou \"como marco uma consulta na UBS?\"."
)

MSG_LOCAL_RESET = "Certo! De qual cidade e bairro você fala agora?"

MSG_HELP = (
    "Pergunte do seu jeito sobre a rede pública de saúde: unidades, como marcar consulta, "
    "documentos, horários. Não faço diagnóstico nem indico remédio.\n\n"
    "Comandos:\n"
    "/local — trocar cidade/bairro\n"
    "/sugerir <texto> — sugerir uma correção (fica pendente até ser verificada)\n"
    "/start — recomeçar a conversa"
)

MSG_SUGGEST_THANKS = "Obrigado! Sua sugestão fica pendente até ser verificada."

MSG_SUGGEST_EMPTY = "Me diz o que você quer sugerir, assim: /sugerir <texto>."

MSG_SUGGEST_NEEDS_LOCATION = "Antes de sugerir, me diz sua cidade e estado."

NOT_COVERED_MESSAGE = (
    "Ainda não tenho dados sobre {city}/{uf}. Você pode ligar no Disque Saúde "
    "136 ou procurar a UBS mais próxima para se orientar."
)

NO_MATCH_MESSAGE = (
    "Não encontrei uma unidade para isso na sua região ainda. Tenta o Disque "
    "Saúde 136 ou procure a UBS mais próxima."
)

EMERGENCY_REPLY = (
    "Isso parece uma emergência. Ligue agora para o SAMU 192 ou vá direto à "
    "UPA mais próxima. Por aqui eu não consigo ajudar com emergências."
)
