---
name: teste-e2e-playwright
description: Testes de ponta a ponta com Playwright que não ficam instáveis - explorar com o Playwright MCP e gravar como spec, seletores por papel, dados próprios por teste, esperar o servidor e não o relógio, várias pessoas, IDOR, axe e foco, e o CI contra o build de produção. Use ao criar ou mudar testes E2E, ao reproduzir um defeito pelo navegador ou quando uma tela nova precisar de teste.
---

# Testes de ponta a ponta com Playwright

## Explorar primeiro, gravar depois

1. Com o app no ar, use o **Playwright MCP** para abrir a tela, navegar pelo snapshot de
   acessibilidade e reproduzir o caminho (ou o defeito).
2. Transforme o que funcionou num spec versionado. O MCP serve para descobrir; quem garante é o
   spec, que roda em todo PR.

## Seletores

- **Por papel e rótulo**: `getByRole("button", { name: "Aceitar convite" })`, `getByLabel("Nome")`.
  Nada de classe CSS, `nth-child` ou `data-testid` para o que a pessoa vê.
- Texto que aparece em mais de um lugar: `{ exact: true }` ou restrinja pela região
  (`getByRole("region", { name: "Pessoas" })`).
- Seletor difícil de escrever costuma ser tela sem rótulo acessível: corrija a tela.

## Dados

- **Cada teste cria o que usa** (pessoa, registro) com um nome único (e-mail com o nome do teste e
  do projeto, porque desktop e celular rodam juntos) e apaga no `afterEach`.
- Dado compartilhado entre testes só para leitura. Teste que confere SOMA ou CONTAGEM cria um
  conjunto próprio e compara a tela com uma consulta ao banco.
- Os testes rodam em qualquer ordem, em várias partes (`--shard`) e máquinas: nenhum depende de
  outro ter rodado antes.

## Esperar o estado, nunca o relógio

- Nada de `waitForTimeout`, aumentar timeout ou `retries` para "passar".
- Aviso, URL ou lista que só mudam depois de uma resposta do servidor são conferidos **depois
  dela**: registre `page.waitForResponse(...)` ANTES do clique e espere depois; navegação, com
  `page.waitForURL(...)`. O `expect` fica para o que a tela mostra quando o estado já chegou.
- **Hidratação**: digitar antes do React carregar perde o texto. Marque no HTML quando a tela está
  pronta (um atributo que o componente liga num efeito, depois do commit) e espere por ele ao abrir
  qualquer página. Não espere por detalhes internos do React (chaves `__reactFiber$`): eles aparecem
  antes do commit.
- **Trabalho em segundo plano** (fila): `expect.poll` recarregando a página, e dentro do poll nada
  que espere sozinho (`count()`, não `textContent()` de algo que pode não existir).
- Teste instável não se conserta com retry: rode a suíte inteira várias vezes, ache a corrida
  (dado compartilhado, medida antes da animação, pedido sem resposta) e corrija a causa. O trace
  mostra a ordem dos pedidos (`status -1` = ainda sem resposta quando o `expect` desistiu).

## Next.js com Cache Components

O Next guarda as últimas telas escondidas (`<Activity>`, `display: none`) em vez de desmontá-las.
`getByRole` ignora o escondido; `getByLabel`, `getByText` e `locator(...)` não: use
`.filter({ visible: true })`. Tela escondida não roda efeitos, então a marca de "pronta" dela pode
nunca ligar: conte só a marca do que está à vista.

## Várias pessoas

Cada pessoa num contexto próprio (`browser.newContext()`), como outro aparelho, com a conta já
logada. Um helper que cria a conta pelo caminho de verdade (inclusive 2FA) e devolve a página
evita repetir o login em cada teste.

## Segurança e acessibilidade em todo PR

- **Toda página** entra numa lista central percorrida por testes gerados: sem sessão manda para o
  login; com sessão, axe nos temas claro e escuro, foco visível, nenhuma violação de CSP.
- Tela que só existe no meio de um fluxo ganha a conferência do axe no próprio teste do fluxo.
- **IDOR**: para cada tela com id na URL, outra pessoa abre a URL e recebe o mesmo 404 de um id
  inexistente, **sem nenhum dado** do recurso no HTML (`page.content()` não contém o nome).
- **Formulários sem JavaScript**: confira no HTML que todo `<form>` declara método e ação, e que
  senha, e-mail ou código nunca vão na URL (GET) se o envio acontecer antes do React.
- Ao conferir para onde um link aponta, leia `new URL(href).protocol` e aceite só `http:`/`https:`;
  nunca `startsWith("javascript:")` (o CodeQL acusa, mesmo em teste).

## Serviços de fora

Nenhum teste depende da internet. Todo serviço externo (banco, mensageria, e-mail, consulta de
senhas vazadas) tem uma versão de mentira local que o `webServer` do `playwright.config.ts` sobe,
ou fica desligado por variável de ambiente nos testes. Serviço novo entra ali no mesmo PR.

## Medir tempo

Limite de tempo (`toBeLessThan(ms)`) só contra o build de produção (`test.skip` fora dele): no
servidor de desenvolvimento, o número mede a máquina.

## No CI

- Rode a suíte contra o **build de produção** (o mesmo servidor que vai ao ar), em partes
  (`--shard=1/3`), com `trace: "retain-on-failure"` e o relatório juntado (`merge-reports`) como
  artefato. Teste que só faz sentido no servidor de desenvolvimento leva uma etiqueta (`@dev`) e
  roda num job próprio: sem ela, ele seria pulado no CI sem ninguém ver.
- Diante de uma falha, leia o trace antes de mexer no teste.

## Nunca

`test.only` no commit, `test.skip` sem o motivo escrito, `waitForTimeout`, `force: true` para
clicar no que está coberto, ou mudar o teste para casar com um defeito.

## Rodar

```bash
pnpm exec playwright test                                   # tudo
pnpm exec playwright test e2e/login.spec.ts --project=desktop
pnpm exec playwright test --trace=retain-on-failure --output=test-results/um-teste
pnpm exec playwright show-report
```
