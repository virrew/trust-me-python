# Trust Me Python – instruktioner för agenter

Förslag framtaget 2026-09-13. Dokumentet beskriver ett rekommenderat arbetssätt
för framtida uppgifter; det ger inget mandat att göra ändringar utanför
användarens beställning. Läs `ARCHITECTURE.md` för systemkarta och begränsningar.

## Börja varje uppgift

1. Läs användarens uppdrag och kontrollera `git status --short` samt relevant diff.
   Arbetskopian kan innehålla avsiktliga, ocommittade ändringar och nya filer.
   Återställ, skriv över eller committa inte andras arbete som del av din uppgift.
2. Läs `ARCHITECTURE.md`, berörda funktioner, deras anropare och tester.
   Dokumentationen är en karta; verifiera detaljer mot aktuell kod.
3. Beskriv berörda kontrakt innan en ändring: kolumner, index/tidszon, typer,
   parametrar, signalvillkor och beräkningarnas tidpunkt.
4. Begränsa ändringen till godkänt arbete. Ett granskningsuppdrag innebär inte
   tillstånd att samtidigt rätta upptäckta fel eller göra en bred refaktorering.

## Snabbkarta

- `src/market_data.py`: Yahoo OHLCV, normalisering, reguljär USA-session och
  separat Daily→intraday-mappning.
- `src/trust_me_core.py`: indikatorer, trend, volatilitet, momentum, volym,
  breakout, squeeze, pullback, fyra entrymoduler per riktning, score och slutfilter.
- `src/diagnostics_context.py`: OHLCV plus indikatorer, läge/session och marginaler.
- `src/diagnostics_signals.py`: context plus moduler, score, slutliga signaler,
  blockerare, bitmasker, near misses och väntestreaks.
- `src/diagnostics_analysis.py`: åtta analystabeller från signaldiagnostikens schema.
- `src/parity_test.py`: manuella MU/TradingView-kontroller och indikatorutskrifter.
- `tests/test_core.py`: automatisk syntetisk testsamling.
- `tests/diagnostics_*_test.py`: manuella nätverksberoende program med assertions i `main()`.
- `src/backtest.py`, `src/live_scanner.py`, `tests/test_market_data.py` är tomma.

Systemet saknar order/fills, positionshantering, exits, kapitalrisk, ML och
avkastningsbacktest. Beskriv inte signalfrekvens eller diagnostik som lönsamhet.

## Bevara gränssnitt och strategi

- Håll datahämtning i datalagret, beräkningar i core och aggregerad rapportering
  i analyslagret. Lägg inte nätverk eller rapportutskrift i core.
- OHLCV-kontraktet är `open`, `high`, `low`, `close`, `volume` med DatetimeIndex.
  Series måste aligna. Resampling/mappning kräver tidszonsmedveten intradaydata.
- Ändra inte indexordning, tidszon, kolumnnamn eller maskbitvärden utan att
  uppdatera konsumenter och relevanta tester i samma samordnade ändring.
- Bevara RMA-seed, EMA-inställningar, RSI-initialisering, `ddof=0`, breakoutens
  `shift(1)` och jämförelseoperatorer när uppgiften inte avser att ändra dem.
- Skilj diagnostiska marginaler från strategiändringar. Vid ett ändrat entrykrav
  måste core, motsvarande failvillkor i signals och kravlistor i analysis
  granskas tillsammans.
- Kontrollera duplicerade standardparametrar i context, signals, parity och
  manuella testprogram. Ändra inte bara en kopia av ett avsett gemensamt värde.
- Hantera warm-up/NaN uttryckligen. Att fylla NaN eller skära bort inledande bars
  kan ändra signaler, procentnämnare och eventlängder.

## Kända fallgropar att kontrollera

- `breakout_context` finns två gånger i core. Sista definitionen används.
  Båda returnerade DataFrame vid genomgången; en ändring av bara den första
  får ingen effekt på den exporterade funktionen.
- `trend_regime_context` använder ADX `>` trots docstringens `>=`.
- Diagnostikens `htf_*` beräknas på inputupplösningen. Daily→intraday-mappningen
  används separat i parityprogrammet och är inte kopplad till signalflödet.
- Context tar sessionsmasker, men signals exponerar dem inte och använder därmed
  True som standard. Signals sätter också alla bars till bekräftade.
- Daily-mappningens sista observerade bar behöver inte vara dagens verkliga
  slutbar. Kontrollera dataåtkomst vid barstängning innan intraday/backtest utökas.
- Analyslagrets kolumnberoenden syns inte som importer. Läs dess kravtabeller.
- Tomma opportunity events kan sakna kolumner. Rapportprogrammet antar events.
- Pine-paritet är en ambition och manuella referenser finns; gröna enhetstester
  bevisar inte fullständig paritet eller att marknadsdata är identiska.

## Verifiering

Kör från projektroten med befintlig miljö, utan att installera om beroenden i onödan:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

Baslinjen 2026-09-13 är 13 passerande tester. Diagnostikprogrammens `main()`
körs inte av pytest. Använd vid behov följande manuella körningar, som hämtar
Yahoo-data och kräver nätverk:

```sh
.venv/bin/python -m src.parity_test
PYTHONPATH=. .venv/bin/python tests/diagnostics_context_test.py
PYTHONPATH=. .venv/bin/python tests/diagnostics_signals_test.py
PYTHONPATH=. .venv/bin/python tests/diagnostics_analysis_test.py
```

De manuella exemplen använder MU och delvis datumet 2026-08-21. Hårdkodade
förväntningar kan påverkas av rullande historik och leverantörens data.
De ersätter inte deterministiska regressionstester.

För beteendeändringar: verifiera berörda gränsvärden, indexalignment, warm-up,
long/short, tomma resultat och signalernas överensstämmelse med diagnostiken.
Vid nya tidsflöden behövs tester av ofullständiga sessioner och framtidsläckage.
Anpassa testomfattningen till ändringen; rapportera vad som faktiskt körts och
vad som återstår. Ändra inte testförväntningar enbart för att få grönt resultat.

## Samarbete mellan flera agenter

När uppdraget omfattar flera agenter: använd en samordnare och avgränsade
ägare för data, kärna/strategi respektive diagnostik/analys enligt arkitekturkartan.
En fil ska ha en skrivande ägare åt gången. Bestäm ägare för `parity_test.py`
utifrån uppgiften. Dela inte corefilen mellan flera samtidiga strategiförfattare.

Varje delegerad uppgift ska ange mål, tillåtna filer, input/output-kontrakt,
beroenden, verifiering och vad som ska återrapporteras. Schemaspräckande ändringar
samordnas innan konsumenter uppdateras. Samordnaren äger integrationsgranskningen.

## Avsluta uppgiften

- Granska diffen och kontrollera att inga orelaterade filer ändrats.
- Redovisa ändrat beteende, testresultat och faktiska begränsningar.
- Uppdatera arkitekturdokumentet om modulansvar, kontrakt eller dataflöden ändras.
- Bevara användarens befintliga arbete och gör inga extra produktändringar som
  en bieffekt av dokumentation eller felsökning.
