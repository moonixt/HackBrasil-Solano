"""Textos em pt-BR usados pelo onboarding. Curtos, pensados para o Telegram."""

MSG_GREETING = (
    "Oi! Eu sou o Solano. Te ajudo a entender como acessar a rede pública de "
    "saúde: onde se vacinar, como marcar consulta na UBS e que documentos levar.\n\n"
    "Não faço diagnóstico nem indico remédio — sempre te mando para a unidade "
    "certa, com a fonte da informação.\n\n"
    "Pra começar, compartilha seu telefone com o botão abaixo."
)

MSG_ASK_CONTACT_AGAIN = (
    "Preciso que você use o botão \"Compartilhar meu telefone\" abaixo — "
    "ainda não consegui confirmar seu contato."
)

MSG_INVALID_PHONE = (
    "Esse telefone não parece um número brasileiro válido. Usa o botão "
    "\"Compartilhar meu telefone\" para eu confirmar certinho."
)

MSG_ASK_CITY = "Perfeito! Agora me diz sua cidade e estado (ex.: Recife, PE)."

MSG_INVALID_CITY = (
    "Não entendi a cidade. Manda no formato \"Cidade, UF\" (ex.: Recife, PE)."
)

MSG_ASK_NEIGHBORHOOD = "E qual é o seu bairro?"

MSG_ASK_NEIGHBORHOOD_AGAIN = "Não entendi. Qual é o nome do seu bairro?"

MSG_READY = (
    "Prontinho! Você está com o {agent_name}, e já posso te ajudar com coisas "
    "como \"onde consigo me vacinar?\" ou \"como marco uma consulta na UBS?\"."
)

MSG_HELP = (
    "Posso te orientar sobre a rede pública de saúde: unidades, como marcar "
    "consulta e documentos necessários. Não faço diagnóstico nem indico remédio.\n\n"
    "Comandos:\n"
    "/local — trocar cidade/bairro\n"
    "/sugerir <texto> — sugerir uma correção (fica pendente até ser revisada)\n"
    "/ajuda — ver esta mensagem"
)

MSG_SUGGEST_THANKS = "Obrigado! Sua sugestão fica pendente até ser verificada."

MSG_SUGGEST_EMPTY = "Me diz o que você quer sugerir, assim: /sugerir <texto>."

MSG_SUGGEST_NEEDS_LOCATION = (
    "Antes de sugerir, preciso saber sua cidade. Manda /local para configurar."
)

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
