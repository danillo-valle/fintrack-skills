#!/usr/bin/env python3
"""Confere as skills antes de cada PR (roda no CI e na sua máquina):

    python3 scripts/validar.py

- cada pasta de skills/ tem um SKILL.md com o cabeçalho (frontmatter) certo: name igual ao nome
  da pasta (minúsculas, números e hífens, até 64 caracteres) e description de até 1024
  caracteres, sem os sinais < e >;
- os manifestos do plugin e do marketplace são JSON válido, com a mesma versão no README;
- nenhum texto das skills fala do projeto de onde elas vieram (a lista PROIBIDO): as skills são
  genéricas, e o que é de um projeto fica no repositório dele;
- nenhum caminho de máquina (/home/..., C:\\...) nem nada com cara de segredo.

Sai com 1 e a lista do que falhou.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# O projeto de origem e o que só existe nele: nada disso pode aparecer numa skill
PROIBIDO = re.compile(
    r"fintrack|pluggy|whatsapp|telegram|carteira|\blar\b|wallet|household|danillo"
    r"|\bM\d{2}(\.\d)?\b|ADR-\d{3}|/srv/|N150",
    re.IGNORECASE,
)
MAQUINA = re.compile(r"/home/\w|/root/|/Users/\w|[A-Z]:\\\\")
SEGREDO = re.compile(
    r"AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{36}|github_pat_\w{20,}|sk-[A-Za-z0-9]{20,}"
    r"|AGE-SECRET-KEY-1|hc-ping\.com/[0-9a-f]{8}-|-----BEGIN [A-Z ]*PRIVATE KEY"
)

erros: list[str] = []


def frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
if not skills:
    erros.append("skills/: nenhuma skill")
for folder in skills:
    md = folder / "SKILL.md"
    if not md.is_file():
        erros.append(f"{folder.name}: falta o SKILL.md")
        continue
    text = md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        erros.append(f"{folder.name}: SKILL.md sem o cabeçalho entre linhas ---")
        continue
    name, desc = fm.get("name", ""), fm.get("description", "")
    if name != folder.name:
        erros.append(f"{folder.name}: name '{name}' diferente do nome da pasta")
    if not NAME.match(name) or len(name) > 64:
        erros.append(f"{folder.name}: name fora do formato (minúsculas, números e hífens, até 64)")
    if not desc or len(desc) > 1024 or "<" in desc or ">" in desc:
        erros.append(f"{folder.name}: description vazia, com mais de 1024 caracteres ou com < >")
    if len(text.splitlines()) > 500:
        erros.append(f"{folder.name}: SKILL.md com mais de 500 linhas (divida em arquivos de referência)")

for path in sorted((ROOT / "skills").rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT)
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for regex, what in ((PROIBIDO, "fala do projeto de origem"), (MAQUINA, "caminho de máquina"),
                            (SEGREDO, "parece um segredo")):
            if (m := regex.search(line)):
                erros.append(f"{rel}:{n}: {what} ({m.group(0)!r})")

versions = {}
for manifest in ("plugin.json", "marketplace.json"):
    try:
        data = json.loads((ROOT / ".claude-plugin" / manifest).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        erros.append(f".claude-plugin/{manifest}: {exc}")
        continue
    if manifest == "plugin.json":
        versions["plugin"] = data.get("version")
    else:
        names = [p.get("name") for p in data.get("plugins", [])]
        if names != ["fintrack-skills"]:
            erros.append(".claude-plugin/marketplace.json: a lista de plugins mudou sem o validador saber")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
if versions.get("plugin") and f"v{versions['plugin']}" not in readme:
    erros.append(f"README.md: não cita a versão v{versions['plugin']} do plugin.json")
for folder in skills:
    if f"skills/{folder.name}/" not in readme:
        erros.append(f"README.md: a skill {folder.name} não está na lista")

if erros:
    print("validar: falhou", *erros, sep="\n  ")
    sys.exit(1)
print(f"validar: {len(skills)} skills certas")
