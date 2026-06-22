# INSTALL — Instruções de instalação automática

> **Para o Claude (agente):** o usuário te pediu para instalar e configurar este MCP.
> Siga este passo a passo de cima para baixo. Onde houver **🙋 AÇÃO DO USUÁRIO**,
> pause, explique de forma simples e espere a pessoa te responder antes de continuar.
> Fale em português, de forma amigável, e nunca exponha a `UNIPILE_API_KEY` em texto
> visível depois de configurada. Não invente valores: se faltar uma credencial, peça.

Este MCP conecta o Claude ao LinkedIn através da [Unipile](https://www.unipile.com/?utm_source=linkedin&utm_campaign=passionfroot_victor-baggio).
São 29 ferramentas: buscar pessoas/empresas, enriquecer perfis, achar decisores,
analisar posts, publicar, comentar, reagir, enviar convites e mensagens.

---

## Passo 0 — Descubra o ambiente

1. Identifique o sistema operacional do usuário (macOS, Windows ou Linux).
2. Identifique qual cliente Claude ele está usando agora:
   - **Claude Code** (terminal/IDE) → você vai registrar o MCP com o comando `claude mcp add`.
   - **Claude Desktop** (app) → você vai editar o arquivo `claude_desktop_config.json`.
   Se não tiver certeza, pergunte: *"Você está falando comigo pelo app Claude Desktop ou pelo Claude Code (terminal)?"*

## Passo 1 — Garanta o `uv` instalado

O `uv` é o que roda o servidor. Verifique se já existe:

```bash
uv --version
```

Se **não** estiver instalado, instale (sem pedir ação ao usuário, apenas rode):

- **macOS / Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

Depois confirme novamente com `uv --version`. Anote o caminho completo do `uv`
(`which uv` no Mac/Linux, `where uv` no Windows) — você pode precisar dele.

## Passo 2 — 🙋 AÇÃO DO USUÁRIO: pegar as 3 credenciais da Unipile

Você precisa de 3 valores que só o usuário consegue obter no painel da Unipile.
Guie a pessoa assim (uma coisa de cada vez, com paciência):

1. **Criar conta:** peça para acessar e criar a conta (tem teste grátis):
   👉 https://www.unipile.com/?utm_source=linkedin&utm_campaign=passionfroot_victor-baggio
2. **Conectar o LinkedIn:** no painel, ir em **Accounts → Add account → LinkedIn**
   e fazer login. A Unipile cuida da conexão com segurança.
3. **Copiar os 3 valores** e te enviar:
   - `UNIPILE_BASE_URL` → é o **DSN** da conta + `/api/v1`.
     Ex.: `https://api38.unipile.com:16871/api/v1`
   - `UNIPILE_API_KEY` → em **Access Tokens / API Keys**, gerar e copiar a chave.
   - `UNIPILE_ACCOUNT_ID` → em **Accounts**, abrir a conta de LinkedIn conectada e copiar o ID.

Espere a pessoa te mandar os 3 valores antes de seguir. Se ela travar em algum
ponto do painel, ajude a localizar o item.

## Passo 3 — Registre o MCP

Use os 3 valores do passo anterior. O servidor roda direto do GitHub (sem baixar nada):

```
https://raw.githubusercontent.com/vzbaggio/unipile-linkedin-mcp/main/server.py
```

### Se for Claude Code
Rode (substituindo os valores). O `--scope user` deixa o MCP disponível em qualquer projeto:

```bash
claude mcp add unipile-linkedin --scope user \
  --env UNIPILE_BASE_URL="https://SEU-DSN/api/v1" \
  --env UNIPILE_API_KEY="SUA-CHAVE" \
  --env UNIPILE_ACCOUNT_ID="SEU-ACCOUNT-ID" \
  -- uv run https://raw.githubusercontent.com/vzbaggio/unipile-linkedin-mcp/main/server.py
```

> Se o `uv` não estiver no PATH do cliente, troque `uv` pelo caminho completo
> que você anotou no Passo 1.

### Se for Claude Desktop
Edite o arquivo de configuração (crie se não existir) e adicione a entrada
`unipile-linkedin` dentro de `mcpServers`, **preservando** o que já existir lá.

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Entrada a adicionar:

```json
{
  "mcpServers": {
    "unipile-linkedin": {
      "command": "uv",
      "args": [
        "run",
        "https://raw.githubusercontent.com/vzbaggio/unipile-linkedin-mcp/main/server.py"
      ],
      "env": {
        "UNIPILE_BASE_URL": "https://SEU-DSN/api/v1",
        "UNIPILE_API_KEY": "SUA-CHAVE",
        "UNIPILE_ACCOUNT_ID": "SEU-ACCOUNT-ID"
      }
    }
  }
}
```

> Em `command`, se o `uv` não for encontrado, use o caminho absoluto do Passo 1
> (ex.: `/opt/homebrew/bin/uv` no Mac com Homebrew).

## Passo 4 — 🙋 AÇÃO DO USUÁRIO: reiniciar o Claude

- **Claude Desktop:** peça para fechar e abrir o app de novo.
- **Claude Code:** o MCP é carregado em uma nova sessão; oriente conforme o caso.

Avise que, ao reabrir, deve aparecer o conector **`unipile-linkedin`** ativo.

## Passo 5 — Valide a conexão

Depois do restart, confirme com uma chamada **somente leitura** (não faz nada
visível na conta). Por exemplo, use a ferramenta `get_my_profile` ou `list_accounts`
e mostre ao usuário que voltou o nome/perfil dele. Se voltar erro de credencial,
reveja os 3 valores do Passo 2 com a pessoa.

## Passo 6 — Mostre como usar

Com tudo funcionando, dê 2-3 exemplos prontos para a pessoa testar:

- *"Busca no LinkedIn 10 CEOs de indústria automotiva no Brasil numa tabela."*
- *"Pega o perfil completo de [link/nome] e me resume a trajetória + 2 ganchos de abordagem."*
- *"Quais posts sobre 'IA em vendas' estão bombando essa semana? Resume os temas."*

> ⚠️ Lembre o usuário: ações de **escrita** (convite, mensagem, post, comentário)
> acontecem de verdade na conta dele. Respeite os limites do LinkedIn
> (~80–100 convites/dia em conta paga, ~15/semana em conta grátis) para não tomar bloqueio.
> A `UNIPILE_API_KEY` é sensível — nunca compartilhar.

---

## Lista completa de ferramentas (29)

**Buscar/prospectar:** `search_people`, `search_people_sales_nav`, `search_companies`, `search_posts`, `get_search_params`
**Perfis:** `get_my_profile`, `get_profile`, `get_company_profile`, `list_accounts`
**Conexões:** `send_invitation`, `list_invitations_sent`, `list_invitations_received`, `accept_invitation`, `decline_invitation`, `cancel_invitation`, `list_relations`
**Mensagens:** `list_chats`, `get_chat_messages`, `send_message`, `start_chat`, `send_inmail`, `get_inmail_credits`
**Posts:** `get_user_posts`, `get_post`, `create_post`, `list_post_comments`, `comment_on_post`, `list_post_reactions`, `react_to_post`
