# Roblox Limiteds Explorer

Aplicativo de desktop para Windows que consulta itens **limiteds** do Roblox: valor, RAP, cópias,
histórico de preço, textura, favoritos com alertas, comparador e calculadora de lucro.

![Screenshot do app](docs/screenshot.png)

> Projeto não oficial. Não tem ligação com a Roblox Corporation nem com a Rolimons.
> "Roblox" é marca registrada da Roblox Corporation.

## Funcionalidades

- **Busca por ID ou nome**, com sugestões enquanto você digita
- **Detalhes do item:** criador, datas, tipo, preço original, se é Limited ou Limited U
- **Valores:** Value, RAP, tendência, demanda e marcações (projetado, hyped, raro) da Rolimons
- **Cópias e vendas:** total de cópias, vendas registradas e menor preço de revenda
- **Histórico de preço** em gráfico, com dados reais do Roblox
- **Donos do item** (com cookie): usuário, ID, UAID, número de série e data, com exportação para CSV
- **Textura/modelo:** baixa a imagem e a textura do item
- **Favoritos** com alertas do Windows quando o RAP ou o menor preço mudam
- **Comparador** de dois itens lado a lado
- **Calculadora de lucro** já descontando a taxa de 30% do Roblox
- Tema claro/escuro, cache local e exportação em JSON

## Instalação

Requer **Python 3.11 ou mais novo** ([python.org](https://www.python.org/downloads/), marque *Add to PATH*).

```bash
git clone https://github.com/SEU-USUARIO/roblox-limiteds-explorer.git
cd roblox-limiteds-explorer
```

**Jeito fácil (Windows):** dê dois cliques em `instalar_e_rodar.bat`.

**Jeito manual:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Gerar o .exe

Dê dois cliques em `gerar_exe.bat`, ou rode:

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name RobloxLimitedsExplorer ^
  --collect-all customtkinter ^
  --hidden-import plyer.platforms.win.notification ^
  --hidden-import keyring.backends.Windows ^
  main.py
```

O programa fica em `dist\RobloxLimitedsExplorer\RobloxLimitedsExplorer.exe`.
Para distribuir, compacte a **pasta inteira** `RobloxLimitedsExplorer`, não só o `.exe`.

## Estrutura

```
main.py                 ponto de entrada
core/
  api.py                chamadas Roblox + Rolimons (retry, rate limit, cache)
  assets.py             download de textura/modelo
  cache.py              cache em memória com gravação lenta em disco
  config.py             configurações, favoritos e cookie
  report.py             monta os campos e o texto de um item
  utils.py              formatação, CSV/JSON, notificação, calculadora
  watcher.py            alertas em segundo plano
ui/
  app.py                janela principal e busca
  item_view.py          aba Item
  owners_view.py        aba Donos
  chart_view.py         aba Histórico
  compare_view.py       aba Comparar
  favorites_view.py     aba Favoritos
  calculator_view.py    aba Calculadora
  settings_view.py      aba Configurações
  theme.py              threads seguras, tema da tabela e do gráfico
```

## De onde vêm os dados

| Dado | Fonte |
|---|---|
| Detalhes, datas, Limited/Limited U | `economy.roblox.com` |
| Total de cópias, vendas, histórico de preço | `economy.roblox.com` (resale-data) |
| Menor preço de revenda | `catalog.roblox.com` |
| Imagem do item | `thumbnails.roblox.com` |
| Value, RAP, tendência, demanda | `rolimons.com/itemapi` |
| Donos do item | `inventory.roblox.com` (exige cookie) |

## Cookie `.ROBLOSECURITY` (opcional)

Só é necessário para listar donos e para baixar alguns assets protegidos.
**Quem tem esse cookie controla a conta.** Por isso:

- nunca compartilhe, nem em issues, prints ou commits;
- prefira usar uma conta alternativa;
- o app guarda o cookie no Gerenciador de Credenciais do Windows (ou em
  `%APPDATA%\RobloxLimitedsExplorer\config.json` se o cofre não estiver disponível),
  nunca dentro da pasta do projeto, e só o envia para o Roblox.

## Limitações

Estas limitações vêm das APIs do Roblox e da Rolimons, não do app:

- **Donos:** o Roblox só libera a lista em alguns casos (ex.: itens que a conta criou ou possui).
  Pode retornar 403 mesmo com cookie válido.
- **Total de donos** não existe na API pública. O app mostra quantos foram carregados.
- **Data em que virou limited** não é informada. O app mostra a data do primeiro registro de
  revenda, que é uma aproximação.
- **Textura:** camisas e calças funcionam bem. Acessórios usam formato binário comprimido,
  então nem sempre dá para extrair a textura.
- As APIs não são oficiais e podem mudar sem aviso. Se algo parar de funcionar, abra uma issue.

## Solução de problemas

Erros inesperados são gravados em `%APPDATA%\RobloxLimitedsExplorer\error.log`.
Ao abrir uma issue, anexe esse arquivo (confira antes se não há nenhum dado pessoal).

## Contribuindo

Pull requests são bem-vindos. Abra uma issue descrevendo a mudança antes de grandes alterações.

## Licença

[MIT](LICENSE)
# Roblox Limiteds Explorer

Aplicativo de desktop para Windows que consulta itens **limiteds** do Roblox: valor, RAP, cópias,
histórico de preço, textura, favoritos com alertas, comparador e calculadora de lucro.

![Screenshot do app](docs/screenshot.png)

> Projeto não oficial. Não tem ligação com a Roblox Corporation nem com a Rolimons.
> "Roblox" é marca registrada da Roblox Corporation.

## Funcionalidades

- **Busca por ID ou nome**, com sugestões enquanto você digita
- **Detalhes do item:** criador, datas, tipo, preço original, se é Limited ou Limited U
- **Valores:** Value, RAP, tendência, demanda e marcações (projetado, hyped, raro) da Rolimons
- **Cópias e vendas:** total de cópias, vendas registradas e menor preço de revenda
- **Histórico de preço** em gráfico, com dados reais do Roblox
- **Donos do item** (com cookie): usuário, ID, UAID, número de série e data, com exportação para CSV
- **Textura/modelo:** baixa a imagem e a textura do item
- **Favoritos** com alertas do Windows quando o RAP ou o menor preço mudam
- **Comparador** de dois itens lado a lado
- **Calculadora de lucro** já descontando a taxa de 30% do Roblox
- Tema claro/escuro, cache local e exportação em JSON

## Instalação

Requer **Python 3.11 ou mais novo** ([python.org](https://www.python.org/downloads/), marque *Add to PATH*).

```bash
git clone https://github.com/SEU-USUARIO/roblox-limiteds-explorer.git
cd roblox-limiteds-explorer
```

**Jeito fácil (Windows):** dê dois cliques em `instalar_e_rodar.bat`.

**Jeito manual:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Gerar o .exe

Dê dois cliques em `gerar_exe.bat`, ou rode:

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name RobloxLimitedsExplorer ^
  --collect-all customtkinter ^
  --hidden-import plyer.platforms.win.notification ^
  --hidden-import keyring.backends.Windows ^
  main.py
```

O programa fica em `dist\RobloxLimitedsExplorer\RobloxLimitedsExplorer.exe`.
Para distribuir, compacte a **pasta inteira** `RobloxLimitedsExplorer`, não só o `.exe`.

## Estrutura

```
main.py                 ponto de entrada
core/
  api.py                chamadas Roblox + Rolimons (retry, rate limit, cache)
  assets.py             download de textura/modelo
  cache.py              cache em memória com gravação lenta em disco
  config.py             configurações, favoritos e cookie
  report.py             monta os campos e o texto de um item
  utils.py              formatação, CSV/JSON, notificação, calculadora
  watcher.py            alertas em segundo plano
ui/
  app.py                janela principal e busca
  item_view.py          aba Item
  owners_view.py        aba Donos
  chart_view.py         aba Histórico
  compare_view.py       aba Comparar
  favorites_view.py     aba Favoritos
  calculator_view.py    aba Calculadora
  settings_view.py      aba Configurações
  theme.py              threads seguras, tema da tabela e do gráfico
```

## De onde vêm os dados

| Dado | Fonte |
|---|---|
| Detalhes, datas, Limited/Limited U | `economy.roblox.com` |
| Total de cópias, vendas, histórico de preço | `economy.roblox.com` (resale-data) |
| Menor preço de revenda | `catalog.roblox.com` |
| Imagem do item | `thumbnails.roblox.com` |
| Value, RAP, tendência, demanda | `rolimons.com/itemapi` |
| Donos do item | `inventory.roblox.com` (exige cookie) |

## Cookie `.ROBLOSECURITY` (opcional)

Só é necessário para listar donos e para baixar alguns assets protegidos.
**Quem tem esse cookie controla a conta.** Por isso:

- nunca compartilhe, nem em issues, prints ou commits;
- prefira usar uma conta alternativa;
- o app guarda o cookie no Gerenciador de Credenciais do Windows (ou em
  `%APPDATA%\RobloxLimitedsExplorer\config.json` se o cofre não estiver disponível),
  nunca dentro da pasta do projeto, e só o envia para o Roblox.

## Limitações

Estas limitações vêm das APIs do Roblox e da Rolimons, não do app:

- **Donos:** o Roblox só libera a lista em alguns casos (ex.: itens que a conta criou ou possui).
  Pode retornar 403 mesmo com cookie válido.
- **Total de donos** não existe na API pública. O app mostra quantos foram carregados.
- **Data em que virou limited** não é informada. O app mostra a data do primeiro registro de
  revenda, que é uma aproximação.
- **Textura:** camisas e calças funcionam bem. Acessórios usam formato binário comprimido,
  então nem sempre dá para extrair a textura.
- As APIs não são oficiais e podem mudar sem aviso. Se algo parar de funcionar, abra uma issue.

## Solução de problemas

Erros inesperados são gravados em `%APPDATA%\RobloxLimitedsExplorer\error.log`.
Ao abrir uma issue, anexe esse arquivo (confira antes se não há nenhum dado pessoal).

## Contribuindo

Pull requests são bem-vindos. Abra uma issue descrevendo a mudança antes de grandes alterações.

## Licença

[MIT](LICENSE)
