# Skill: EduPage Helper

Tento skill poskytuje špecializované príkazy a kontext na správu a prezeranie školských údajov z EduPage.

## Inštrukcie

Pri práci s EduPage skriptom dodržiavaj tieto pravidlá:
1. **Virtuálne prostredie:** Vždy spúšťaj skript pomocou `uv run {skillDir}/get_edupage.py`, aby sa zabezpečilo použitie správnych závislostí.
2. **Súkromie:** Nikdy nevypisuj celé heslá do logov, používaj maskovanie.
4. **Formátovanie:** Výstupy formátuj do prehľadných tabuliek alebo zoznamov pre lepšiu čitateľnosť v CLI.
5. **Diagnostika:** Ak zlyhá načítanie rozvrhu, skontroluj `debug_response.txt` a over, či je `userid` správne nastavený pre dané dieťa.

## Dostupné operácie

- **Prehľad dňa:** Spusti `uv run {skillDir}/get_edupage.py` a zhrň najdôležitejšie zmeny (nové známky alebo odpadnuté hodiny).
- **Kontrola rozvrhu na konkrétny deň:** Spusti `uv run {skillDir}/get_edupage.py --date DD.MM.YYYY` na zobrazenie rozvrhu pre konkrétny dátum.
- **Kontrola známok:** Zameraj sa na posledné záznamy a upozorni na prípadné zhoršenie alebo dôležité písomky.
- **Konfigurácia:** Pre správnu funkčnosť nastav premenné `USERNAME`, `PASSWORD` a `SUBDOMAINS` v systéme OpenClaw (alebo cez `.env` pre lokálny vývoj).
- **Správa .env:** Ak nepoužívaš OpenClaw konfiguráciu, pomôž používateľovi aktualizovať .env súbor pri zmene údajov.

## Príklady promptov

- "Pozri sa, čo majú deti dnes v škole."
- "Aký rozvrh majú deti tento piatok (20.02.2026)?"
- "Máme nejaké nové známky?"
- "Skontroluj školské oznamy."
