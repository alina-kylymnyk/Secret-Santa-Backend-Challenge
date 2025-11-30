import csv
import logging
from io import BytesIO, StringIO
from typing import List

from src.database.models import DrawResult

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting draw results in various formats"""
    
    @staticmethod
    def generate_text_export(results, game_code):
        """
        Generate text export of draw results.
        """
        if not results:
            return f"Немає результатів для гри {game_code}"
        
        lines = [
            f"🎁 Результати Secret Santa {game_code}",
            "",
            f"Всього пар: {len(results)}",
            "",
            "=" * 50,
            ""
        ]
        
        # Sort by giver name for consistent output
        sorted_results = sorted(results, key=lambda r: r.giver_name)
        
        for result in sorted_results:
            lines.append(f"{result.giver_name} → дарує → {result.receiver_name}")
        
        lines.extend([
            "",
            "=" * 50,
            "",
            "⚠️ КОНФІДЕНЦІЙНО: Не діліться цим списком з учасниками!",
            "Кожен учасник має знати тільки своє призначення."
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_csv_export(results):
        """
        Generate CSV file with draw results.
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Дарує", "Отримує"])
        
        # Sort by giver name
        sorted_results = sorted(results, key=lambda r: r.giver_name)
        
        # Write data rows
        for result in sorted_results:
            writer.writerow([result.giver_name, result.receiver_name])
        
        # Convert to BytesIO for file sending
        csv_bytes = BytesIO(output.getvalue().encode('utf-8-sig'))  # BOM for Excel
        csv_bytes.seek(0)
        
        logger.info(f"Generated CSV export with {len(results)} rows")
        
        return csv_bytes
    
    @staticmethod
    def generate_individual_messages(results):
        """
        Generate individual messages for each participant.
        
        This can be used to send private messages to each participant
        telling them who they should give a gift to
        """
        messages = {}
        
        for result in results:
            message = (
                f"🎅 <b>Secret Santa</b>\n\n"
                f"Привіт, {result.giver_name}!\n\n"
                f"🎁 Ти даруєш подарунок для:\n"
                f"<b>{result.receiver_name}</b>\n\n"
                f"Нікому не кажи про це! 🤫\n"
                f"Це таємниця до обміну подарунками!"
            )
            messages[result.giver_name] = message
        
        return messages
    
    @staticmethod
    def generate_markdown_export(results, game_code):
        """
        Generate Markdown-formatted export
        """
        if not results:
            return f"# Немає результатів для гри {game_code}"
        
        lines = [
            f"# 🎁 Secret Santa {game_code}",
            "",
            f"**Всього пар:** {len(results)}",
            "",
            "## Результати жеребкування",
            "",
            "| Дарує | Отримує |",
            "|-------|---------|"
        ]
        
        # Sort by giver name
        sorted_results = sorted(results, key=lambda r: r.giver_name)
        
        for result in sorted_results:
            lines.append(f"| {result.giver_name} | {result.receiver_name} |")
        
        lines.extend([
            "",
            "---",
            "",
            "⚠️ **КОНФІДЕНЦІЙНО**",
            "",
            "Не діліться цим списком з учасниками!",
            "Кожен має знати тільки своє призначення."
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_export(results):
        """
        Generate JSON-serializable export.
        """
        return {
            "total_pairs": len(results),
            "results": [
                {
                    "giver": result.giver_name,
                    "receiver": result.receiver_name
                }
                for result in sorted(results, key=lambda r: r.giver_name)
            ]
        }
    
    @staticmethod
    def validate_results(results):
        """
        Validate draw results for correctness.
        """
        if not results:
            return False, "No results to validate"
        
        givers = set()
        receivers = set()
        
        for result in results:
            # Check self-assignment
            if result.giver_name == result.receiver_name:
                return False, f"Self-assignment detected: {result.giver_name}"
            
            # Check duplicates
            if result.giver_name in givers:
                return False, f"Duplicate giver: {result.giver_name}"
            
            if result.receiver_name in receivers:
                return False, f"Duplicate receiver: {result.receiver_name}"
            
            givers.add(result.giver_name)
            receivers.add(result.receiver_name)
        
        # Check that giver and receiver sets match
        if givers != receivers:
            return False, "Giver and receiver sets don't match"
        
        return True, "Valid"


class ExportFormatter:
    """Helper class for formatting export data"""
    
    @staticmethod
    def format_table(results):
        """
        Format results as an ASCII table.
        """
        if not results:
            return "Немає результатів"
        
        # Calculate column widths
        sorted_results = sorted(results, key=lambda r: r.giver_name)
        
        max_giver = max(len(r.giver_name) for r in sorted_results)
        max_receiver = max(len(r.receiver_name) for r in sorted_results)
        
        # Ensure minimum width
        giver_width = max(max_giver, 10)
        receiver_width = max(max_receiver, 10)
        
        # Create table
        lines = []
        
        # Header
        header = f"┌─{'─' * giver_width}─┬─{'─' * receiver_width}─┐"
        title = f"│ {'Дарує'.ljust(giver_width)} │ {'Отримує'.ljust(receiver_width)} │"
        separator = f"├─{'─' * giver_width}─┼─{'─' * receiver_width}─┤"
        
        lines.extend([header, title, separator])
        
        # Data rows
        for result in sorted_results:
            row = f"│ {result.giver_name.ljust(giver_width)} │ {result.receiver_name.ljust(receiver_width)} │"
            lines.append(row)
        
        # Footer
        footer = f"└─{'─' * giver_width}─┴─{'─' * receiver_width}─┘"
        lines.append(footer)
        
        return "\n".join(lines)