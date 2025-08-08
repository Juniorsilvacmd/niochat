#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from core.models import Provedor
from conversations.models import Contact, Conversation, Message
from integrations.models import WhatsAppIntegration

print("🔍 Verificando configurações do sistema...\n")

# Verificar provedores
provedores = Provedor.objects.all()
print(f"📊 Provedores encontrados: {provedores.count()}")

for p in provedores:
    print(f"\n🏢 Provedor: {p.nome}")
    print(f"   ID: {p.id}")
    print(f"   Ativo: {p.is_active}")
    print(f"   Integrações: {p.integracoes_externas}")
    
    # Verificar integração WhatsApp
    whatsapp_integration = WhatsAppIntegration.objects.filter(provedor=p).first()
    if whatsapp_integration:
        print(f"   WhatsApp Integration: {whatsapp_integration}")
        print(f"   - Ativo: {whatsapp_integration.is_active}")
        print(f"   - Conectado: {whatsapp_integration.is_connected}")
        print(f"   - Instance: {whatsapp_integration.instance_name}")
    else:
        print(f"   ❌ WhatsApp Integration: NÃO CONFIGURADA")

# Verificar contatos e conversas
contacts = Contact.objects.all()
conversations = Conversation.objects.all()
messages = Message.objects.all()

print(f"\n📞 Contatos: {contacts.count()}")
print(f"💬 Conversas: {conversations.count()}")
print(f"💭 Mensagens: {messages.count()}")

# Verificar últimas mensagens
print(f"\n📨 Últimas 5 mensagens:")
recent_messages = Message.objects.order_by('-created_at')[:5]
for msg in recent_messages:
    print(f"   - {msg.created_at}: {msg.content[:50]}... (Conversa: {msg.conversation.id})")

print(f"\n🌐 URLs de Webhook:")
print(f"   - Evolution/Uazapi: http://localhost:8010/webhook/evolution-uazapi/")
print(f"   - Evolution/Uazapi (sem slash): http://localhost:8010/webhook/evolution-uazapi")

print(f"\n🔧 Para testar o webhook:")
print(f"   curl -X POST http://localhost:8010/webhook/evolution-uazapi/ \\")
print(f"     -H 'Content-Type: application/json' \\")
print(f"     -d '{{\"event\":\"message\",\"data\":{{\"chatid\":\"5511999999999@s.whatsapp.net\",\"content\":\"teste\"}}}}'") 