#!/usr/bin/env python3
"""
# Knowledge Base Agent – Deutsche Version

Dieses Beispiel zeigt einen Strands-Agenten, der Fragen aus einer
Amazon-Bedrock-Wissensdatenbank beantwortet. Die Wissensdatenbank enthält
deutschsprachige Dokumente zu Unternehmens-Compliance und Nachhaltigkeit
(ISO-Zertifizierungen, Umweltziele, Informationssicherheit).

Ein kleiner Klassifikations-Agent bestimmt zuerst die Absicht des Nutzers:
- RETRIEVE: Relevante KB-Inhalte werden automatisch über den MemoryManager
  in den Modellinput eingebettet, und der Agent antwortet daraus in einem Aufruf.
- STORE: Der Agent erklärt, dass diese KB nur lesend zugänglich ist (siehe unten);
  es wird nichts geschrieben.

## Anpassungen für diese Umgebung
- Alle Agenten laufen auf amazon.nova-lite-v1:0 (das einzige erlaubte Bedrock-Modell).
- Verwendet die aktuelle Memory-API (MemoryManager + BedrockKnowledgeBaseStore)
  anstelle des veralteten `memory`-Tools. Der Abruf erfolgt über automatische
  Memory-Injektion: Relevante KB-Inhalte werden in den Modellinput eingebettet,
  sodass kein separater Abruf-dann-Zusammenfassung-Schritt (oder `use_llm`-Aufruf)
  nötig ist.
- Die Wissensdatenbank befindet sich in einem anderen AWS-Konto. Der Store erhält
  einen injizierten bedrock-agent-runtime-Client, der aus einem benannten
  Credential-Profil erstellt wird (Standard „xacct", überschreibbar mit
  STRANDS_KB_PROFILE), während Modellinvokationen die eigenen Credentials
  dieser Instanz verwenden.
- `knowledge_base_type` wird explizit gesetzt, da die Cross-Account-Rolle kein
  bedrock:GetKnowledgeBase erlaubt, was der Store sonst zur Erkennung aufrufen würde.
- Der Store-Pfad ist nicht verfügbar: Die Datenquelle der KB ist S3-basiert, und
  Schreiben würde zusätzlich s3:PutObject auf dem Bucket des besitzenden Kontos
  erfordern, was die Cross-Account-Rolle nicht gewährt. Store-Anfragen erhalten
  eine ehrliche Nachricht.

## Voraussetzungen
- ~/.aws/credentials enthält ein Profil (Standardname „xacct") mit
  Cross-Account-Zugriff auf die KB.
- STRANDS_KNOWLEDGE_BASE_ID-Umgebungsvariable (Standard: die Lab-KB unten).

## Beispielabfragen

(Die Lab-KB enthält deutschsprachige Dokumente zu Unternehmens-Compliance
und Nachhaltigkeit.)

- „Welche ISO-Zertifizierungen werden erwähnt?"
- „Was sind die Umweltziele?"
- „Merke dir, dass unser nächstes Audit am 25. Juli ist" (meldet die Nur-Lese-Einschränkung)
"""

import os

import boto3
from strands import Agent
from strands.memory import MemoryManager
from strands.vended_memory_stores.bedrock_knowledge_base import BedrockKnowledgeBaseStore

# Angepasst: Diese Umgebung erlaubt nur das Bedrock-Modell amazon.nova-lite-v1:0.
MODEL_ID = "amazon.nova-lite-v1:0"

# Cross-Account-KB-Konfiguration.
KB_ID = os.environ.get("STRANDS_KNOWLEDGE_BASE_ID", "Y3S3SAL74D")
KB_REGION = os.environ.get("STRANDS_KB_REGION", "us-east-1")
KB_PROFILE = os.environ.get("STRANDS_KB_PROFILE", "xacct")

print(f"Verwende Wissensdatenbank-ID: {KB_ID} (Region {KB_REGION}, Credentials-Profil '{KB_PROFILE}')")

# KB-Aufrufe laufen über das Cross-Account-Profil via injiziertem Client;
# alles andere (Modellinvokation) bleibt auf der Standard-Credential-Chain.
kb_session = boto3.Session(profile_name=KB_PROFILE, region_name=KB_REGION)

knowledge_store = BedrockKnowledgeBaseStore(
    config={
        "knowledge_base_id": KB_ID,
        "knowledge_base_type": "VECTOR",  # GetKnowledgeBase-Erkennung überspringen (Cross-Account nicht erlaubt)
        "data_source_type": "S3",
        "runtime_client": kb_session.client("bedrock-agent-runtime"),
    },
    name="knowledge_base",
    writable=False,  # S3-basierte Datenquelle; keine Schreibrechte über diesen Zugriffspfad
)

# System-Prompt zur Bestimmung der Nutzerabsicht. Store-Anfragen werden weiterhin
# klassifiziert (und dann mit der Nur-Lese-Nachricht unten beantwortet), daher
# decken die Beispiele beide Absichten in der Domäne dieser KB ab:
# Unternehmens-Compliance / Nachhaltigkeitsdokumente.
ACTION_SYSTEM_PROMPT = """
Du bist ein Wissensdatenbank-Assistent, der sich AUSSCHLIEẞLICH auf die Klassifizierung von Nutzeranfragen konzentriert.
Deine Aufgabe ist es festzustellen, ob eine Nutzeranfrage das SPEICHERN von Informationen in einer Wissensdatenbank
oder das ABRUFEN von Informationen aus einer Wissensdatenbank erfordert.

Antworte mit GENAU EINEM WORT – entweder „store" oder „retrieve".
Füge KEINE Erklärungen oder sonstigen Text hinzu.

Beispiele:
- „Welche ISO-Zertifizierungen werden erwähnt?" -> „retrieve"
- „Merke dir, dass unser nächstes Audit am 25. Juli ist" -> „store"
- „Was sind die Umweltziele?" -> „retrieve"
- „Füge eine Notiz hinzu, dass ISO 27001 dieses Jahr verlängert wurde" -> „store"
- „Welche Themen deckt die Informationssicherheitsrichtlinie ab?" -> „retrieve"
- „Speichere das: Der Nachhaltigkeitsbericht ist im 3. Quartal fällig" -> „store"

Antworte nur mit „store" oder „retrieve" – keine Erklärung, kein Präfix, kein sonstiger Text.
"""

ANSWER_SYSTEM_PROMPT = """
Du bist ein hilfreicher Assistent, der Fragen zu Unternehmens-Compliance und
Nachhaltigkeitsdokumenten beantwortet (ISO-Zertifizierungen, Umweltziele,
Informationssicherheitsrichtlinien). Relevante Inhalte aus der Wissensdatenbank
werden automatisch in deinen Kontext eingebettet; stütze deine Antworten darauf.

Deine Antworten sollten:
1. Direkt und auf den Punkt sein
2. Keine Dokument-IDs, Scores oder andere Metadaten erwähnen
3. Gesprächig, aber knapp sein
4. Anerkennen, wenn die eingebetteten Inhalte die Frage nicht abdecken,
   oder wenn Informationen widersprüchlich oder fehlend sind

Antworte immer auf Deutsch.
"""


def determine_action(query):
    """Bestimmt, ob die Anfrage eine Speicher- oder Abrufaktion ist."""
    classifier = Agent(model=MODEL_ID, system_prompt=ACTION_SYSTEM_PROMPT, callback_handler=None)
    action_text = str(classifier(f"Anfrage: {query}")).lower().strip()

    # Standard ist Abruf, falls die Antwort nicht eindeutig ist
    return "store" if "store" in action_text else "retrieve"


def run_kb_agent(query):
    """Verarbeitet eine Nutzeranfrage mit dem Wissensdatenbank-Agenten."""
    action = determine_action(query)

    if action == "store":
        print(
            "\nIch kann keine neuen Informationen speichern: Diese Wissensdatenbank wird "
            "nur lesend zugegriffen (S3-basierte Datenquelle in einem anderen Konto)."
        )
    else:
        # MemoryManager bettet relevante KB-Inhalte automatisch in den
        # Modellinput ein – Abruf und Beantwortung geschehen in einem Agenten-Aufruf.
        agent = Agent(
            model=MODEL_ID,
            system_prompt=ANSWER_SYSTEM_PROMPT,
            memory_manager=MemoryManager(stores=[knowledge_store]),
        )
        agent(query)


if __name__ == "__main__":
    # Willkommensnachricht ausgeben
    print("\n🧠 Wissensdatenbank-Agent 🧠\n")
    print("Dieser Agent beantwortet Fragen aus deiner Wissensdatenbank.")
    print("Die Lab-KB enthält deutschsprachige Dokumente zu Unternehmens-Compliance und Nachhaltigkeit. Probiere:")
    print("- \"Welche ISO-Zertifizierungen werden erwähnt?\"")
    print("- \"Was sind die Umweltziele?\"")
    print("\nGib deine Anfrage unten ein oder 'exit' zum Beenden:")

    # Interaktive Schleife
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit", "beenden"]:
                print("\nAuf Wiedersehen! 👋")
                break

            if not user_input.strip():
                continue

            # Eingabe durch den Wissensdatenbank-Agenten verarbeiten
            print("Verarbeite...")
            run_kb_agent(user_input)

        except KeyboardInterrupt:
            print("\n\nAusführung unterbrochen. Beende...")
            break
        except Exception as e:
            print(f"\nEin Fehler ist aufgetreten: {str(e)}")
