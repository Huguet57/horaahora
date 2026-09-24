# Validació editorial de Jev — 24 de setembre de 2026

Versió preparada: `castells-interest-v8`, model `jev-1.13.0`. Aquesta avaluació acompanya les proves automatitzades de contractes i ingesta; no afirma una exactitud garantida del classificador.

## Mètode

S’han fixat 40 casos de la captura de 500 notícies, incloent encerts i errors ja comentats. Les etiquetes es van fixar abans de provar el canvi: 9 Low, 20 Medium i 11 High. Algunes incorporen feedback explícit de l’usuari; les altres són una aplicació editorial dels criteris i continuen obertes a revisió. És una mostra intencionadament difícil, no representativa de tot el feed.

La comparació inicial manté exactament títol, resum i text públic capturats: v5 encerta 23/40, amb 4 falsos High; la nova procedència amb les definicions anteriors encerta 26/40, amb 3 falsos High. La revisió final de criteris obté 30/40 en una primera passada, amb 1 fals High i 1 High perdut. La variabilitat observada impedeix atribuir cada diferència individual només al prompt.

A continuació s’ha repetit la versió final tres vegades sobre cada entrada original, amb el cos HTTP idèntic verificat pel SHA-256. A part, s’ha executat una passada sobre els 40 casos versionats al repositori, que utilitzen paràfrasis breus del text addicional per poder mantenir exemples llegibles sense copiar articles complets. Els dos conjunts no són entrades equivalents i els resultats no s’han de barrejar.

## Resultats finals

| Conjunt | Crides | Coincidències editorials | Falsos High | High perduts | Errors de Jev |
| --- | ---: | ---: | ---: | ---: | ---: |
| 40 entrades originals, tres repeticions | 120 | 89 | 3 | 1 | 0 |
| 40 casos amb text addicional parafrasejat | 40 | 35 | 1 | 0 | 0 |

En les entrades originals, 32 de les 33 classificacions que esperàvem High ho són; 3 dels 35 High retornats no ho haurien de ser segons aquestes etiquetes. Aquests tres corresponen a la mateixa notícia de la primera actuació dels Xiquets de Flix, que continua com a fals positiu conegut.

Misericòrdia, Euskadi, la nota breu dels guanyadors del Quarts Amunt i «Els Nens fan el 4de8 com a millor castell» són Medium en les tres repeticions. La prèvia del Quarts Amunt amb intents inèdits, la classificació al Concurs amb la millor actuació de Sant Pere i Sant Pau i la defunció de Manel Huguet són High en les tres.

Hi ha variació de nivell en 3 de les 40 entrades originals: la crònica «Domini verd…» alterna Medium/High; els bàsics de set de Sitges i Sarrià i el 3de9f de Montblanc alternen Low/Medium. Tots els hash coincideixen dins de cada repetició. No s’introdueixen reintents ni votacions en producció: es desa una classificació per notícia.

Els altres desacords són sobretot Low/Medium: algunes agendes continuen Medium i alguns resultats, novetats culturals i anuncis d’articles queden Low. No s’han canviat les etiquetes de referència per fer passar el model ni s’hi han afegit excepcions per titular o colla.

Les repeticions del proveïdor poden variar: la [documentació de TypeSafe sobre consistència de Choice](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) també descriu canvis de categoria quan les probabilitats són properes. L’aplicació reutilitza el resultat persistit i no depèn de respostes idèntiques en crides posteriors.

## Resultats de les entrades originals

| Cas | Esperat | v5 inicial | v8, tres repeticions |
| --- | --- | --- | --- |
| [news-006 · Els Castellers de Mallorca intentaran el 3de7.](https://revistacastells.cat/hora-a-hora/dijous-24-11h-els-castellers-de-mallorca-intentaran-el-3de7/) | Medium | Medium | Medium / Medium / Medium |
| [news-010 · Sant Pere i Sant Pau i el Serrallo fan la seva millor actuació per Santa Tecla](https://www.elmoncasteller.cat/sant-pere-i-sant-pau-i-el-serrallo-fan-la-seva-millor-actuacio-per-santa-tecla/) | High | High | High / High / High |
| [news-011 · Primera Santa Tecla de la història sense castells de 7. La Crònica.](https://revistacastells.cat/hora-a-hora/dimecres-23-18h-primera-santa-tecla-de-la-historia-sense-castells-de-7-la-cronica/) | High | High | High / High / High |
| [news-035 · Els Bous de la Bisbal s’adjudiquen el Concurs Quarts Amunt amb una entrada triomfal a la gamma alta de 7](https://www.elmoncasteller.cat/els-bous-de-la-bisbal-sadjudiquen-el-concurs-quarts-amunt-amb-una-entrada-triomfal-a-la-gamma-alta-de-7/) | High | High | High / High / High |
| [news-037 · Els Verds regnen a Tarragona i els Xiquets recuperen el somriure](https://www.elmoncasteller.cat/els-verds-regnen-a-tarragona-i-els-xiquets-recuperen-el-somriure/) | High | High | High / High / High |
| [news-038 · Domini verd, ambició rosada, alegria matalassera i èxit del concurs de la Bisbal.](https://revistacastells.cat/hora-a-hora/diumenge-20-21h-domini-verd-ambicio-rosada-alegria-matalassera-i-exit-del-concurs-de-la-bisbal/) | High | High | Medium / High / High |
| [news-047 · Les tres colles es reivindiquen a la Misericòrdia](https://www.elmoncasteller.cat/les-tres-colles-es-reivindiquen-a-la-misericordia/) | Medium | High | Medium / Medium / Medium |
| [news-048 · La colla d’Euskadi estrena lloc d’assaig.](https://revistacastells.cat/hora-a-hora/diumenge-20-9h-la-colla-deuskadi-estrena-lloc-dassaig/) | Medium | Low | Medium / Medium / Medium |
| [news-056 · Els Bous guanyen el Concurs del Quarts Amunt, on tres colles han fet estrenes.](https://revistacastells.cat/hora-a-hora/dissabte-19-20h-els-bous-guanyen-el-concurs-del-quarts-amunt-on-tres-colles-han-fet-estrenes/) | Medium | Medium | Medium / Medium / Medium |
| [news-062 · Deu actuacions per a avui dissabte.](https://revistacastells.cat/hora-a-hora/dissabte-9-8h-deu-actuacions-per-a-avui-dissabte/) | Low | Medium | Medium / Medium / Medium |
| [news-077 · La Bisbal del Penedès estrena el Concurs de Quarts Amunt](https://www.elmoncasteller.cat/la-bisbal-del-penedes-estrena-el-concurs-de-quarts-amunt/) | High | High | High / High / High |
| [news-095 · La Jove convoca els Premis Agustí Forné a la Comunicació castellera.](https://revistacastells.cat/hora-a-hora/dilluns-14-17h-la-jove-convoca-els-premis-agusti-forne-a-la-comunicacio-castellera/) | Medium | Medium | Low / Low / Low |
| [news-102 · Els èxits del Serrallo i Barcelona marquen la Diada](https://www.elmoncasteller.cat/els-exits-del-serrallo-i-barcelona-marquen-la-diada/) | High | High | High / High / High |
| [news-110 · Els Castellers of Eire fan el seu primer pilar de 4.](https://revistacastells.cat/hora-a-hora/diumenge-13-11h-els-castellers-of-eire-fan-el-seu-primer-pilar-de-4/) | High | High | High / High / High |
| [news-111 · Terrassa, Horta i Hostalets de Pierola centren l’agenda d’avui.](https://revistacastells.cat/hora-a-hora/diumenge-13-8h-terrassa-horta-i-hostalets-de-pierola-centren-lagenda-davui/) | Low | Medium | Low / Low / Low |
| [news-114 · Castellar fa el 3de6s, el primer des de la pandèmia.](https://revistacastells.cat/hora-a-hora/dissabte-12-20-15/) | Medium | Medium | Medium / Medium / Medium |
| [news-116 · Bàsics de 7 de Sitges i Sarrià.](https://revistacastells.cat/hora-a-hora/dissabte-12-19h-basics-de-7-de-sitges-i-sarria/) | Medium | Low | Low / Medium / Low |
| [news-125 · Castells de 7 a Badalona.](https://revistacastells.cat/hora-a-hora/divendres-11-15-30h-castells-de-7-a-badalona/) | Medium | Medium | Low / Low / Low |
| [news-128 · 5de8 dels Castellers de Barcelona.](https://revistacastells.cat/hora-a-hora/divendres-11-13-45h-5de8-dels-castellers-de-barcelona/) | Medium | Medium | Low / Low / Low |
| [news-141 · La diada castellera de la Mercè Històrica commorarà el 25è aniversari del primer 3de9f dels Castellers de Barcelona.](https://revistacastells.cat/hora-a-hora/dijous-10-11h-la-diada-castellera-de-la-merce-historica-commorara-el-25e-aniversari-del-primer-3de9f-dels-castellers-de-barcelona/) | Low | High | Low / Low / Low |
| [news-163 · Els Castellers de Sarrià assagen el 3de8 fins a quints i el 2de7 fins a dosos.](https://revistacastells.cat/hora-a-hora/dilluns-7-15h-els-castellers-de-sarria-assagen-el-3de8-fins-a-quins-i-el-2de7-fins-a-dosos/) | Medium | Low | Medium / Medium / Medium |
| [news-174 · 3de9f dels Xiquets de Valls a Montblanc.](https://revistacastells.cat/hora-a-hora/diumenge-6-14h-3de9f-dels-xiquets-de-valls-a-montblanc/) | Medium | Medium | Medium / Low / Medium |
| [news-194 · Gairebé una vintena de places on veure castells avui dissabte.](https://revistacastells.cat/hora-a-hora/dissabte-5-9h-gairebe-una-vintena-de-places-on-veure-castells-avui-dissabte/) | Low | Medium | Low / Low / Low |
| [news-197 · Els Xiquets de Tarragona celebren el centenari el proper dissabte 12 de setembre.](https://revistacastells.cat/hora-a-hora/divendres-4-15h-els-xiquets-de-tarragona-celebren-el-centenari-el-proper-dissabte-12-de-setembre/) | Low | Medium | Low / Low / Low |
| [news-214 · La nova colla d’Horta s’estrena el 13 de setembre.](https://revistacastells.cat/hora-a-hora/dimecres-2-10h-la-nova-colla-dhorta-sestrena-el-13-de-setembre/) | Medium | Low | Medium / Medium / Medium |
| [news-218 · Anunciat el llistat defintiu del Concurs.](https://revistacastells.cat/hora-a-hora/dimarts-1-14h-anunciat-el-llistat-defintiu-del-concurs/) | Medium | High | Medium / Medium / Medium |
| [news-221 · Nou article: ‘Setembre: exigència o conservadorisme?’.](https://revistacastells.cat/hora-a-hora/dimarts-1-9h-nou-article-setembre-exigencia-o-conservadorisme/) | Medium | Medium | Low / Low / Low |
| [news-246 · La clàssica de 8 torna a ser dels Xicots](https://www.elmoncasteller.cat/la-classica-de-8-torna-a-ser-dels-xicots/) | Medium | Medium | Medium / Medium / Medium |
| [news-280 · Els Castellers de Tortosa estrenen mural.](https://revistacastells.cat/hora-a-hora/dimarts-25-10h-els-castellers-de-tortosa-estrenen-mural/) | Medium | Low | Low / Low / Low |
| [news-314 · Classificació per al Concurs: Sacsejada confirmada de Sant Pere i Sant Pau.](https://revistacastells.cat/hora-a-hora/dijous-20-16h-classificacio-per-al-concurs-sacsejada-confirmada-de-sant-pere-i-sant-pau/) | High | High | High / High / High |
| [news-325 · El Pom de Baix: El fenomen dels Govindes de l’Índia.](https://revistacastells.cat/hora-a-hora/dimecres-19-12h-el-pom-de-baix-el-fenomen-dels-govindes-de-lindia/) | Low | Medium | Low / Low / Low |
| [news-340 · Mor Manel Huguet, ‘Gastby’, emblemàtic component dels Castellers de Vilafranca.](https://revistacastells.cat/hora-a-hora/dimarts-19h-mor-joan-huguet-gastby-emblematic-component-dels-castellers-de-vilafranca/) | High | High | High / High / High |
| [news-373 · La Jove fa proves de 3 i 4de10fm.](https://revistacastells.cat/hora-a-hora/dissabte-8-8h-la-jove-fa-proves-de-3-i-4de10fm/) | Medium | Medium | Medium / Medium / Medium |
| [news-380 · La Vella treu pit pels 25 4de9sf descarregats.](https://revistacastells.cat/hora-a-hora/dijous-6-18h-la-vella-treu-pit-pels-25-4de9sf-descarregats/) | Low | Medium | Medium / Medium / Medium |
| [news-389 · Els Castellers de Sant Vicenç rememoren els seus 100 pilars de 5.](https://revistacastells.cat/hora-a-hora/dimecres-5-18h-els-castellers-de-sant-vicenc-rememoren-els-seus-100-pilars-de-5/) | Low | Medium | Low / Low / Low |
| [news-393 · Els Xiquets de Flix faran la seva primera actuació el 16 d’agost.](https://revistacastells.cat/hora-a-hora/dimecres-5-13h-els-xiquets-de-fliz-faran-la-seva-primera-actuacio-el-16-dagost/) | Medium | Medium | High / High / High |
| [news-414 · Sant Pere i Sant Pau firma la millor actuació de la seva història.](https://revistacastells.cat/hora-a-hora/diumenge-2-20-30h-sant-pere-i-sant-pau-firma-la-millor-actuacio-de-la-seva-historia/) | High | High | High / High / High |
| [news-474 · Els Nens fan el 4de8 com a millor castell.](https://revistacastells.cat/hora-a-hora/diumenge-26-14-45h-els-nens-fan-el-4de8-om-a-millor-castell/) | Medium | High | Medium / Medium / Medium |
| [news-481 · Primers 3de7(c) i 5de6 dels Castellers de Tortosa.](https://revistacastells.cat/hora-a-hora/dissabte-25-22h-primers-3de7c-i-5de6-dels-castellers-de-tortosa-a-la-pineda/) | Medium | Medium | Medium / Medium / Medium |
| [news-499 · Agenda i previsions del cap de setmana.](https://revistacastells.cat/hora-a-hora/divendres-24-8h-agenda-i-previsions-del-cap-de-setmana/) | Low | Medium | Medium / Medium / Medium |

## Reproducció i operació

La mostra mantenible és `tests/fixtures/jev_editorial_cases.json`; l’avaluador és `scripts/evaluate_jev_news.py`. Accepta un fitxer alternatiu amb el mateix esquema i registra versió de criteris, model, hash del conjunt, hash de cada petició, probabilitats, latència i consum. No consulta ni escriu a la base de dades i no envia avisos.

```bash
uv run --env-file .env.jev.local python -m scripts.evaluate_jev_news \
  --output /tmp/jev-evaluation.json --repetitions 3
```

Un codi de sortida 1 indica errors o desacords amb les etiquetes; no s’amaguen com a proves superades. CI executa proves locals de contractes, procedència, migracions i ingesta, sense crides externes a Jev.

Les 160 crides de validació final han tingut una latència mitjana de 1352 ms. Consum retornat per l’API: 3,841,324 tokens d’entrada i 366,240 de sortida. La revisió prèvia de variants va fer 160 crides addicionals.

El [pla de desplegament](jev-notifications-rollout.md) requereix la migració additiva `20260924_07` abans del backend. El canvi no envia avisos retroactius i manté els reintents d’APNs, les omissions definitives de Jev i la revalidació de preferències.
