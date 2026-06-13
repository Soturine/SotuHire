# RSS, Atom e URL Pública Manual

## URL de vaga

O conector manual baixa uma URL pública, extrai texto visível, detecta título, empresa, local, modalidade, senioridade, contrato, salário, skills e benefícios, e cria uma oportunidade revisável.

## Listagens e páginas de carreira

Os conectores de listagem genérica e página de carreira identificam links prováveis de vagas. Isso permite compatibilidade inicial com boards HTML simples, páginas de empresas e formatos semelhantes a Greenhouse ou Lever.

## RSS e Atom

O conector XML lê `item` ou `entry`, extrai título, link e descrição e normaliza cada item. O limite por coleta vem de `ScrapingSource.max_items`.

## Fontes configuradas

Copie e edite:

```bash
cp config/sources.example.toml config/sources.toml
```

O arquivo local não é versionado. Cada fonte pode definir tipo, URL, ativação, limite e intervalo.

## Responsabilidade

Todos os conectores verificam acesso público e `robots.txt`, usam cache e rate limit e retornam falhas sem quebrar a interface. Autenticação automatizada e bypass de bloqueios não são suportados.
