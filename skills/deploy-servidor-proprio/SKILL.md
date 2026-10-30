---
name: deploy-servidor-proprio
description: Pôr e manter no ar um app num servidor próprio com Docker Compose - imagens no GHCR, deploy puxado pelo servidor com volta automática, Caddy e túnel na frente, migração aditiva, variáveis fora do Git, backup cifrado com age provado de ponta a ponta, alerta pelo Healthchecks e scripts de operação em bash testados. Use ao mexer no Dockerfile, no compose de produção, nos scripts e timers de operação, no health check, em logs, ao criar variável de ambiente nova, ao escrever migração que vai para produção ou quando a pessoa pedir ajuda com um problema da produção.
---

# Deploy e operação num servidor próprio

## O caminho de um merge até a produção

1. **PR → CI**: qualidade, testes, segurança e a imagem: constrói as imagens, migra um banco limpo
   e roda um teste de fumaça no container com o mesmo endurecimento da produção.
2. **Merge na `main`** → o CI publica as imagens no registro (GHCR) com a etiqueta do commit e, só
   com tudo verde, move a etiqueta `:main` para elas.
3. **O servidor puxa** (timer do systemd a cada minuto): viu uma `:main` nova, baixa as imagens,
   pega os arquivos de deploy do MESMO commit, faz backup, migra o banco, troca SÓ o app e exige
   que o `/api/health` responda `ok` com o commit novo. Senão, volta o app para a versão anterior
   e avisa. Nenhuma porta aberta para o CI entrar no servidor.

## Regras

1. **Migração que vai para produção é aditiva** (tabela nova, coluna opcional, valor novo de
   enum). A volta automática troca só o app: a versão anterior precisa funcionar com o banco já
   migrado. Mudança incompatível = expandir num PR, contrair noutro.
2. **Variável de ambiente nova**: no `.env.example` (sem valor), na validação do app (zod), na lista
   de passagem do monorepo (Turborepo) e no modelo do servidor (`app.env.example`). No PR, avise que
   o valor de produção precisa estar no servidor ANTES do merge, senão o health falha e o deploy volta.
3. **Nada de segredo no Git, na imagem ou no log.** A imagem recebe tudo pelo `env_file` do
   compose. Valor de mentira para o build só dentro do `RUN`. O logger apaga senha, token, cookie e
   chaves por caminho (redact); e-mail só mascarado.
4. **Todo log do servidor** é JSON com um `event` curto e estável (`email.send_failed`). Nunca
   `console.log`, nunca o corpo do pedido.
5. **O app não publica porta**: só o proxy (Caddy) fala com ele, numa rede interna. Atrás de um
   túnel (Cloudflare), o proxy monta o IP real a partir do cabeçalho do túnel e repassa um único
   `X-Forwarded-For`; o app confia só nele.
6. **Containers endurecidos**: `read_only`, `cap_drop: [ALL]` (com o mínimo de volta, como
   `NET_BIND_SERVICE` para o proxy), `no-new-privileges`, usuário sem privilégio, limite de
   memória, redes internas sem saída para a internet quando o serviço não precisa dela.
7. **Health de verdade**: o `/api/health` confere o banco e devolve a versão (o commit). O deploy
   só considera a versão nova no ar quando o health diz `ok` COM o commit novo.

## Backup e restauração

- Backup diário cifrado com **age** (chave pública no servidor; a privada só no gerenciador de
  senhas), cópia fora de casa (rclone) e retenção. Backup antes de todo deploy.
- Junto com o backup, um **manifesto** cifrado: quantas linhas cada tabela tinha, lido numa
  transação de leitura estável (se o banco mudou durante o dump, refaça ou avise).
- **Prove a restauração de ponta a ponta**, de tempos em tempos: baixar a cópia de fora, decifrar,
  restaurar num banco temporário, conferir tabela a tabela com o manifesto e subir o app sobre esse
  banco. Backup que nunca foi restaurado não é backup.
- Apagar dados da produção (zerar antes do uso real) só por um script que guarda a lista do que
  FICA, faz backup antes, roda tudo numa transação e foi ensaiado numa cópia restaurada.

## Alertas

- Healthchecks.io (gratuito): um check por rotina (backup, deploy, alerta de segurança). O script
  avisa `/start`, sucesso ou `/fail`; o silêncio também alerta.
- O aviso diz a verdade: confira o código HTTP da resposta, mostre o código (nunca o endereço de
  ping, que é segredo) e devolva erro quando não chegou. Em backup e deploy o aviso é acessório
  (`|| true`); no script cujo trabalho é avisar, a falha aparece.
- Valide o formato do endereço ao gravar: um endereço colado duas vezes num campo escondido vira
  um alerta que nunca chega.

## Scripts de operação (bash)

- `set -Eeuo pipefail`, uma biblioteca comum (`lib.sh`) com `log`, `warn`, `die`, o compose de
  produção e um cadeado (`flock`) para dois scripts não rodarem juntos.
- Corpo dentro de `main()`, `shellcheck -x` limpo **na versão do servidor** (o Ubuntu 24.04 tem o
  ShellCheck 0.9; códigos de aviso mudam entre versões), sem `eval`.
- Arquivos de configuração e de estado do servidor com permissão 600/750 e dono próprio: os
  comandos que leem lá dentro vão com `sudo -u <usuário do serviço>`.
- **Testes sem servidor**: um `docker` e um Healthchecks de mentira (um servidor HTTP local que
  responde o código escolhido) e uma pasta temporária no lugar da casa do serviço. Teste o caso
  "nada aconteceu" (nenhum evento, log vazio), não só o caso com dados.
- Pegadinhas já pegas:
  - com `pipefail`, um `grep` que não acha nada derruba o pipeline: `{ grep ... || [ $? -eq 1 ]; }`;
  - `curl --retry -o /dev/null` desiste calado (erro 23) quando precisa tentar de novo: grave a
    resposta num arquivo temporário;
  - função chamada só pelo `trap` vira aviso do ShellCheck: ponha o comando no próprio `trap`;
  - comentário que começa com `# shellcheck` vira diretiva;
  - o que roda em segundo plano num script ignora o Ctrl+C: repasse o sinal no `trap`;
  - o bash lê o script enquanto roda: nunca edite um script que está rodando.
- Espera longa mostra progresso (uma linha por minuto).

## Nunca

- `docker compose down -v` (apaga os volumes, inclusive o banco), apagar o volume do banco ou
  editar arquivos no clone do servidor (o deploy descarta).
- Runner self-hosted do CI no servidor de casa: o CI de um PR passaria a rodar lá dentro.
- Rodar seed, zerar ou restaurar na produção sem a pessoa pedir.

## Problema na produção? Diagnostique antes de mudar

```bash
sudo -u <usuário> <script de status>                  # versão, saúde, backups, alertas
journalctl -u <unidade do deploy> --since "1 hour ago"
docker compose -p <projeto> logs --since 30m --no-log-prefix web | jq -R 'fromjson? // {texto: .}'
```

Tenha um runbook com cada situação (deploy falhou, disco cheio, app não sobe, restaurar) e siga-o.
