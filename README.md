# JARVIS

Um assistente pessoal em Python inspirado no JARVIS de "Homem de Ferro", pensado para Windows, com:

- comandos por texto ou voz
- abertura de programas, sites e pastas
- pesquisas no Google
- respostas por voz
- cérebro configurável por regras ou pela OpenAI
- arquitetura modular para evoluir para automações e agentes mais inteligentes

## Como o cérebro decide

O modelo de linguagem interpreta o pedido, mas não executa nada por conta própria. Com a OpenAI, a API Responses devolve a decisão num formato estruturado, validado por um modelo Pydantic (`BrainDecision`), e a intenção só pode ser uma de oito opções fechadas: `open_app`, `open_site`, `open_folder`, `google_search`, `time`, `help`, `exit` ou `unknown`.

A execução continua nas ações do projeto: um aplicativo só abre se estiver cadastrado em `config/jarvis.json`, e o resto vira erro com a lista dos apelidos conhecidos. Sem `OPENAI_API_KEY`, o assistente usa o roteador por regras, que tem o mesmo contrato de saída. O cérebro da OpenAI guarda as últimas 8 linhas da conversa como contexto e é chamado com `store=False`.

## Arquitetura

O projeto foi organizado em camadas para ficar simples de usar agora e fácil de expandir depois:

1. `assistant.py`
Orquestra o ciclo principal do assistente, gerencia os modos texto, voz e híbrido e centraliza as respostas.

2. `interfaces/`
Contém as interfaces de entrada e saída.
`text_io.py` cuida do terminal.
`voice_io.py` usa a fala nativa do Windows para a saída de voz e combina a captura do microfone em Python com a transcrição pela OpenAI, mantendo o reconhecimento do Windows como alternativa.

3. `brains/`
Separa a inteligência do assistente atrás da interface `Brain`, e `factory.py` escolhe a implementação.
`rule_based.py` usa o roteador determinístico.
`openai_brain.py` usa a OpenAI como cérebro para interpretar ordens livres e responder conversas curtas.

4. `core/router.py`
Transforma frases em intenções como `open_app`, `open_site`, `google_search`, `open_folder`, `time`, `help`, `reply` e `exit`.

5. `actions/`
Executa as ações do mundo real.
`system_actions.py` abre apps e pastas.
`web_actions.py` abre URLs e pesquisas.

6. `config.py`
Carrega e cria a configuração do assistente em `config/jarvis.json`, incluindo apelidos de apps, sites e pastas.

## Estratégia de evolução

A primeira versão usava só regras e apelidos, para ter comportamento previsível. Desde então entraram o cérebro com modelo de linguagem para interpretar ordens livres e a memória curta de contexto. Os próximos passos naturais são:

1. criar um sistema de skills/plugins
2. introduzir automações com confirmação para ações sensíveis
3. adicionar wake word e execução em background

## Como executar

```bash
python main.py
```

Ou escolha o modo:

```bash
python main.py --mode text
python main.py --mode voice
python main.py --mode hybrid
python main.py --list-audio-devices
```

No modo `hybrid`, você pode digitar o comando ou usar `/voz` para ouvir o microfone.

## Testes

```bash
python -m unittest discover -s tests
```

Os testes cobrem o roteador e o cérebro por regras, sem chamar a API.

## Configuração

Na primeira execução, o projeto cria `config/jarvis.json` a partir de `config/jarvis.example.json`.
Edite esse arquivo para apontar seus programas, sites e pastas favoritas. Ele fica fora do Git, porque guarda caminhos da sua máquina.

Para usar a OpenAI como cérebro e como transcrição de voz, crie um arquivo `.env` (há um modelo em `.env.example`) com:

```env
OPENAI_API_KEY=sua_chave_aqui
```

Por padrão:

- `brain_provider: "auto"` usa a OpenAI se houver chave, e regras se não houver
- `stt_provider: "auto"` usa a OpenAI para entrada de voz se houver chave, e o Windows como alternativa

Exemplo de apelido de aplicativo:

```json
"apps": {
  "vscode": {
    "command": ["Code.exe"]
  },
  "spotify": {
    "path": "C:\\Users\\SEU_USUARIO\\AppData\\Roaming\\Spotify\\Spotify.exe"
  }
}
```

## Comandos iniciais

- `abra o youtube`
- `abrir bloco de notas`
- `abrir pasta downloads`
- `pesquise python decorators no google`
- `quero ouvir musica`
- `abra meu email`
- `que horas sao`
- `ajuda`
- `sair`

## Observações

- O projeto foi preparado para Windows.
- A saída de voz usa a infraestrutura nativa do Windows.
- A entrada de voz funciona melhor com `OPENAI_API_KEY`, pois usa gravação real do microfone e transcrição pela API.
- Sem chave da OpenAI, o projeto tenta usar o reconhecimento de voz do Windows.
