"""
Digital Receipt Generator — AI-Powered Business Assistant
=========================================================
Author:  [Your Name]
Date:    2026-08-12
Purpose: An AI-powered business assistant that combines natural conversation
         with digital receipt generation. Talk to it like a real person — it
         understands greetings, daily conversation, and business requests.
         When you need a receipt, just ask!

Business Context (IT Management Perspective):
    In many small and medium-sized enterprises (SMEs), receipts are still
    handwritten or created manually in spreadsheets. This script automates
    the entire process — from data capture to formatted output and file
    storage — showcasing a core principle of digital transformation:
    replacing manual, error-prone tasks with reliable, repeatable software.

    The conversational AI layer (powered by Google Gemini) demonstrates how
    modern businesses integrate Large Language Models (LLMs) to create
    intuitive, human-like interfaces for their digital tools.

Key Digitalization Concepts Demonstrated:
    1. Data Capture      — Structured user input replaces handwritten forms.
    2. Validation         — Automated checks prevent invalid data entry.
    3. Processing         — Calculations are performed instantly and accurately.
    4. Persistence        — The receipt is saved as a .txt file for archiving.
    5. Reproducibility    — The same process can be repeated consistently.
    6. AI Integration     — Natural language understanding for user interaction.

Requirements:
    Python 3.6+ (uses f-strings).
    google-genai package (pip install google-genai).
"""

import os
import sys
import re
import json
from datetime import datetime

# Google Gemini AI SDK — the NEW google-genai library
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Force UTF-8 encoding on Windows terminals to support emoji characters.
# This is a common compatibility fix for non-Unix operating systems.
# ---------------------------------------------------------------------------
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RECEIPT_WIDTH = 48          # Character width of the receipt (mirrors thermal printers)
TAX_RATE = 0.19             # 19% MwSt. (German VAT rate)
CURRENCY_SYMBOL = "\u20ac"  # Euro sign

# ---------------------------------------------------------------------------
# Gemini AI Client — used for natural conversation
# ---------------------------------------------------------------------------
GEMINI_API_KEY = "AIzaSyDZaQUCFmMymjqIjAHQWsdJUOH1vwnbEO4"
client = genai.Client(api_key=GEMINI_API_KEY)


# ===========================================================================
#  Helper Functions
# ===========================================================================

def print_banner():
    """Display a welcoming banner when the program starts."""
    print("\n" + "=" * RECEIPT_WIDTH)
    print("\U0001f9fe  AI BUSINESS ASSISTANT  \U0001f9fe".center(RECEIPT_WIDTH))
    print("=" * RECEIPT_WIDTH)
    print("Chat with me or generate a receipt!".center(RECEIPT_WIDTH))
    print("Type 'exit' to quit.".center(RECEIPT_WIDTH))
    print("=" * RECEIPT_WIDTH + "\n")


def get_text_input(prompt: str) -> str:
    """
    Prompt the user for a non-empty text string.

    Business rationale:
        Ensuring that fields like 'Customer Name' are never blank mirrors
        the mandatory-field concept in enterprise ERP systems (e.g., SAP).
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("\u26a0\ufe0f  This field cannot be empty. Please try again.")


def get_positive_float(prompt: str) -> float:
    """
    Prompt the user for a positive decimal number (e.g., a price).

    Implements try-except error handling to gracefully reject non-numeric
    or negative input — a basic but essential data-validation technique.
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value <= 0:
                print("\u26a0\ufe0f  Value must be greater than zero.")
                continue
            return value
        except ValueError:
            print(f"\u274c  '{raw}' is not a valid number. Please enter a numeric value.")


def get_positive_int(prompt: str) -> int:
    """
    Prompt the user for a positive whole number (e.g., a quantity).

    Quantities are inherently integers — you cannot sell 2.5 units of
    a product in most retail scenarios, so we enforce int conversion here.
    """
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value <= 0:
                print("\u26a0\ufe0f  Quantity must be at least 1.")
                continue
            return value
        except ValueError:
            print(f"\u274c  '{raw}' is not a valid whole number. Please enter an integer.")


def sanitize_filename(name: str) -> str:
    """
    Convert a customer name into a safe, filesystem-friendly string.

    Example: 'Max Müller' -> 'Max_Mueller'

    This prevents OS-level errors when saving receipt files.
    """
    # Replace common German umlauts for broad compatibility
    replacements = {
        "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue",
        "\u00c4": "Ae", "\u00d6": "Oe", "\u00dc": "Ue",
        "\u00df": "ss",
    }
    for char, replacement in replacements.items():
        name = name.replace(char, replacement)

    # Replace any remaining non-alphanumeric characters with underscores
    name = re.sub(r"[^A-Za-z0-9]+", "_", name)
    return name.strip("_")


# ===========================================================================
#  Core Business Logic
# ===========================================================================

def collect_line_items() -> list:
    """
    Interactively collect one or more line items from the user.

    Each line item is stored as a dictionary — a simple but effective
    data structure that maps directly to database rows or JSON objects
    in real-world enterprise applications.

    Returns:
        A list of dictionaries, each with keys: 'name', 'price', 'quantity', 'subtotal'.
    """
    items = []
    print("\n\U0001f4e6 Enter the items/services for this receipt.")
    print("   (Type 'done' as the item name when finished.)\n")

    item_number = 1
    while True:
        print(f"--- Item #{item_number} ---")
        name = input("   Item/Service name (or 'done'): ").strip()

        if name.lower() == "done":
            if not items:
                print("\u26a0\ufe0f  You must add at least one item before finishing.")
                continue
            break

        if not name:
            print("\u26a0\ufe0f  Item name cannot be empty.")
            continue

        price = get_positive_float(f"   Unit price ({CURRENCY_SYMBOL}): ")
        quantity = get_positive_int("   Quantity: ")
        subtotal = round(price * quantity, 2)

        items.append({
            "name": name,
            "price": price,
            "quantity": quantity,
            "subtotal": subtotal,
        })

        print(f"   \u2705 Added: {name} x{quantity} = {CURRENCY_SYMBOL}{subtotal:.2f}\n")
        item_number += 1

    return items


def build_receipt(customer_name: str, items: list) -> str:
    """
    Construct a formatted receipt string.

    The layout mimics a real thermal-printer receipt, with fixed-width
    columns. This demonstrates how digital systems can replicate — and
    improve upon — traditional paper formats.

    Args:
        customer_name: The name of the customer.
        items:         A list of line-item dictionaries.

    Returns:
        A multi-line string representing the complete receipt.
    """
    now = datetime.now()
    receipt_id = now.strftime("%Y%m%d%H%M%S")  # Unique ID based on timestamp

    # --- Calculate financial totals ---
    net_total = sum(item["subtotal"] for item in items)
    tax_amount = round(net_total * TAX_RATE, 2)
    gross_total = round(net_total + tax_amount, 2)

    # --- Build the receipt line by line ---
    border = "=" * RECEIPT_WIDTH
    thin_border = "-" * RECEIPT_WIDTH

    lines = [
        border,
        "DIGITAL RECEIPT".center(RECEIPT_WIDTH),
        border,
        f"  Receipt No. : {receipt_id}",
        f"  Date        : {now.strftime('%d.%m.%Y')}",
        f"  Time        : {now.strftime('%H:%M:%S')}",
        f"  Customer    : {customer_name}",
        thin_border,
        f"  {'Item':<20} {'Qty':>5} {'Price':>9} {'Total':>9}",
        thin_border,
    ]

    # Add each line item
    for item in items:
        lines.append(
            f"  {item['name']:<20} {item['quantity']:>5} "
            f"{CURRENCY_SYMBOL}{item['price']:>7.2f} "
            f"{CURRENCY_SYMBOL}{item['subtotal']:>7.2f}"
        )

    lines.extend([
        thin_border,
        f"  {'Net Total:':<34} {CURRENCY_SYMBOL}{net_total:>7.2f}",
        f"  {'MwSt. (19%):':<34} {CURRENCY_SYMBOL}{tax_amount:>7.2f}",
        border,
        f"  {'TOTAL DUE:':<34} {CURRENCY_SYMBOL}{gross_total:>7.2f}",
        border,
        "",
        "Thank you for your business!".center(RECEIPT_WIDTH),
        "Please keep this receipt for your records.".center(RECEIPT_WIDTH),
        "",
        border,
    ])

    return "\n".join(lines)


def save_receipt(receipt_text: str, customer_name: str) -> str:
    """
    Persist the receipt to a .txt file in the current working directory.

    File-based persistence is the simplest form of digital archiving.
    In a production system, this would be replaced by a database INSERT
    or cloud storage upload — but the principle remains the same.

    Args:
        receipt_text:  The formatted receipt string.
        customer_name: Used to generate the filename.

    Returns:
        The absolute path of the saved file.
    """
    safe_name = sanitize_filename(customer_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Receipt_{safe_name}_{timestamp}.txt"

    # Save in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(receipt_text)

    return filepath


# ===========================================================================
#  AI Conversation Layer
# ===========================================================================

# Keywords that signal the user wants to generate a receipt
RECEIPT_KEYWORDS = [
    "receipt", "invoice", "bill", "quittung", "rechnung",
    "generate", "create receipt", "new receipt", "make a receipt",
    "create a bill", "generate invoice",
]


def wants_receipt(user_input: str) -> bool:
    """
    Detect whether the user's message is asking to generate a receipt.

    Uses simple keyword matching — a lightweight intent-detection approach.
    In production, this could be replaced by an NLU (Natural Language
    Understanding) model for more accurate intent classification.
    """
    lowered = user_input.lower()
    return any(keyword in lowered for keyword in RECEIPT_KEYWORDS)


def chat_with_ai(user_message: str, conversation_history: list) -> str:
    """
    Send the user's message to Gemini and return a natural response.

    Maintains conversation history so the AI remembers context across
    multiple turns — a key feature of modern conversational interfaces.

    Args:
        user_message:         The latest message from the user.
        conversation_history: A list of previous messages for context.

    Returns:
        The AI's response as a string.
    """
    # System instruction defines the AI's personality and role
    system_instruction = (
        "You are a friendly, helpful AI Business Assistant. Your name is Nova. "
        "You work at a digital business solutions company. "
        "You can have normal, warm, human-like conversations — respond to greetings, "
        "small talk, jokes, and daily topics naturally. Keep responses concise (2-3 sentences max). "
        "If the user asks about receipts, invoices, or billing, let them know you can "
        "help generate a digital receipt and they should type 'receipt' or 'create receipt' to start. "
        "Be professional but personable. Use a friendly tone."
    )

    # Add the new user message to conversation history
    conversation_history.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    ))

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=conversation_history,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

        ai_reply = response.text.strip()

        # Add the AI's response to conversation history for future context
        conversation_history.append(types.Content(
            role="model",
            parts=[types.Part.from_text(text=ai_reply)],
        ))

        return ai_reply

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "UNAUTHENTICATED" in error_msg:
            return "\u26a0\ufe0f I'm having trouble connecting to my AI brain. The API key may be invalid."
        return f"\u26a0\ufe0f Sorry, I ran into an issue: {e}"


def run_receipt_workflow():
    """
    Execute the guided receipt generation workflow.

    This is separated from the main loop so the conversational AI
    can seamlessly hand off to structured data collection when needed.
    """
    print("\n" + "-" * RECEIPT_WIDTH)
    print("\U0001f9fe Starting Receipt Generator...")
    print("-" * RECEIPT_WIDTH + "\n")

    # --- Step 1: Data Capture ---
    print("\U0001f464 Customer Information")
    customer_name = get_text_input("   Customer name: ")

    # --- Step 2: Collect Line Items ---
    items = collect_line_items()

    # --- Step 3: Generate the Receipt ---
    receipt_text = build_receipt(customer_name, items)

    # --- Step 4: Display to Terminal ---
    print("\n\U0001f4c4 Here is the generated receipt:\n")
    print(receipt_text)

    # --- Step 5: Persist to File ---
    filepath = save_receipt(receipt_text, customer_name)
    print(f"\n\U0001f4be Receipt saved successfully!")
    print(f"   File: {filepath}")
    print("\n" + "-" * RECEIPT_WIDTH)
    print("\U0001f4ac Back to chat! Ask me anything or create another receipt.")
    print("-" * RECEIPT_WIDTH + "\n")


# ===========================================================================
#  Main Application Loop
# ===========================================================================

def main():
    """
    Entry point for the AI-powered Digital Receipt Generator.

    Implements a conversational loop where the user can chat naturally
    with the AI assistant. When the user requests a receipt, the system
    seamlessly transitions into the structured receipt workflow and then
    returns to the conversation.
    """
    print_banner()

    # Conversation history maintains multi-turn context with the AI
    conversation_history = []

    while True:
        try:
            user_input = input("\U0001f9d1 You: ").strip()

            # --- Exit commands ---
            if user_input.lower() in ("exit", "quit", "q", "bye", "tschüss"):
                # Let the AI say goodbye
                farewell = chat_with_ai("The user is leaving. Say a warm goodbye.", conversation_history)
                print(f"\U0001f916 Nova: {farewell}")
                print("\n\U0001f44b Auf Wiedersehen!\n")
                break

            # --- Skip empty input ---
            if not user_input:
                continue

            # --- Check if user wants a receipt ---
            if wants_receipt(user_input):
                print(f"\U0001f916 Nova: Sure! Let me start the receipt generator for you.")
                run_receipt_workflow()
                continue

            # --- Otherwise, chat naturally with the AI ---
            response = chat_with_ai(user_input, conversation_history)
            print(f"\U0001f916 Nova: {response}\n")

        except KeyboardInterrupt:
            print("\n\n\U0001f44b Auf Wiedersehen!\n")
            break


# ---------------------------------------------------------------------------
# Standard Python entry-point guard.
# Ensures the script only runs when executed directly, not when imported
# as a module — a best practice in professional Python development.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()