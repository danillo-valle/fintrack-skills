---
name: auth-next-better-auth
description: Proteger páginas, Server Actions e rotas de API de um app Next.js 16 (App Router) com o Better Auth - o proxy.ts não é barreira, requireUser em toda entrada, reautenticação para ação sensível, recurso de outra pessoa como 404, destino seguro depois do login, 2FA e passkeys, e os testes que provam. Use ao criar ou alterar uma página, Server Action ou route.ts, ou ao mexer em login, sessão, 2FA, passkey ou cadastro.
---

# Autenticação e acesso no Next.js com o Better Auth

## As camadas (e qual delas é a barreira)

| Camada                     | O que faz                                                    | É barreira? |
| -------------------------- | ------------------------------------------------------------ | ----------- |
| `proxy.ts` (Next 16)       | Sem cookie de sessão → `/entrar?next=...`. Não vai ao banco. | **Não**     |
| `requireUser()`            | Confere a sessão no banco (e o 2FA ligado, se obrigatório)   | **Sim**     |
| `requireRecentAuth(volta)` | Exige login ou reautenticação nos últimos minutos            | **Sim**     |
| Crachá de acesso           | Confere que ESTA pessoa pode fazer ESTA ação NESTE recurso   | **Sim**     |

O `proxy.ts` (o antigo middleware) é conveniência de navegação: o cookie pode ser velho ou forjado,
e o proxy nem roda para toda requisição que importa. Toda decisão de acesso acontece no servidor,
perto do dado.

## Regras

1. **Toda página protegida** começa com `await requireUser()`. Um teste percorre a pasta das rotas
   e reprova a página que esquecer.
2. **Toda Server Action** (`"use server"`) começa com `await requireUser()`. Uma action é um
   endpoint público: qualquer um pode chamá-la com um POST, com ou sem a tela.
3. **Toda rota de API própria** (`route.ts`) confere a sessão (`auth.api.getSession({ headers })`) e
   responde 401 sem ela. Exceções explícitas e poucas: o handler do Better Auth, o health check e
   webhooks (que têm a própria assinatura).
4. **Dados sempre filtrados pela sessão**, nunca por um id do formulário ou da URL sem conferir.
   Recurso de vários donos: uma função de acesso (`requireAccess(sessão, recursoId, ação)`) devolve
   um "crachá" tipado, e as funções do banco só aceitam o crachá. Sem crachá, não compila.
5. **Recurso de outra pessoa = 404**, igual ao de um id que não existe. 403 conta que o recurso
   existe.
6. **Ação sensível** (exportar, excluir, conectar conta externa, trocar e-mail, desligar 2FA):
   `requireRecentAuth("/tela")` na action. Endpoint sensível do próprio Better Auth entra numa lista
   que exige a mesma reautenticação.
7. **Destino depois do login** (`?next=`): só caminho interno, validado (`safeNextPath`): começa com
   uma `/`, não com `//` nem `/\`, sem esquema. Nunca redirecione para uma URL vinda de fora.
8. **Cliente e servidor separados**: componente `"use client"` usa o cliente do Better Auth; nunca
   importe a configuração do servidor, as variáveis de ambiente ou o envio de e-mail num arquivo
   de cliente (`import "server-only"` neles).
9. **Mensagens de erro** passam por um tradutor único. Login errado diz sempre "E-mail ou senha
   incorretos.", sem revelar se o e-mail existe; cadastro também não revela.
10. **Depois de entrar, confirmar o 2FA ou sair**, troque de página com navegação completa
    (`window.location.assign`), não com `router.replace`: no build de produção, rotas pré-carregadas
    antes do login podem ser reaproveitadas depois dele (laço entre login e início).
11. **Formulário de login, 2FA e senha** funciona (ou pelo menos não vaza nada) antes do React
    carregar: `method="post"` declarado, para um clique adiantado não pôr senha, e-mail ou código na
    URL.

## Modelos

```tsx
// Página com id na URL: sessão, depois o crachá; quem não participa vê o 404
export default async function Pagina({ params }: PageProps<"/projetos/[id]">) {
  const session = await requireUser();
  const { id } = await params;
  const grant = await requireAccess(session, id, "view").catch(
    notFoundOnDenied,
  );
  // ...
}
```

```ts
"use server";
// Action sensível: reautenticação recente, depois o crachá
export async function exportar(formData: FormData) {
  const session = await requireRecentAuth("/exportar");
  // ...
}
```

## Endurecimento do Better Auth

- Cadastro fechado (convite ou lista) quando o app não é público; e-mail confirmado antes de entrar.
- 2FA (TOTP) obrigatório quando os dados valem; passkeys como entrada forte. O desafio do 2FA só
  acontece no login por senha: passkey já é forte; login social depende do 2FA da conta de lá.
- Limite de tentativas no armazenamento do banco (não na memória, que zera a cada deploy).
- `trustedOrigins` exato; cookies `Secure`, `HttpOnly`, `SameSite=Lax`.
- Consulta de senha vazada (Have I Been Pwned) no cadastro e na troca, com tempo limite.

## Testes obrigatórios para tela ou action nova

- Toda página entra na lista central: sem sessão vai ao login; com sessão passa no axe e no foco.
- Tela com id na URL: E2E de IDOR (outra pessoa → 404 sem nenhum dado no HTML).
- Action que muda dado de um dono: teste com pessoa de outro dono (NOT_FOUND).
- Action sensível: E2E com a sessão "envelhecida" que confere o desvio para a reautenticação.
