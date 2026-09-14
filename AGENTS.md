Trust Me Python – instruktioner för agenter

Detta dokument innehåller permanenta arbetsregler för agenter i projektet.
ARCHITECTURE.md beskriver aktuell systemkarta, roadmap, implementerade lager,
kontrakt och kända begränsningar. Auktoritativa filer under reference/ beskriver
strategi- respektive research-semantik.

En uppgiftsprompt behöver därför normalt bara ange vilket lager eller mål agenten
ansvarar för, eventuell särskild scope och vad som uttryckligen är out of scope.
Agenten ska själv läsa detta dokument, ARCHITECTURE.md, relevanta referenser,
implementationer och tester innan ändringar görs.

Börja varje uppgift

Läs användarens uppdrag och kontrollera git status --short, aktuell branch
och relevant diff innan någon ändring görs. Arbetskopian kan innehålla
avsiktliga, ocommittade ändringar och nya filer.

Återställ, skriv över, committa, pusha eller mergea inte andras arbete om
detta inte uttryckligen ingår i uppgiften.

Vid parallellt agentarbete ska varje implementation ha en tydlig filägare och
normalt arbeta i separat branch eller worktree. Samordnaren ansvarar för
integrationen mellan parallella ändringar.

Läs alltid ARCHITECTURE.md och identifiera:

vilket roadmap-lager uppgiften gäller,

vilka lager som redan är implementerade,

vilka input/output-kontrakt som gäller,

kända blockerare och begränsningar.

Läs relevanta auktoritativa filer under reference/, berörda funktioner,
deras anropare och tester. Dokumentationen är en karta; verifiera detaljer mot
aktuell kod.

Beskriv berörda kontrakt innan en ändring: kolumner, index/tidszon, typer,
parametrar, signalvillkor, available_at och beräkningarnas tidpunkt.

Begränsa ändringen till godkänt arbete. Ett granskningsuppdrag innebär inte
tillstånd att samtidigt rätta upptäckta fel eller göra en bred refaktorering.

Bygg inte automatiskt nästa roadmap-lager bara för att det aktuella blir klart.
Om ett senare lager kräver ett kontrakt som saknas ska detta rapporteras som
beroende/blockerare i stället för att agenten hittar på ett implicit kontrakt.

Auktoritativa källor

Använd följande prioritering för semantik:

reference/trust_me_strategy.pine är auktoritativ referens för Trust Me v2.0
Pine-strategiintention, signalregler, entry-/exitregler och Pine-specifika
strategiinställningar som faktiskt uttrycks i filen.

src/trust_me_core.py är den primära Python-implementationen av strategins
beräkningar. Om Python-koden avviker från den auktoritativa Pine-referensen ska
avvikelsen rapporteras; agenten får inte tyst välja en egen tredje definition.

reference/RESEARCH_EXECUTION_CONTRACT.md är auktoritativ källa för Python-
systemets kausala research execution-/backtestsemantik. Denna semantik är
medvetet separat från TradingViews broker-emulator och får inte beskrivas som
TradingView-paritet om detta inte uttryckligen verifierats.

ARCHITECTURE.md är auktoritativ för aktuell systemkarta, roadmap, offentliga
kontrakt och kända begränsningar.

Om användarens uppdrag, ARCHITECTURE.md och en auktoritativ referens motsäger
varandra: stoppa den berörda implementationen, rapportera konflikten och gissa inte.

Snabbkarta

Denna lista beskriver modulansvar, inte projektstatus. Läs alltid ARCHITECTURE.md
för vad som faktiskt är implementerat just nu.

src/market_data.py: Yahoo OHLCV, normalisering, reguljär USA-session och
separat Daily→intraday-mappning.

src/trust_me_core.py: indikatorer, trend, volatilitet, momentum, volym,
breakout, squeeze, pullback, fyra entrymoduler per riktning, score och slutfilter.

src/diagnostics_context.py: OHLCV plus indikatorer, läge/session och marginaler.

src/diagnostics_signals.py: context plus moduler, score, slutliga signaler,
blockerare, bitmasker, near misses och väntestreaks.

src/diagnostics_analysis.py: diagnostiska analystabeller från signalschemat.

src/historical_outcomes.py: retrospektiva outcomes för signaler/opportunities;
observationslager, inte trade-/fill-simulator.

src/backtest.py: deterministisk research-Swing-backtest enligt
reference/RESEARCH_EXECUTION_CONTRACT.md.

src/live_scanner.py: scanner/live-lager; kontrollera aktuell status i
ARCHITECTURE.md innan arbete.

src/parity_test.py: manuella MU/TradingView-kontroller och indikatorutskrifter.

reference/trust_me_strategy.pine: auktoritativ Pine v2.0-referens.

reference/RESEARCH_EXECUTION_CONTRACT.md: auktoritativ research execution-
semantik för Python-backtesten.

tests/: deterministiska regressionstester samt vissa manuella/nätverksberoende
integrations- och parityprogram.

Beskriv aldrig signalfrekvens eller diagnostik som lönsamhet. Historical Outcomes,
Research Backtest, Strategy Evaluation och framtida ML-lager har olika ansvar och
ska hållas separerade.

Bevara gränssnitt och strategi

Håll datahämtning i datalagret, beräkningar i core och aggregerad rapportering
i analyslagret. Lägg inte nätverk eller rapportutskrift i core.

OHLCV-kontraktet är open, high, low, close, volume med DatetimeIndex.
Series måste aligna. Resampling/mappning kräver tidszonsmedveten intradaydata.

Ändra inte indexordning, tidszon, kolumnnamn eller maskbitvärden utan att
uppdatera konsumenter och relevanta tester i samma samordnade ändring.

Publika DataFrames från diagnostics-, outcomes-, backtest- och analyslager ska
behålla dokumenterat schema även när resultatet innehåller noll rader.
Returnera inte en kolumnlös DataFrame om konsumenterna förväntar sig ett
definierat schema.

Bevara RMA-seed, EMA-inställningar, RSI-initialisering, ddof=0, breakoutens
shift(1) och jämförelseoperatorer när uppgiften inte avser att ändra dem.

Skilj diagnostiska marginaler från strategiändringar. Vid ett ändrat entrykrav
måste core, motsvarande failvillkor i signals och kravlistor i analysis granskas
tillsammans.

diagnostics_signals.py och diagnostics_analysis.py får spegla strategilogik
för förklaring och analys men får inte introducera en alternativ definition av
vad som aktiverar strategin.

Duplicerad strategi-semantik är befintlig teknisk skuld och ska inte utökas.
Nya entrykrav ska inte implementeras som ytterligare oberoende kopior på flera
ställen om ett gemensamt kontrakt eller återanvändbar representation rimligen
kan användas.

Kontrollera duplicerade standardparametrar i context, signals, parity och
manuella testprogram. Ändra inte bara en kopia av ett avsett gemensamt värde.

Hantera warm-up/NaN uttryckligen. Att fylla NaN eller skära bort inledande bars
kan ändra signaler, procentnämnare och eventlängder.

Research-, backtest- och ML-principer

Projektets mål är att analysera Trust Me-strategin, förstå vilka regler som
hjälper eller blockerar trades och senare utvärdera förändringar utan lookahead
eller otydliga execution-antaganden.

Därför gäller:

Python-systemets research-/backtestlager ska vara kausalt, deterministiskt,
reproducerbart och dokumenterat.

Pine Strategy Semantics och Research Execution Semantics är separata kontrakt.
Pine definierar strategiintention; research-kontraktet definierar hur Python
simulerar trades för analys.

TradingView broker-emulator-paritet får inte antas eller påstås om den inte
uttryckligen verifierats.

Historical Outcomes är ett retrospektivt observationslager och ska inte
blandas ihop med fills, PnL eller trade execution.

Backtestresultat ska inte automatiskt tolkas som robust strategi-edge. Senare
Strategy Evaluation, A/B-testing och out-of-sample/walk-forward måste skilja
hypotesgenerering från verifiering.

ML-lager får aldrig använda framtida outcomes, labels eller ännu ej tillgängliga
HTF-/barvärden som features vid beslutstidpunkten.

Ingen agent får optimera parametrar, ändra strategiregler eller välja den bästa
varianten utifrån samma data utan att uppgiften uttryckligen gäller detta och
arkitekturen anger hur överanpassning ska kontrolleras.

Temporal causality / no lookahead

Bevara tidsmässig kausalitet. Varje feature, signal, label, HTF-värde, exit och
framtida ML-input måste endast använda information som faktiskt var tillgänglig
vid beslutstidpunkten.

Vid nya tidsberoende flöden ska agenten uttryckligen dokumentera när värdet blir
tillgängligt, exempelvis available_at = bar close, next bar open eller
motsvarande.

En bar får inte använda information från sin egen framtid eller från ännu ej
avslutade högre tidsupplösningar.

Forward fill, Daily→intraday-mappning, resampling, labels, outcomes, trailing
stops och framtida ML-features ska granskas särskilt för lookahead leakage.

Kända fallgropar att kontrollera

Dessa punkter är historiskt kända riskområden. Verifiera alltid aktuell kod och
ARCHITECTURE.md; anta inte att en punkt fortfarande är oförändrad.

breakout_context har historiskt funnits dubblerad i core. Kontrollera vilken
definition som faktiskt exporteras innan ändring.

trend_regime_context har historiskt använt ADX > trots äldre docstring med
>=.

Diagnostikens htf_* har historiskt beräknats på inputupplösningen medan
Daily→intraday-mappning varit separat. Kontrollera aktuell wiring.

Context har historiskt tagit sessionsmasker medan signals inte alltid exponerat
dem; kontrollera aktuell implementation före session-/Intraday-arbete.

Daily-mappningens sista observerade bar behöver inte vara dagens verkliga
slutbar. Kontrollera dataåtkomst vid barstängning innan intraday/backtest utökas.

Analyslagrets kolumnberoenden syns inte alltid som importer. Läs dess
kravtabeller och tester.

Tomma opportunity events kan kräva explicit stabilt schema.

Gröna unit tests bevisar inte Yahoo-integration, TradingView-paritet eller
robust lönsamhet.

Klassificera ändringen

Varje implementation ska klassificeras som:

Behavior change: NO

Behavior change: YES

Behavior change: YES gäller bland annat om ändringen påverkar:

strategi- eller entryvillkor

jämförelseoperatorer och gränsvärden

indikatorberäkningar eller warm-up

NaN-hantering

tidsstämpling eller index

sessioner eller resampling

HTF-tillgänglighet

signal-, score- eller masklogik

eventdefinitioner

order-/fill-tid

exitlogik

positionsstorlek eller risk

kostnadsmodell

research execution-kontrakt

labels eller ML-features

En refaktorering får endast klassificeras som Behavior change: NO om den
bevarar observerbart beteende och detta stöds av relevanta tester.

Ändra aldrig förväntade testvärden enbart för att få en beteendeändring att
framstå som oförändrad.

Rapportera dessutom separat om Trust Me-strategins regler ändrats:

Existing strategy behavior changed: YES/NO

Ett nytt research-, analys- eller ML-lager kan alltså vara Behavior change: YES
samtidigt som Existing strategy behavior changed: NO.

Verifiering

Anta aldrig ett hårdkodat antal passerande tester från detta dokument.
Varje agent ska mäta aktuell baseline före implementation.

Kör från projektroten med befintlig miljö och installera inte om beroenden i
onödan.

Föredragen ordning:

# macOS / Linux med projektets .venv:
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider

# Windows med projektets .venv:
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider

# Cloud eller miljö utan projektets .venv:
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider

Agenten ska:

köra och rapportera faktisk baseline före ändringar,

köra riktade tester för den berörda modulen,

köra hela deterministiska testsuiten efter ändringen,

köra git diff --check,

köra py_compile på ändrade Python-filer när relevant.

Om baseline inte är grön ska agenten identifiera om felet är relaterat till
uppgiften. Orelaterade fel får inte tyst repareras, döljas eller användas som
ursäkt för scope creep.

Manuella integration-/paritykörningar kan användas när uppgiften kräver dem,
exempelvis:

.venv/bin/python -m src.parity_test
PYTHONPATH=. .venv/bin/python tests/diagnostics_context_test.py
PYTHONPATH=. .venv/bin/python tests/diagnostics_signals_test.py
PYTHONPATH=. .venv/bin/python tests/diagnostics_analysis_test.py

De kan kräva nätverk och externa data och ersätter inte deterministiska
regressionstester.

Redovisa verifiering separat enligt:

Unit / regression

Integration

Parity / reference

Skriv inte enbart "alla tester passerar". Ange kommandon, exakta resultat och
vilka relevanta nivåer som inte kördes.

För beteendeändringar: verifiera berörda gränsvärden, indexalignment, warm-up,
long/short, tomma resultat, tidskausalitet och signalernas överensstämmelse med
relevanta kontrakt. Ändra inte testförväntningar enbart för att få grönt resultat.

Samarbete mellan flera agenter

När uppdraget omfattar flera agenter: använd en samordnare och avgränsade ägare.
En fil ska ha en skrivande ägare åt gången. Dela inte corefilen mellan flera
samtidiga strategiförfattare.

Varje delegerad uppgift ska minst ange:

mål / roadmap-lager,

tillåtna eller huvudsakliga filer om detta behöver begränsas,

särskild scope/out of scope som inte redan framgår av arkitekturen,

eventuella nya kontrakt som uttryckligen ska skapas.

Övriga standardkrav — kontraktsgranskning, temporal causality, verifiering,
slutrapport och scope-disciplin — följer automatiskt av denna AGENTS.md och
behöver normalt inte upprepas i varje prompt.

Avsluta uppgiften

Granska diffen och kontrollera att inga orelaterade filer ändrats.

Uppdatera ARCHITECTURE.md om modulansvar, roadmap, kontrakt eller dataflöden
ändras.

Uppdatera relevant fil under reference/ endast när uppgiften uttryckligen
ändrar ett auktoritativt kontrakt.

Bevara användarens befintliga arbete och gör inga extra produktändringar som
bieffekt av dokumentation eller felsökning.

Slutrapporten ska minst innehålla:

Behavior change: YES/NO

Existing strategy behavior changed: YES/NO

filer tillagda

filer modifierade

vad som ändrades

berörda kontrakt

baseline-testresultat

riktade tester och resultat

full deterministisk testsuite och resultat

relevanta Integration-/Parity-tester som kördes eller inte kördes

kvarvarande risker, begränsningar och blockerare

Rapportera inte större säkerhet än verifieringen stödjer. Gröna unit tests innebär
exempelvis inte automatiskt verifierad Yahoo-integration, Pine/TradingView-paritet,
robust lönsamhet eller out-of-sample-generaliserbarhet.