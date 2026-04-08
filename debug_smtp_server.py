#!/usr/bin/env python3
"""
Serveur SMTP de debug local pour tester l'envoi d'emails
"""
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging
import asyncio

class DebugHandler(Debugging):
    def handle_message(self, message):
        print("\n" + "="*80)
        print("📧 NOUVEL EMAIL REÇU")
        print("="*80)
        return super().handle_message(message)

async def amain():
    controller = Controller(DebugHandler(), hostname='localhost', port=1025)
    controller.start()
    print("\n🚀 Serveur SMTP de debug démarré sur localhost:1025")
    print("📧 Les emails envoyés s'afficheront ci-dessous")
    print("💡 Appuyez sur Ctrl+C pour arrêter\n")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
        controller.stop()

if __name__ == '__main__':
    asyncio.run(amain())
