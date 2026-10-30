# fintrack-skills

Sete skills em português para agentes de código (Claude Code e outros que leem o formato
[Agent Skills](https://agentskills.io)), para apps web com **Next.js 16, Better Auth, Prisma 7,
Playwright e deploy num servidor próprio com Docker Compose**.

Elas nasceram no [FinTrack](https://github.com/danillo-valle/fintrack), um app de finanças pessoais
construído em módulos, e foram **reescritas sem nada dele**: nenhum nome de tela, tabela ou pasta
do projeto, só as regras e as lições que valem para qualquer projeto parecido. O FinTrack continua
com as suas skills próprias, que apontam para os arquivos dele.

Versão atual: **v1.0.0**.

## As skills

| Skill                                                                | Para quê                                                                                                                                                  |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`commit-e-pr`](skills/commit-e-pr/SKILL.md)                         | Branch por tarefa, Conventional Commits em português, PR com o CI verde e o que fazer com um check vermelho                                               |
| [`migracao-prisma`](skills/migracao-prisma/SKILL.md)                 | Mudar o banco com o Prisma 7 sem perder dados: migração aditiva, CHECK e gatilho à mão, dinheiro exato, testes de integração e o que um agente nunca roda |
| [`teste-e2e-playwright`](skills/teste-e2e-playwright/SKILL.md)       | E2E que não fica instável: seletores por papel, dados próprios, esperar o servidor e não o relógio, IDOR, axe e o CI contra o build de produção           |
| [`seguranca-owasp`](skills/seguranca-owasp/SKILL.md)                 | OWASP Top 10:2025 item por item, ZAP, OSV-Scanner, CodeQL, CSP com nonce, SQL parametrizado, texto limpo na entrada, eventos e alerta                     |
| [`deploy-servidor-proprio`](skills/deploy-servidor-proprio/SKILL.md) | Deploy puxado pelo servidor com volta automática, migração aditiva, backup com age provado de ponta a ponta, alertas e scripts de bash testados           |
| [`auth-next-better-auth`](skills/auth-next-better-auth/SKILL.md)     | O `proxy.ts` não é barreira: sessão em toda página, action e rota, reautenticação, 404 para o que é de outra pessoa e os testes que provam                |
| [`ui-shadcn-tailwind`](skills/ui-shadcn-tailwind/SKILL.md)           | shadcn/ui e Tailwind v4 com tokens e contraste testado, formulário que funciona antes do React, foco do WCAG 2.2 e o Cache Components                     |

Cada skill tem uma descrição que diz quando usá-la; o agente carrega a skill sozinho quando a
tarefa combina, ou você pede pelo nome.

## Instalar

**No Claude Code, como plugin** (as sete de uma vez, atualizáveis):

```text
/plugin marketplace add danillo-valle/fintrack-skills
/plugin install fintrack-skills@fintrack-skills
```

As skills aparecem com o prefixo do plugin (`fintrack-skills:commit-e-pr`).

**Copiando para um projeto** (só as que quiser, editáveis):

```bash
git clone https://github.com/danillo-valle/fintrack-skills.git /tmp/fintrack-skills
mkdir -p .claude/skills
cp -r /tmp/fintrack-skills/skills/commit-e-pr .claude/skills/
```

Copiadas, elas são do seu projeto: acrescente os caminhos e as regras dele (onde fica a função de
acesso, o nome do script de status, a lista de páginas dos testes). Foi assim que elas nasceram.

## O que elas assumem

Next.js 16 (App Router, `proxy.ts`, Cache Components), React 19, TypeScript estrito, Better Auth,
Prisma ORM 7 com PostgreSQL, Playwright com axe, pnpm, GitHub Actions e um servidor Linux com
Docker Compose. Onde a sua pilha for outra, a regra costuma valer e o comando muda.

## Contribuir

```bash
python3 scripts/validar.py            # o mesmo que o CI roda
claude plugin validate . --strict     # se tiver o Claude Code
```

O validador confere o cabeçalho de cada skill, os manifestos e que nenhuma skill fale de um
projeto específico. Issues e PRs são bem-vindos, em português.

## Licença

[MIT](LICENSE).
