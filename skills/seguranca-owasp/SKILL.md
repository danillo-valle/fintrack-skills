---
name: seguranca-owasp
description: Segurança contínua de uma aplicação web contra o OWASP Top 10:2025 - o documento item por item, ZAP passivo e OSV-Scanner barrando o PR, ZAP ativo só numa cópia local, CodeQL sem dispensa fácil, CSP com nonce e hash, SQL parametrizado, texto de fora limpo na entrada, eventos de segurança no log com alerta e ações do CI presas pelo commit. Use ao criar rota pública, mexer em cabeçalhos ou na CSP, acrescentar ou atualizar dependência, mexer no login ou no log, quando uma verificação de segurança barrar o PR, ou ao revisar a segurança de uma funcionalidade.
---

# Segurança contra o OWASP Top 10:2025

## O documento anda com o código

Mantenha um documento com os 10 itens do OWASP Top 10:2025, cada um com: o que se aplica ao
sistema, a proteção, **o arquivo e o teste que provam**, e as pendências com prioridade. PR que
mexe num item (acesso, cabeçalho, dependência, login, log, erro) atualiza a linha dele no mesmo PR.
Uma tabela de "exceções em vigor" guarda cada exceção de ferramenta com o motivo e a prova.

## No CI, barrando o PR

| Verificação                                                    | O que barra                                                         |
| -------------------------------------------------------------- | ------------------------------------------------------------------- |
| ZAP passivo (Automation Framework) contra a imagem de produção | alerta de risco Baixo ou maior, sem sessão e com uma conta de teste |
| OSV-Scanner nos lockfiles                                      | qualquer vulnerabilidade conhecida numa dependência                 |
| CodeQL                                                         | qualquer alerta novo                                                |
| Busca de segredos (gitleaks)                                   | segredo em qualquer commit do histórico                             |

Regras de cada uma:

1. **ZAP**: a rodada logada usa uma conta de teste criada pelo caminho de verdade (cadastro,
   e-mail, 2FA), nunca por SQL; o cookie entra só por variável de ambiente, nunca na linha de
   comando. Exceção (`alertFilter`) só com a prova de que a proteção existe por outro caminho, de
   preferência um teste. Nunca subir o nível de erro, tirar a rodada logada ou excluir telas do
   contexto para o CI passar. Rota sem link (o spider não acha) entra num job `requestor`.
2. **OSV-Scanner**: corrija atualizando. Exceção no `osv-scanner.toml` só presa ao pacote e à
   versão, com motivo e data de validade (`effectiveUntil`), e quando o código vulnerável não roda
   no sistema. Pacote publicado há menos de um dia não entra (`minimumReleaseAge` no pnpm).
3. **CodeQL**: corrija o código. Falso positivo só é dispensado com o motivo escrito no alerta, uma
   linha na tabela de exceções e um comentário no código. Em teste, tire o padrão que o CodeQL vê
   em vez de dispensar. Alerta aberto na `main` conta como alerta do PR.
4. **Ações do CI presas pelo commit**: `uses: dono/acao@<sha de 40 caracteres> # vX.Y.Z`; um bot
   (Dependabot, Renovate) propõe as versões novas. Permissões mínimas no workflow
   (`permissions: contents: read`) e mais só no job que precisa.
5. **Limite de tempo em todo job**, e passo que baixa algo da rede com o próprio limite: um
   download travado não pode segurar o pipeline até o fim do job.

## Varredura ativa: só numa cópia descartável

O ZAP ativo ataca de verdade (grava, apaga, manda e-mail). Rode antes de cada versão grande, numa
cópia local descartável (banco em memória, só em `127.0.0.1`, a mesma imagem que vai ao ar),
**nunca contra a produção**: o script deve recusar endereço que não seja local. Além dos alertas
do ZAP, conte os erros 500 do app no log durante o ataque: erro sem detalhe não vira alerta, mas é
defeito. Uma varredura longa escreve o progresso (uma linha por minuto): terminal calado parece
travado.

## Regras do código

1. **Rota pública nova** (sem sessão): o caminho exato numa lista central, nunca um prefixo.
2. **CSP**: `script-src` com nonce por pedido, nunca `'unsafe-inline'` em script nem em
   `style-src-elem` de produção. Biblioteca que injeta `<style>` sem nonce: o hash exato do texto,
   com um teste que calcula o hash a partir do pacote instalado (a atualização do pacote quebra o
   teste, e não a tela).
3. **SQL só parametrizado**: o template com parâmetros do ORM (no Prisma, `$queryRaw` com template ou `Prisma.sql`).
   Proíba no lint os caminhos que aceitam texto cru (`$queryRawUnsafe`, `$executeRawUnsafe`,
   `Prisma.raw`).
4. **Texto de fora, limpo na entrada**: todo texto livre que chega (formulário, URL, mensagem,
   arquivo, API de terceiro) passa por uma função única que tira caracteres de controle e
   invisíveis ANTES de qualquer conferência. Limpar só na hora de gravar faz a conferência olhar um
   texto e o banco guardar outro (um caractere invisível no meio de um número de cartão passa pela
   regra que o barraria). Nos schemas, um helper (`textField()`) em vez de `z.string()` cru, com um
   teste que barra o cru.
5. **Falha fechada**: na dúvida sobre acesso, 404 (o mesmo de um recurso inexistente); webhook
   responde igual para assinatura errada e evento desconhecido; a tela de erro mostra um código do
   log, nunca a mensagem ou a pilha.
6. **Webhook**: confira a assinatura sobre o corpo CRU antes de ler o JSON, recuse corpo grande e
   processe cada evento uma vez só (id do evento).
7. **Senha**: consulte senhas vazadas (Have I Been Pwned, por k-anonimato) com tempo limite curto e
   decida o que fazer sem resposta (recusar é o mais seguro); 2FA obrigatório quando os dados valem.

## Log e alerta (A09)

- Tentativa recusada (login errado, limite de tentativas, origem recusada, acesso negado, webhook
  com assinatura errada) vira um **evento** no log com nome estável (`auth.failed`,
  `access.denied`). Nunca o corpo do pedido, e-mail inteiro, senha, código ou token.
- Um alerta automático conta os eventos numa janela e avisa quando passa do limite, com o texto só
  com o nome do evento, a quantidade e o limite. O alerta também avisa "ok" a cada rodada, para que
  o silêncio (alerta parado) também dispare um aviso. Teste o caso "nenhum evento".

## Conferir antes do PR

```bash
pnpm exec vitest run <testes dos cabeçalhos e do login>
pnpm exec playwright test e2e/cabecalhos.spec.ts      # nenhuma violação de CSP nas telas
# o ZAP passivo do CI, rodado à mão contra a IMAGEM de produção no ar (não contra o dev)
```
