# Para o Claude

Se o usuário pediu para **instalar / configurar este MCP**, leia o arquivo
[`INSTALL.md`](INSTALL.md) e siga o passo a passo de lá, de cima para baixo.

Resumo do que você vai fazer:
1. Garantir o `uv` instalado.
2. Pedir ao usuário as 3 credenciais da Unipile (guiando no painel) — única ação manual dele.
3. Registrar o MCP (`claude mcp add` no Claude Code, ou editar `claude_desktop_config.json` no Desktop).
4. Pedir para reiniciar o Claude e validar com uma chamada de leitura.
5. Mostrar exemplos de uso.

Onde houver **🙋 AÇÃO DO USUÁRIO** no INSTALL.md, pause e guie a pessoa. Fale em
português. Nunca exponha a `UNIPILE_API_KEY` em texto depois de configurada.
