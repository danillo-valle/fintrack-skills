---
name: ui-shadcn-tailwind
description: Construir telas e componentes no Next.js 16 com shadcn/ui, Tailwind CSS v4 e tokens de tema - componentes de servidor por padrão, formulário que funciona antes do React, cores só por token com contraste testado, acessibilidade e foco do WCAG 2.2, avisos com desfazer e telas preservadas pelo Cache Components. Use ao criar ou alterar arquivos .tsx de interface, adicionar um componente do shadcn ou revisar a acessibilidade de uma tela.
---

# Interface com shadcn/ui e Tailwind

## De onde vem cada peça

- **Primitivos** (botão, campo, rótulo, diálogo, esqueleto): shadcn/ui, gerados pelo CLI
  (`pnpm dlx shadcn@latest add <nome>`) em `components/ui/`. Não edite à mão sem motivo.
- **Peças visuais repetidas** (cartão de resumo, linha de lista, barra de filtros, estado vazio):
  componentes próprios numa pasta de componentes visuais. Nunca copie classes de uma tela para
  outra: o que aparece duas vezes vira componente.
- **Peças que conhecem o domínio** ficam na pasta da funcionalidade e compõem as visuais. Regra de
  negócio nunca mora em componente: vai para um pacote de regras puras, com teste.
- Mantenha um **catálogo** (uma página só do desenvolvimento) com cada componente nos dois temas;
  antes de criar, procure lá.

## Servidor e cliente

- Componente de servidor por padrão. `"use client"` só quando precisa de estado, efeito, evento ou
  API do navegador, e o mais fundo possível na árvore.
- Componente de servidor não passa função para componente de cliente (nem um ícone como
  componente): passe o elemento pronto (`icon={<Casa aria-hidden />}`).

## Formulários

- **Server Action direto no `<form action>`** (pelo `useActionState`), sem função em volta: assim o
  envio funciona mesmo antes do React carregar. Embrulhar a action numa função faz o primeiro
  clique se perder.
- Formulário cujo envio precisa do navegador (cliente de login, por exemplo) sai com
  `method="post"` declarado: antes do React, o envio vai no corpo e nada vai para a URL.
- Validação no servidor sempre (zod); no envio, o foco vai ao primeiro campo com erro. O erro de
  um campo some quando ele fica válido; erro novo só no próximo envio.
- Formulário que pode aparecer duas vezes na tela (página atrás e modal na frente) recebe um
  prefixo de id, senão os rótulos apontam para o campo errado.

## Cores e tema

- **Sempre por token** (`bg-background`, `text-muted-foreground`, `text-destructive`, tokens
  próprios como `text-income`). Nunca cor fixa (`text-green-600`, `#1e5099`): o tema escuro depende
  dos tokens.
- Token novo: em `:root` E em `.dark`, ligado no `@theme inline` do Tailwind v4, e o par conferido
  num **teste de contraste** (texto ≥ 4,5:1; anel de foco, ícone e gráfico ≥ 3:1), inclusive o hover.
- Significado nunca só pela cor: entrada e saída de dinheiro levam sinal, seta e texto para leitor
  de tela. Cor que vira texto informativo usa uma "tinta" conferida a 4,5:1, não a cor de gráfico.
- Dinheiro e datas na tela só por funções únicas de formatação (moeda, fuso do usuário); valores em
  inteiros (centavos), nunca `number` com casas decimais.

## Acessibilidade (obrigatório)

1. Uma página, um `<h1>`; seções com `<h2>`; regiões com nome.
2. Todo campo com rótulo ligado (`htmlFor`/`id`); erro com `aria-invalid` + `aria-describedby`.
3. Botão só com ícone tem `aria-label`; ícone decorativo tem `aria-hidden`.
4. Tudo funciona só com teclado: Tab chega, Enter/Espaço aciona.
5. Alvos de toque com pelo menos 24 px (40 px no celular é melhor).
6. Nada de animação essencial; respeite "reduzir movimento".
7. axe em todas as telas nos testes, nos dois temas.

## Foco (WCAG 2.2)

- **Anel visível com contraste ≥ 3:1** (1.4.11): cor cheia, nunca o anel com transparência
  (`ring-ring/50`) que os componentes gerados trazem. Depois de um `shadcn add`, revise os anéis.
- **Foco nunca escondido** (2.4.11): cabeçalho fixo, barra inferior e avisos não cobrem o elemento
  focado (`scroll-padding` no `html`).
- **O foco nunca se perde**: quando o elemento focado some (excluir um item), leve o foco ao vizinho
  ou à mensagem de vazio (`tabIndex={-1}`); ao desfazer, devolva ao item restaurado.
- Campo com partes internas (`type="date"`): anel com `focus-within:`.

## Avisos e exclusão

- Sem "tem certeza?": exclua e ofereça **Desfazer** num aviso com tempo suficiente (10 s) e uma
  forma de pausar pelo teclado (2.2.1). Textos do aviso em português, inclusive os que só o leitor
  de tela lê.
- Criou algo num modal: volte para a lista com o aviso no TOPO e a linha nova marcada. Aviso no
  fim de um formulário longo passa despercebido.

## Next.js 16 com Cache Components

- O Next guarda as últimas telas escondidas (`<Activity>`, `display: none`): formulário com aviso
  de sucesso precisa recomeçar ao ser escondido (troque a `key` depois do envio); menu ou popover
  aberto fecha num efeito de limpeza; estado que recomeça a cada visita vem da URL, não do
  `useState`.
- Dado que depende do usuário fica fora do cache estático (`"use cache"` só com a etiqueta certa
  e invalidada por quem muda o dado).

## Layout

- Celular primeiro; colunas no desktop sem repetir o texto no HTML (repetir confunde leitor de tela
  e testes): `display: contents` e grade a partir de um breakpoint.
- Modal que cabe em telas baixas: aperte espaços com uma variante própria em vez de altura fixa ou
  `overflow: hidden`. No Safari, a parte que rola num painel de altura automática usa
  `flex-auto`, nunca `flex-1`.

## Antes de concluir

- A tela entrou na lista central dos testes (axe, foco, proteção).
- Conferida nos dois temas, em 390 px e no desktop, com teclado e com o modal aberto.
- Lint, tipos, testes e E2E passam.
