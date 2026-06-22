# LinkedIn no Claude via Unipile (MCP)

Conecte o **Claude** ao **LinkedIn** e comande tudo em linguagem natural:
gerar listas de leads, enriquecer dados, encontrar decisores, analisar o mercado,
escrever posts, enviar convites de conexão e mandar mensagens na DM.

Este é um servidor **MCP** (Model Context Protocol) que liga o Claude à
[Unipile](https://www.unipile.com/?utm_source=linkedin&utm_campaign=passionfroot_victor-baggio),
a maior e melhor API de LinkedIn do mercado.

> Feito por [Victor Baggio](https://www.linkedin.com/in/victorzbaggio) / Playbook Lab.
> Baseado no projeto open-source [unipile-linkedin-mcp](https://github.com/bhaktatejas922/unipile-linkedin-mcp),
> estendido com a família completa de **Posts** (publicar, comentar, reagir, ler posts e engajamento).

---

## 🤖 Jeito mais fácil: deixe o Claude te instalar

Abra o Claude e cole isto:

> "Quero conectar meu LinkedIn ao Claude usando este repositório:
> https://github.com/vzbaggio/unipile-linkedin-mcp
> Leia o README e me guie passo a passo: criar minha conta na Unipile, conectar meu
> LinkedIn, pegar as 3 credenciais e configurar o Claude Desktop. Vá uma etapa por vez."

O Claude segue as instruções abaixo com você. Se preferir fazer na mão, é só seguir
os passos a seguir.

---

## Passo 1 — Crie sua conta na Unipile e conecte o LinkedIn

1. Crie sua conta aqui 👉 **[unipile.com](https://www.unipile.com/?utm_source=linkedin&utm_campaign=passionfroot_victor-baggio)**
   (tem teste grátis para começar).
2. No painel, vá em **Accounts → Add account → LinkedIn** e faça login na sua conta
   do LinkedIn. A própria Unipile cuida da conexão de forma segura.

## Passo 2 — Pegue suas 3 credenciais

No painel da Unipile você precisa de 3 valores:

| Credencial | Onde achar |
|---|---|
| `UNIPILE_BASE_URL` | É o seu **DSN** + `/api/v1`. Ex: `https://apiXX.unipile.com:PORTA/api/v1` |
| `UNIPILE_API_KEY` | Em **Access Tokens / API Keys** — gere uma chave |
| `UNIPILE_ACCOUNT_ID` | Em **Accounts**, abra a conta do LinkedIn conectada e copie o ID |

> 🔒 Trate a `UNIPILE_API_KEY` como uma senha. Ela dá acesso de escrita à sua conta
> de LinkedIn (enviar convite, mandar mensagem, postar). Nunca a compartilhe nem a
> publique em repositório público.

## Passo 3 — Instale o `uv`

O `uv` é o que roda o servidor (ele instala o resto sozinho).

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
**macOS (com Homebrew):**
```bash
brew install uv
```
**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Passo 4 — Configure o Claude Desktop

Abra o arquivo de configuração do Claude Desktop:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

E adicione o bloco abaixo dentro de `mcpServers` (troque pelos seus 3 valores).
Esta versão roda o servidor **direto do GitHub**, sem precisar baixar nada:

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
        "UNIPILE_API_KEY": "sua-chave",
        "UNIPILE_ACCOUNT_ID": "seu-account-id"
      }
    }
  }
}
```

> Se o `uv` não for encontrado, troque `"command": "uv"` pelo caminho completo
> (descubra com `which uv` no Mac/Linux ou `where uv` no Windows). Ex. no Mac com
> Homebrew: `/opt/homebrew/bin/uv`.

## Passo 5 — Reinicie o Claude Desktop e teste

Feche e abra o Claude Desktop. Depois peça, por exemplo:

- "Busca 5 heads de vendas no Brasil no LinkedIn."
- "Pega o perfil completo do fulano e me resume a trajetória dele."
- "Quais foram os últimos posts da [empresa] e o que engajou mais?"
- "Escreve um rascunho de post sobre [tema] no meu estilo."
- "Manda um convite de conexão pro fulano com uma mensagem personalizada."

---

## 🛠️ O que dá pra fazer (29 ferramentas)

**Buscar e prospectar**
`search_people` · `search_people_sales_nav` · `search_companies` · `search_posts` ·
`get_search_params`

**Perfis e enriquecimento**
`get_my_profile` · `get_profile` · `get_company_profile` · `list_accounts`

**Conexões**
`send_invitation` · `list_invitations_sent` · `list_invitations_received` ·
`accept_invitation` · `decline_invitation` · `cancel_invitation` · `list_relations`

**Mensagens / DM**
`list_chats` · `get_chat_messages` · `send_message` · `start_chat` ·
`send_inmail` · `get_inmail_credits`

**Posts, comentários e reações** *(extensão deste fork)*
`get_user_posts` · `get_post` · `create_post` · `list_post_comments` ·
`comment_on_post` · `list_post_reactions` · `react_to_post`

---

## ⚠️ Boas práticas e limites

- **Respeite os limites do LinkedIn.** Convites: ~80–100/dia em conta paga, ~15/semana
  em conta gratuita. Exagerar pode levar a bloqueio. Vá com calma, principalmente em
  ações de escrita (convites, mensagens, posts).
- **Comentário criado via API não pode ser apagado pela API** — só manualmente pelo
  LinkedIn. Confira o texto antes de comentar.
- **A chave de API é sensível.** Não a exponha. O `.gitignore` deste repo já ignora
  o arquivo `.env`.
- Ferramentas de escrita (`send_invitation`, `send_message`, `create_post`,
  `comment_on_post`, `react_to_post`) executam ações reais na sua conta. Use com
  intenção.

## Rodando localmente (alternativa ao "via URL")

Se preferir rodar a partir do arquivo local, baixe o `server.py` e use:

```bash
UNIPILE_BASE_URL="https://SEU-DSN/api/v1" \
UNIPILE_API_KEY="sua-chave" \
UNIPILE_ACCOUNT_ID="seu-account-id" \
uv run server.py
```

No `claude_desktop_config.json`, troque a URL pelo caminho absoluto do arquivo.

## Licença

MIT. Veja [LICENSE](LICENSE).
