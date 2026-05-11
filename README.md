# Kramerius Screener – Jak spustit

## Co potřebuješ
- **Google Chrome**
- **Python 3.10+**
- Přístup do [digitalniknihovna.cz](https://www.digitalniknihovna.cz)

### Instalace Pythonu
- **Mac**: `brew install python@3.11` nebo stáhni z [python.org](https://python.org/downloads)
- **Windows**: Stáhni z [python.org](https://python.org/downloads) – při instalaci zaškrtni **"Add Python to PATH"**
- **Linux**: `sudo apt install python3`

---

## Spuštění

### Mac / Linux
```bash
cd cesta/k/v0.10
chmod +x spustit.sh
./spustit.sh
```

### Windows
Dvojklik na `spustit.bat`

Automaticky se otevře **Google Chrome** na adrese `localhost:7432`.

---

## První spuštění – přihlášení

Klikni na **Přihlásit se do knihovny** vpravo nahoře → přihlas se svým účtem (např. univerzitním) → po přihlášení okno zavři. Program si přihlášení zapamatuje pro příště.

---

## Použití

1. Zkopíruj URL knihy z digitalniknihovna.cz do pole **URL knih**
2. Volitelně vyber výstupní složku (výchozí je Downloads)
3. Klikni **Spustit**
4. Otevře se okno prohlížeče – nech ho běžet na pozadí, nezavírej ho
5. Po dokončení se okno samo zavře a PDF se uloží do zvolené složky

---

## Tipy

- Více knih najednou? Každou URL na nový řádek
- Zkontroluj výsledné PDF – pokud se stránka načítala pomalu, mohlo se vyfotit načítací kolečko místo obsahu
- **Test režim** – zaškrtni před spuštěním, stáhne jen 2 stránky z každé knihy

---

*Projekt vznikl z frustrace při psaní 2 seminárních prací s obskurní tematikou na poslední chvíli.*
