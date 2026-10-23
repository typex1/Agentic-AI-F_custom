# Wann lohnt sich ein KI-Agent für einen Geschäftsvorfall?

Natürlichsprachliche Eingabe ist ein guter Hinweis, aber eher ein Symptom als das eigentliche Kriterium. Dahinter steckt: der Vorfall ist nicht sauber strukturiert und lässt sich nicht vorab in ein Formular pressen.

## Vier Stufen der Automatisierung

| Stufe | Beschreibung | Beispiel |
|-------|--------------|----------|
| 0. Rein regelbasiert, keine KI | Strukturierte Eingaben, feste Regeln, deterministisches Ergebnis | Rechnung freigeben, wenn Betrag unter Limit und Bestellnummer vorhanden |
| 1. Einzelner LLM-Aufruf | Ein Schritt, kein Ablauf | Klassifizieren, Extrahieren, Zusammenfassen |
| 2. Fester Workflow mit LLM-Schritten | Reihenfolge der Schritte steht fest, einzelne Schritte brauchen Sprachverständnis | Eingang prüfen → Felder extrahieren → Ticket anlegen → Antwort entwerfen |
| 3. Agent | Das Modell entscheidet selbst, welche Schritte, in welcher Reihenfolge und wie oft | Reklamation mit Rückfragen, Recherche, Fehlersuche |

Ein Agent lohnt sich erst auf Stufe 3. Immer mit der einfachsten Stufe anfangen, die den Fall löst. Oft ist das Stufe 0.

## Stufe 0: Wann gar keine KI nötig ist

Viele Geschäftsvorfälle brauchen kein Sprachmodell. Eine regelbasierte Lösung (Workflow-Engine, Skript, klassische Software, RPA) ist die richtige Wahl, wenn:

- **Die Eingaben strukturiert sind.** Formularfelder, Datenbankeinträge, API-Payloads, klar definierte Dateiformate.
- **Die Entscheidungslogik vollständig als Regeln formulierbar ist.** Wenn-dann-Bedingungen, Schwellwerte, Lookup-Tabellen, Zuständigkeitsmatrizen.
- **Jeder Fall gleich behandelt werden muss.** Gleiche Eingabe, gleiches Ergebnis, immer. Kein Interpretationsspielraum erlaubt.
- **Nachvollziehbarkeit Pflicht ist.** Buchhaltung, Steuern, Fristen, Zugriffsrechte, regulierte Prozesse.
- **Exaktheit zählt.** Berechnungen, Abgleiche, Validierungen. Ein Sprachmodell rundet, rät oder übersieht; Code tut das nicht.
- **Volumen hoch und Latenz kritisch ist.** Regeln laufen in Millisekunden und kosten praktisch nichts.

Typische Beispiele: Rechnungsfreigabe nach Betragsgrenze, Mahnlauf, Dublettenprüfung per Schlüssel, Routing nach Postleitzahl, Berechtigungsvergabe nach Rolle, Stammdatenvalidierung.

Warnsignal für einen überflüssigen KI-Einsatz: Die KI soll etwas tun, was ein Mitarbeiter nach einer Woche Einarbeitung fehlerfrei und ohne Nachdenken erledigt. Das ist eine Regel, kein Urteil.

## Kriterien, die für einen Agenten sprechen

- **Der Lösungsweg steht vorher nicht fest.** Erst nach Schritt 1 weiß man, was Schritt 2 ist. Typisch für Recherche, Triage, Fehlersuche, Reklamationen mit Rückfragen.
- **Viele Verzweigungen und Sonderfälle.** Wenn die Regelmenge eines klassischen Workflows explodiert, weil jeder dritte Fall anders ist, ist der Agent billiger als die Regelpflege.
- **Urteilsvermögen statt harter Regeln.** Plausibilität prüfen, priorisieren, zwischen ähnlichen Kategorien abwägen, Widersprüche in Dokumenten erkennen.
- **Mehrere Quellen und Systeme müssen kombiniert werden.** CRM nachschlagen, Richtlinie lesen, Ticket anlegen, E-Mail formulieren. Der Agent orchestriert die Tools, statt dass ein Mensch zwischen Fenstern wechselt.
- **Unvollständige Eingaben.** Der Agent muss selbst nachfragen oder nachrecherchieren.
- **Unstrukturierte Eingaben jeder Art.** Nicht nur Freitext, auch E-Mails mit PDF-Anhang, Scans, Chatverläufe.
- **Das Ergebnis ist selbst Text oder ein Entwurf.** Antwortschreiben, Zusammenfassung, Empfehlung, nicht nur ein Datensatz.
- **Fehler sind erkennbar und korrigierbar.** Idealerweise gibt ein Mensch am Ende frei. Agenten sind nicht deterministisch; der Prozess muss das aushalten.
- **Genug Volumen oder genug Zeit pro Fall.** Aufbau, Tests und Betrieb müssen sich rechnen.

## Gegenindikatoren für einen Agenten

Hier ist eine regelbasierte Lösung, ein fester Workflow oder ein einzelner LLM-Aufruf die bessere Wahl:

- **Der Ablauf ist deterministisch und bekannt.** Ein fester Workflow ist günstiger, schneller und nachvollziehbarer; ohne unstrukturierte Eingaben reicht Stufe 0.
- **Exakte Berechnungen, Buchungen, rechtlich verbindliche Entscheidungen ohne Review.**
- **Strenge Audit- und Compliance-Anforderungen**, bei denen jeder Pfad vorab dokumentiert sein muss.
- **Hohes Volumen bei niedriger Latenz und engem Budget.** Jeder Agentenschritt kostet Tokens und Zeit.

## Faustregel

Beschreib den Vorfall einem Sachbearbeiter.

- Sagt er *"kommt drauf an, ich muss erst mal nachschauen"*, ist das ein Agenten-Kandidat (Stufe 3).
- Zieht er eine Checkliste aus der Schublade und muss dabei Freitext, E-Mails oder Dokumente lesen, ist es ein Workflow mit LLM-Schritten (Stufe 1 oder 2).
- Zieht er eine Checkliste aus der Schublade und alle Angaben stehen bereits in Feldern, ist es eine Regel (Stufe 0). Hier braucht es keine KI.

## Checkliste zur Einordnung

- [ ] Steht die Reihenfolge der Schritte vorab fest?
- [ ] Lassen sich alle Entscheidungen als Regeln formulieren?
- [ ] Sind die Eingaben strukturiert?
- [ ] Ist das Ergebnis ein strukturierter Datensatz?
- [ ] Muss jeder Pfad auditierbar und reproduzierbar sein?

Auswertung:

- **Alle Häkchen gesetzt:** Stufe 0, rein regelbasiert. Keine KI nötig.
- **Die meisten Häkchen gesetzt, aber Eingaben oder Ergebnis unstrukturiert:** Stufe 1 oder 2, fester Ablauf mit LLM-Schritten.
- **Die meisten Kästchen leer:** Stufe 3, ein Agent ist den Aufwand wert.
