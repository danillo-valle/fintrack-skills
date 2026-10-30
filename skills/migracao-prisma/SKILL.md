---
name: migracao-prisma
description: Como mudar um banco PostgreSQL com o Prisma ORM 7 sem perder dados - schema em pasta, migração nomeada, regras que o Prisma não escreve (CHECK, gatilho), dinheiro exato, testes de integração e o que um agente de IA nunca roda sozinho. Use ao criar ou alterar arquivos do schema do Prisma, adicionar tabela, coluna, índice ou regra, mexer no seed ou antes de rodar migrate.
---

# Migrações com o Prisma 7

## Antes de mudar

- Leia o mapa das tabelas e as decisões do modelo de dados do projeto (diagrama, ADR). Mudança
  que não cabe no modelo é decisão de arquitetura: proponha o ADR antes do código.
- Confira o estado: `prisma migrate status` precisa dizer "Database schema is up to date!".

## Como o modelo cresce

Cada funcionalidade é um **acréscimo**, nunca uma reestruturação:

- **Coisa nova = tabela nova, coluna opcional (ou com `@default`) ou valor novo de enum.** Coluna
  obrigatória sem padrão numa tabela com linhas quebra a migração; valor de enum removido quebra
  quem ainda o usa.
- **Uma coluna nunca muda de significado.** Outro significado = coluna nova.
- **O que se calcula não se guarda** (saldo, status derivado, totais): duas cópias discordam.
- **Mudança incompatível (renomear, trocar tipo) = expandir e contrair.** PR 1: coluna nova, cópia
  dos dados e o código lendo a nova. PR 2, depois do deploy: remover a antiga. A produção precisa
  aguentar a versão anterior do app sobre o banco já migrado (é o que permite voltar o deploy).
- **Dados de vários donos (multi-tenant):** toda tabela do domínio leva o id do dono, e as ligações
  usam chave composta com ele (`@@unique([id, ownerId])` no alvo). Assim, nada aponta para o
  registro de outro dono, nem por erro do código.

## Regras

1. **Nunca edite uma migração já aplicada** (no seu banco, no CI, na `main` ou na produção). Mudou
   de ideia? Migração nova. Editar a antiga faz quem já aplicou divergir do histórico.
2. **Toda migração tem nome** que diz o que muda: `prisma migrate dev --name orcamento-por-semana`.
3. **Dinheiro**: `Decimal @db.Decimal(14, 2)` no banco; no código, inteiro em centavos (`bigint`),
   convertido em um único ponto (funções `toDbDecimal`/`fromDbDecimal` ou equivalentes). Nunca
   `Float`, `number`, `parseFloat` ou `toFixed`. Uma regra de lint que barre isso vale o esforço.
4. **Data sem hora** (vencimento, dia do lançamento, mês): `DateTime @db.Date`, convertida por
   funções próprias de "data civil". Fuso horário só entra quando há hora de verdade.
5. **Ids**: `String @id @default(uuid(7)) @db.Uuid` (ordenável pelo tempo, sem expor contagem).
6. **Nomes**: modelo em PascalCase com `@@map("snake_case")`; enum também com `@@map`.
7. **Toda chave estrangeira tem `onDelete` escolhido de propósito e um índice** (o PostgreSQL não
   indexa chave estrangeira sozinho). Chave composta opcional: `NoAction`, nunca `SetNull` (zeraria
   também a parte obrigatória da chave). O que está em uso é arquivado (`archivedAt`), não apagado.
8. **Regra que o Prisma não escreve** (CHECK, gatilho, índice parcial, função): gere com
   `--create-only`, acrescente o SQL no fim do `migration.sql` com um comentário por regra e só
   então aplique. O Prisma não enxerga CHECK nem gatilho e não tenta desfazê-los; índice parcial
   ele enxerga e quer "consertar" na migração seguinte, então prefira resolver pelo schema.
9. **Toda regra no banco ganha um teste de integração** que tenta quebrá-la contra um PostgreSQL de
   verdade e confere o NOME da regra na mensagem de erro (não só "deu erro").
10. **Tabelas da biblioteca de login** (Better Auth e afins): coluna nova vai pela configuração da
    biblioteca e pelo gerador dela, não à mão no schema.
11. **Dado sensível**: guarde só o necessário (de um cartão, só os 4 últimos dígitos, com CHECK no
    banco). Nunca em colunas livres como `notes` ou `metadata`.
12. **Seed só com dados sintéticos**, gerados de forma determinística (semente fixa), e que se
    recusa a rodar contra um banco que não seja local.

## Passo a passo

```bash
# 1. edite o arquivo certo do schema (o Prisma 7 aceita o schema em pasta: um arquivo por assunto)
pnpm exec prisma format                                  # alinha e confere a sintaxe
pnpm exec prisma migrate dev --name descricao --create-only   # gera o SQL SEM aplicar
# 2. leia o migration.sql gerado; acrescente CHECK, gatilho ou dados se precisar
pnpm exec prisma migrate dev                             # aplica e gera o cliente
pnpm exec prisma generate                                # garante o cliente atualizado
# 3. testes de integração contra o banco, depois a suíte inteira
```

Conferências rápidas:

```bash
pnpm exec prisma migrate status
pnpm exec prisma migrate diff --from-config-datasource --to-schema prisma/schema --script
# a segunda deve responder "-- This is an empty migration."
```

No Prisma 7, a conexão vem do `prisma.config.ts` (não do `schema.prisma`), o cliente é gerado
numa pasta do próprio projeto e importado de lá, e o banco é acessado por um adaptador de driver
(`@prisma/adapter-pg`). Siga a documentação da versão fixada no projeto, não exemplos antigos.

## Produção

- `prisma migrate deploy` é o único comando de migração na produção (nunca `migrate dev`).
- Rode a migração depois do backup e antes de trocar o app; se o app novo falhar, o anterior
  precisa funcionar com o banco já migrado (por isso migração aditiva).
- Fixe a versão maior do Prisma no projeto e só troque de versão maior num PR próprio.

## O que um agente de IA NUNCA roda sozinho

- `prisma migrate reset`, `db push --force-reset`, `DROP`, `TRUNCATE` ou qualquer comando que
  apaga o banco: peça para a pessoa rodar no terminal dela. (O próprio Prisma recusa o reset
  quando percebe que quem pede é um agente.)
- Editar migração existente para "consertar" um erro: crie uma migração nova.
- Rodar seed, script de dados ou migração apontando para a produção sem a pessoa pedir.
