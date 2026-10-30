---
name: commit-e-pr
description: Branch por tarefa, Conventional Commits em português e pull request que só entra com o CI verde. Use ao criar branch, preparar um commit, sugerir a mensagem de um commit ou abrir e fazer o merge de um PR.
---

# Commits e pull requests

O histórico do repositório é documentação: quem lê `git log` daqui a um ano precisa entender o que
mudou e por quê, sem abrir cada diff.

## Branch

- Uma branch por tarefa, criada da `main` atualizada: `git switch main && git pull --ff-only && git switch -c tipo/descricao-curta`.
- O nome começa pelo tipo do commit principal: `feat/login-com-passkey`, `fix/soma-do-filtro`,
  `chore/atualiza-node`. Se o projeto anda por marcos (milestones), o marco pode entrar no nome
  (`feat/marco3-login-google`).
- Nunca trabalhe direto na `main`. A `main` só recebe código por pull request.

## Mensagem de commit (Conventional Commits)

```
tipo(escopo opcional): o que muda, no imperativo, em português, até 100 caracteres

Corpo opcional: o PORQUÊ, não o quê (o diff já mostra o quê). Linhas de até ~72 colunas.

Refs #12
```

| Tipo       | Quando                                              |
| ---------- | --------------------------------------------------- |
| `feat`     | funcionalidade nova para quem usa                   |
| `fix`      | correção de defeito                                 |
| `refactor` | mudança interna sem mudar comportamento             |
| `perf`     | mais rápido ou mais leve, mesmo comportamento       |
| `test`     | só testes                                           |
| `docs`     | só documentação                                     |
| `build`    | dependências, gerenciador de pacotes, imagem Docker |
| `ci`       | o pipeline (GitHub Actions e afins)                 |
| `chore`    | manutenção que não se encaixa acima                 |
| `style`    | formatação, sem mudança de lógica                   |

- O escopo é a parte do sistema (`auth`, `db`, `ui`, `deps`, `operacao`), não o nome do arquivo.
- Mudança que quebra quem usa: `feat!:` ou o rodapé `BREAKING CHANGE: ...`.
- **Um commit, uma mudança lógica.** Se a descrição precisa de "e", provavelmente são dois commits.
- Commit que corrige o que um PR anterior trouxe diz qual: `fix(alerta): ... (revisão do #74)`.

## Antes do commit

1. Rode o que o CI roda (lint, tipos, testes, build). O hook local é atalho, não garantia.
2. `git status --short`: só os arquivos da mudança. Nada de `.env`, dump de banco, extrato,
   planilha com dado real ou relatório gerado.
3. `git diff --staged` lido de verdade: é a última chance barata de achar o que não devia ir.

## Pull request

1. Título no mesmo formato do commit: ele vira a mensagem do squash na `main`.
2. Corpo: o que muda, por quê, como foi testado, riscos e o que a pessoa precisa fazer fora do
   código (variável nova na produção, passo manual). `Closes #N` fecha a issue no merge.
3. Abra como rascunho (`gh pr create --draft`) enquanto o CI roda; `gh pr ready` quando estiver verde.
4. Merge **só com o CI verde**, por squash, apagando a branch:
   `gh pr checks --watch --fail-fast && gh pr merge --squash --delete-branch`.
5. Depois do merge, espere o CI da `main` (o do push, não o do PR) antes de esperar o deploy:
   `gh run list --workflow ci.yml --branch main --event push --limit 1`.

## Check vermelho

- Leia o log antes de mexer: `gh run view <id> --log-failed`.
- "cancelled" não é "failed": costuma ser tempo esgotado de um job (`timeout-minutes`) ou uma
  execução mais nova na mesma branch (`concurrency`). Veja qual job e qual passo antes de rodar de
  novo (`gh run rerun <id> --failed`).
- Nunca "conserte" o CI desligando a verificação, subindo o limite de tempo sem entender a
  causa, ou marcando o teste para pular.

## Nunca

- `--no-verify` para pular os hooks.
- `git push --force` na `main`, ou em branch que outra pessoa usa.
- Reescrever um commit que já está na `main`.
- Segredo na mensagem de commit ou no corpo do PR (eles são públicos e eternos).
