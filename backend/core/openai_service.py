"""
Serviço para integração com OpenAI ChatGPT
"""

import os
import openai
import logging
import json
from typing import Dict, Any, Optional, List
from django.conf import settings
from .models import Provedor, SystemConfig
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = self._get_api_key()
        openai.api_key = self.api_key
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 1000
        self.temperature = 0.7

    def _get_api_key(self) -> str:
        """Busca a chave da API da OpenAI do banco de dados ou variável de ambiente"""
        try:
            # Primeiro tenta buscar do banco de dados
            config = SystemConfig.objects.first()
            if config and config.openai_api_key:
                logger.info("Usando chave da API OpenAI do banco de dados")
                return config.openai_api_key
        except Exception as e:
            logger.warning(f"Erro ao buscar chave da API do banco: {e}")
        
        # Fallback para variável de ambiente
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("Usando chave da API OpenAI da variável de ambiente")
            return api_key
        
        # Se não encontrar chave, retornar None para que o erro seja tratado adequadamente
        logger.error("Nenhuma chave da API OpenAI encontrada - configure no painel do superadmin")
        return None

    async def _get_api_key_async(self) -> str:
        """Versão assíncrona para buscar a chave da API da OpenAI"""
        try:
            # Usar sync_to_async para buscar do banco de dados
            config = await sync_to_async(SystemConfig.objects.first)()
            if config and config.openai_api_key:
                logger.info("Usando chave da API OpenAI do banco de dados (async)")
                return config.openai_api_key
        except Exception as e:
            logger.warning(f"Erro ao buscar chave da API do banco (async): {e}")
        
        # Fallback para variável de ambiente
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("Usando chave da API OpenAI da variável de ambiente (async)")
            return api_key
        
        # Se não encontrar chave, retornar None para que o erro seja tratado adequadamente
        logger.error("Nenhuma chave da API OpenAI encontrada - configure no painel do superadmin (async)")
        return None

    def update_api_key(self):
        """Atualiza a chave da API quando ela é modificada no banco"""
        self.api_key = self._get_api_key()
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("Chave da API OpenAI atualizada")
        else:
            logger.error("Não foi possível atualizar a chave da API OpenAI - chave não configurada")

    async def update_api_key_async(self):
        """Versão assíncrona para atualizar a chave da API"""
        self.api_key = await self._get_api_key_async()
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("Chave da API OpenAI atualizada (async)")
        else:
            logger.error("Não foi possível atualizar a chave da API OpenAI - chave não configurada (async)")

    def _get_greeting_time(self) -> str:
        """Retorna saudação baseada no horário atual"""
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            return "Bom dia"
        elif 12 <= hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
    


    def _build_system_prompt(self, provedor: Provedor) -> str:
        import json
        from datetime import datetime
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except:
            pass
        now = datetime.now()
        
        # Dados básicos
        nome_agente = provedor.nome_agente_ia or 'Assistente Virtual'
        nome_provedor = provedor.nome or 'Provedor de Internet'
        site_oficial = provedor.site_oficial or ''
        endereco = provedor.endereco or ''
        
        # Configurações dinâmicas
        greeting_time = self._get_greeting_time()
        
        # Redes sociais
        redes = provedor.redes_sociais or {}
        if not isinstance(redes, dict):
            try:
                import json as _json
                redes = _json.loads(redes)
            except Exception:
                redes = {}
        
        # Horários de funcionamento
        horarios = {}
        try:
            import json as _json
            if provedor.horarios_atendimento:
                if isinstance(provedor.horarios_atendimento, str):
                    horarios = _json.loads(provedor.horarios_atendimento)
                elif isinstance(provedor.horarios_atendimento, dict):
                    horarios = provedor.horarios_atendimento
                else:
                    horarios = {}
            else:
                horarios = {}
        except Exception:
            horarios = {}
        
        # Personalidade (pode ser lista ou objeto estruturado)
        personalidade = provedor.personalidade or []
        personalidade_avancada = None
        
        # Verificar se é personalidade avançada (objeto) ou lista simples
        if isinstance(personalidade, dict):
            personalidade_avancada = personalidade
            # Manter compatibilidade usando características como personalidade base
            personalidade_traits = personalidade.get('caracteristicas', '').split(',') if personalidade.get('caracteristicas') else []
            personalidade = [trait.strip() for trait in personalidade_traits if trait.strip()] or ["Atencioso", "Carismatico", "Educado", "Objetivo", "Persuasivo"]
        elif not personalidade:
            personalidade = ["Atencioso", "Carismatico", "Educado", "Objetivo", "Persuasivo"]
        
        # Planos de internet
        planos_internet = provedor.planos_internet or ''
        # Informações extras
        informacoes_extras = provedor.informacoes_extras or ''
        # Emojis
        uso_emojis = provedor.uso_emojis or ""
        
        # Novos campos dinâmicos
        taxa_adesao = provedor.taxa_adesao or ''
        inclusos_plano = provedor.inclusos_plano or ''
        multa_cancelamento = provedor.multa_cancelamento or ''
        tipo_conexao = provedor.tipo_conexao or ''
        prazo_instalacao = provedor.prazo_instalacao or ''
        documentos_necessarios = provedor.documentos_necessarios or ''
        observacoes = provedor.observacoes or ''
        
        # E-mail de contato principal
        email_contato = ''
        if hasattr(provedor, 'emails') and provedor.emails:
            emails = provedor.emails
            if isinstance(emails, dict):
                email_contato = next((v for v in emails.values() if v), '')
            elif isinstance(emails, list) and emails:
                email_contato = emails[0]
        
        # Data atual formatada
        data_atual = now.strftime('%A, %d/%m/%Y, %H:%M')
        
        # Construir identidade do agente
        identidade = f"Sou o {nome_agente}, um assistente virtual. Estou aqui para te ajudar com dúvidas, verificar se você já é nosso cliente e te apresentar os melhores planos de internet disponíveis."
        
        # Objetivos padrão
        objetivos = [
            f"Identificar se a pessoa é ou não cliente da {nome_provedor}",
            "Atender clientes com dúvidas ou problemas (ex: fatura, suporte)",
            "Apresentar os planos de internet para novos interessados",
            "Encaminhar para um atendente humano quando necessário"
        ]
        
        # Ferramentas disponíveis - usar personalizadas se disponíveis, senão usar padrão
        ferramentas_padrao = [
            {
                "name": "buscar_documentos",
                "usage": "Use esta ferramenta sempre que o usuário fizer uma pergunta técnica ou comercial fora do seu conhecimento. Se não encontrar nada, encaminhe para um atendente humano."
            },
            {
                "name": "validar_cpf",
                "usage": "Após coletar o CPF do cliente, utilize essa ferramenta para validar o CPF e recuperar os dados do cliente."
            },
            {
                "name": "buscar_faturas",
                "usage": "Use esta ferramenta quando o cliente solicitar a segunda via da fatura, conta ou boleto. Sempre pergunte se ele deseja receber o QRCODE PIX ou o boleto. Se ele ja estiver falado, não pergunte novamente.",
                "observacao": "Se o cliente tiver mais de 2 faturas pendentes, informe e encaminhe para o atendimento humano usando a tool 'encaminha_financeiro'."
            },
            {
                "name": "envia_boleto",
                "usage": "Use esta ferramenta para enviar o boleto para cliente apos ele ter decidido que deseja receber a sua fatura via boleto.",
                "observacao": "Após usar a ferramenta, pergunte se o cliente deseja mais alguma coisa."
            },
            {
                "name": "envia_qrcode",
                "usage": "Use esta ferramenta para enviar o QRCODE PIX para cliente apos ele ter decidido que deseja receber a sua fatura via pix/qrcode",
                "observacao": "Após usar a ferramenta, pergunte se o cliente deseja mais alguma coisa."
            },
            {
                "name": "prazo_de_confianca",
                "usage": "Use esta ferramenta para tentar desbloquear o contrato do cliente por prazo de confiança, caso o cliente peça pra desbloquear.",
                "observacao": "Após usar a ferramenta, pergunte se o cliente deseja a sua fatura para pagamento antes que o contrato fique suspenso novamente."
            },
            {
                "name": "checha_conexao",
                "usage": "Use esta ferramenta para verificar o status da conexão do cliente. Ela retornará se o equipamento está online ou offline."
            },
            {
                "name": "encaminha_suporte",
                "usage": "Use esta ferramenta para encaminhar o cliente para o suporte humano quando necessário, como em casos de problemas técnicos que não puder resolver."
            },
            {
                "name": "encaminha_financeiro",
                "usage": "Use esta ferramenta para encaminhar o cliente para o departamento financeiro quando necessário, como em casos de dúvidas sobre faturas, pagamentos ou questões financeiras."
            },
            {
                "name": "GetCpfContato",
                "usage": "Use essa ferramenta para capturar o CPF do cliente no contato inicial. Ela retornará o CPF/CNPJ já salvo no contato do ChatWoot, se existir. *SEMPRE* use essa ferramenta antes de solicitar o CPF ao cliente.",
                "observacao": "**EXECUÇÃO OBRIGATÓRIA**: Deve ser acionada automaticamente nos primeiros 3 segundos de interação, antes de qualquer pergunta. Se falhar, reinicie o atendimento.",
                "critical_rule": True
            },
            {
                "name": "SalvarCpfContato",
                "usage": "Use essa ferramenta para salvar o numero do CPF do cliente dentro do seu contato no ChatWoot. O CPF DEVE SER SALVO SOMENTE NO FORMATO NUMÉRICO."
            },
            {
                "name": "consultar_cliente_sgp",
                "usage": "Use esta ferramenta para consultar dados reais do cliente no SGP usando CPF/CNPJ. Retorna nome, contratos, status reais do sistema.",
                "observacao": "SEMPRE use esta ferramenta após receber CPF/CNPJ de cliente existente. Use APENAS os dados retornados.",
                "critical_rule": True
            },
            {
                "name": "verificar_acesso_sgp", 
                "usage": "Use para verificar status de acesso/conexão de um contrato específico no SGP.",
                "observacao": "Use após identificar o contrato do cliente via consultar_cliente_sgp."
            },
            {
                "name": "gerar_fatura_completa",
                "usage": "Use para gerar fatura completa com boleto, PIX, QR code e todos os dados de pagamento.",
                "observacao": "SEMPRE use esta ferramenta quando cliente pedir fatura/boleto. Retorna dados completos incluindo PIX.",
                "critical_rule": True
            },
            {
                "name": "gerar_pix_qrcode",
                "usage": "Use para gerar especificamente PIX e QR code para uma fatura.",
                "observacao": "Use quando precisar apenas dos dados PIX de uma fatura específica."
            }
        ]
        
        # Usar ferramentas personalizadas se disponíveis, senão usar padrão
        ferramentas = provedor.ferramentas_ia if provedor.ferramentas_ia else ferramentas_padrao
        
        # Regras gerais - usar personalizadas se disponíveis, senão usar padrão
        regras_padrao = [
            f"Responder apenas sobre assuntos relacionados à {nome_provedor}.",
            "Nunca inventar informações. Sempre use 'buscar_documentos' para confirmar dados técnicos ou planos.",
            "Se não souber ou for fora do escopo, diga exatamente: 'Desculpe, não posso te ajudar com isso. Encaminhando para um atendente humano.'",
            "Seja natural e conversacional. Responda cumprimentos e perguntas gerais de forma amigável.",
            "REGRA CRÍTICA: Se cliente já disse o que quer (fatura, boleto, suporte), NÃO pergunte 'como posso ajudar' - vá DIRETO executar a demanda.",
            "Quando cliente mencionar FATURA/BOLETO: peça CPF → consulte SGP → apresente dados → AUTOMATICAMENTE gere fatura completa com QR code e PIX.",
            "Quando cliente mencionar PROBLEMA TÉCNICO: peça CPF → consulte SGP → apresente dados → AUTOMATICAMENTE verifique status da conexão.",
            "NUNCA use textos genéricos se a demanda já foi especificada - seja específico e direto.",
            "Após receber CPF/CNPJ: consulte automaticamente no SGP e execute a ação solicitada.",
            "NUNCA invente nomes de clientes, contratos ou dados - use APENAS informações reais do SGP.",
            "Para novos clientes: responda sobre planos sem necessidade de CPF."
        ]
        
        regras_gerais = provedor.regras_gerais if provedor.regras_gerais else regras_padrao
        
        # Fluxo de atendimento - usar personalizado se disponível, senão usar padrão
        fluxo_padrao = {
            "boas_vindas": {
                "instructions": f"Use '{greeting_time}' para saudar baseado no horário atual. Seja natural e acolhedor. Só pergunte se é cliente ou colete CPF quando ele solicitar algo específico como boleto, suporte técnico, problemas de conexão, etc.",
                "example_message": f"{greeting_time}! Seja bem-vindo à {nome_provedor}! Eu sou o {nome_agente}, como posso te ajudar?"
            },
            "cliente": {
                "descricao_geral": f"Fluxo para quem já é cliente da {nome_provedor}.",
                "instrucoes_importantes": [
                    "NUNCA use textos prontos ou pergunte 'Para te ajudar melhor, você já é nosso cliente?'",
                    "Se o cliente disser que já é cliente, vá DIRETO para solicitar CPF/CNPJ",
                    "Após receber CPF/CNPJ, consulte AUTOMATICAMENTE no SGP e retorne os dados reais",
                    "Use apenas dados reais vindos do SGP, nunca invente informações"
                ],
                "etapas": [
                    {
                        "etapa": 1,
                        "titulo": "Detectar demanda específica",
                        "acao_ia": "SE o cliente já mencionou uma demanda específica (fatura, boleto, problema técnico, etc.), vá DIRETO para ela. NÃO pergunte 'como posso ajudar' se ele já disse.",
                        "demandas_especificas": [
                            "fatura", "boleto", "conta", "pagamento", "segunda via",
                            "sem internet", "internet parou", "problema", "suporte",
                            "cancelar", "mudar plano", "reclamação"
                        ],
                        "observacao": "Se cliente disse 'quero pagar minha fatura', vá direto para solicitar CPF e gerar fatura."
                    },
                    {
                        "etapa": 2,
                        "titulo": "Solicitar CPF/CNPJ para demanda específica",
                        "acao_ia": "Para demandas específicas, peça CPF/CNPJ de forma direcionada ao que ele quer.",
                        "examples": {
                            "fatura": "Para gerar sua fatura, preciso do seu CPF ou CNPJ.",
                            "suporte": "Para verificar sua conexão, preciso do seu CPF ou CNPJ.",
                            "geral": "Para localizar seu cadastro, preciso do seu CPF ou CNPJ."
                        }
                    },
                    {
                        "etapa": 3,
                        "titulo": "Consultar SGP e executar demanda automaticamente",
                        "acao_ia": "Após consultar dados no SGP, execute automaticamente a demanda solicitada:",
                        "acoes_por_demanda": {
                            "fatura": "Consulte SGP → Apresente dados do cliente → AUTOMATICAMENTE gere fatura com QR code, PIX e valor",
                            "suporte": "Consulte SGP → Apresente dados do cliente → AUTOMATICAMENTE verifique status da conexão",
                            "geral": "Consulte SGP → Apresente dados do cliente → Pergunte como pode ajudar"
                        },
                        "observacao": "NÃO pergunte 'como posso ajudar' se o cliente já especificou o que quer."
                    },
                    {
                        "etapa": 4,
                        "titulo": "Entregar resultado completo",
                        "acao_ia": "Entregue o resultado completo da demanda em uma mensagem organizada.",
                        "example_fatura": "🧾 **Sua Fatura**\n📄 Valor: R$ 89,90\n📅 Vencimento: 15/08/2024\n💳 Código PIX: pix123abc\n📱 QR Code: [link]\n📋 ID Fatura: #12345"
                    }
                ]
            },
            "nao_cliente": {
                "descricao_geral": f"Fluxo para pessoas que ainda não são clientes da {nome_provedor}.",
                "etapas": [
                    {
                        "etapa": 1,
                        "titulo": "Descobrir interesse",
                        "acao_ia": f"Perguntar se conhece a {nome_provedor} e qual sua necessidade com internet. Se já tiver falado, não pergunte novamente.",
                        "example_message": f"👀Você já conhece a {nome_provedor}? Está buscando internet pra *casa*, *trabalho* ou algo mais específico? "
                    },
                    {
                        "etapa": 2,
                        "titulo": "Apresentar benefícios",
                        "acao_ia": f"Falar dos diferenciais da {nome_provedor} (fibra óptica, estabilidade, suporte, etc.).",
                        "example_message": f"A {nome_provedor} oferece internet via fibra óptica, super estável e com suporte 24/7! Temos planos incríveis para atender sua necessidade. Vamos ver qual é o melhor pra você? 😊"
                    },
                    {
                        "etapa": 3,
                        "titulo": "Apresentar planos",
                        "acao_ia": "Utilize 'buscar_documentos' para mostrar os planos atuais e tirar dúvidas."
                    },
                    {
                        "etapa": 4,
                        "titulo": "Coletar dados para proposta",
                        "acao_ia": "Pedir nome completo e endereço para continuar com a contratação.",
                        "example_message": "Que ótimo! Para seguir com a contratação, preciso do seu nome completo e endereço, por favor. Assim já agilizo tudo para você! "
                    },
                    {
                        "etapa": 5,
                        "titulo": "Encaminhar para atendimento humano",
                        "acao_ia": "Encaminhar para equipe de vendas ou atendimento final com dados coletados."
                    }
                ]
            },
            "fallback": {
                "instructions": "Se não entender a intenção ou for assunto fora da Fibra/telecom, usar resposta padrão e encaminhar.",
                "example_message": "Desculpe, não posso te ajudar com isso. Encaminhando para um atendente humano."
            }
        }
        
        fluxo = provedor.fluxo_atendimento if provedor.fluxo_atendimento else fluxo_padrao
        
        # Montar prompt JSON completo
        prompt_dict = {
            "name": nome_agente,
            "context": {
                "identity": identidade,
                "business": nome_provedor,
                "site": site_oficial,
                "endereco": endereco,
                "language": "Português Brasileiro",
                "data_atual": data_atual,
                "planos_internet": planos_internet,
                "informacoes_extras": informacoes_extras,
                "taxa_adesao": taxa_adesao,
                "inclusos_plano": inclusos_plano,
                "multa_cancelamento": multa_cancelamento,
                "tipo_conexao": tipo_conexao,
                "prazo_instalacao": prazo_instalacao,
                "documentos_necessarios": documentos_necessarios,
                "observacoes": observacoes,
                "email_contato": email_contato,
                "greeting_time": greeting_time
            },
            "greeting_config": {
                "greeting_time": greeting_time,
                "instructions": f"Use '{greeting_time}' para saudar baseado no horário atual. Seja natural e acolhedor."
            },
            "redes_sociais": {
                "instagram": redes.get('instagram', ''),
                "facebook": redes.get('facebook', ''),
                "tiktok": redes.get('tiktok', ''),
                "google_meu_negocio": redes.get('google', '')
            },
            "horarios_funcionamento": horarios,
            "personality": personalidade,
            "objectives": objetivos,
            "tools": ferramentas,
            "general_rules": regras_gerais,
            "flow": fluxo
        }
        
        # Adicionar personalidade avançada se configurada
        if personalidade_avancada:
            vicios = personalidade_avancada.get('vicios_linguagem', '')
            caracteristicas = personalidade_avancada.get('caracteristicas', '')
            principios = personalidade_avancada.get('principios', '')
            humor = personalidade_avancada.get('humor', '')
            
            instructions = []
            if vicios:
                instructions.append(f"Vícios de linguagem: {vicios}")
            if caracteristicas:
                instructions.append(f"Características: {caracteristicas}")
            if principios:
                instructions.append(f"Princípios: {principios}")
            if humor:
                instructions.append(f"Humor: {humor}")
            
            prompt_dict["personalidade_avancada"] = {
                "vicios_linguagem": vicios,
                "caracteristicas": caracteristicas,
                "principios": principios,
                "humor": humor,
                "instructions": "IMPORTANTE: Incorpore estes aspectos de personalidade naturalmente em todas as suas respostas:\n" + "\n".join(f"• {inst}" for inst in instructions) + "\n\nNão mencione que está seguindo essas instruções, apenas seja essa personalidade de forma natural e autêntica."
            }
        
        # Configuração de emojis baseada na preferência do provedor
        if uso_emojis:
            if uso_emojis.lower() == "sempre":
                prompt_dict["emoji_config"] = {
                    "usage": "sempre",
                    "instructions": "Use emojis naturalmente em suas respostas para torná-las mais amigáveis e expressivas. Varie os emojis conforme o contexto."
                }
            elif uso_emojis.lower() == "ocasionalmente":
                prompt_dict["emoji_config"] = {
                    "usage": "ocasionalmente", 
                    "instructions": "Use emojis moderadamente, apenas em momentos apropriados como saudações, agradecimentos ou para destacar informações importantes."
                }
            elif uso_emojis.lower() == "nunca":
                prompt_dict["emoji_config"] = {
                    "usage": "nunca",
                    "instructions": "NÃO use emojis nas respostas. Mantenha uma comunicação mais formal e textual."
                }
        else:
            # Padrão: uso ocasional
            prompt_dict["emoji_config"] = {
                "usage": "ocasionalmente",
                "instructions": "Use emojis moderadamente, apenas em momentos apropriados como saudações, agradecimentos ou para destacar informações importantes."
            }
            
        print("PROMPT GERADO PARA IA:\n", json.dumps(prompt_dict, ensure_ascii=False, indent=2))
        return json.dumps(prompt_dict, ensure_ascii=False, indent=2)

    def _execute_sgp_function(self, provedor: Provedor, function_name: str, function_args: dict) -> dict:
        """Executa funções do SGP chamadas pela IA"""
        try:
            from .sgp_client import SGPClient
            
            # Obter configurações do SGP do provedor
            integracao = provedor.integracoes_externas or {}
            sgp_url = integracao.get('sgp_url')
            sgp_token = integracao.get('sgp_token') 
            sgp_app = integracao.get('sgp_app')
            
            if not all([sgp_url, sgp_token, sgp_app]):
                return {
                    "erro": "Configurações do SGP não encontradas. Configure no painel do provedor.",
                    "success": False
                }
            
            # Criar cliente SGP
            sgp = SGPClient(
                base_url=sgp_url,
                token=sgp_token,
                app_name=sgp_app
            )
            
            # Executar função solicitada
            if function_name == "consultar_cliente_sgp":
                cpf_cnpj = function_args.get('cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '')
                resultado = sgp.consultar_cliente(cpf_cnpj)
                
                # Processar resultado para formato mais legível
                if resultado.get('contratos'):
                    contrato = resultado['contratos'][0]
                    return {
                        "success": True,
                        "cliente_encontrado": True,
                        "nome": contrato.get('razaoSocial', 'Nome não encontrado'),
                        "contrato_id": contrato.get('contratoId'),
                        "status_contrato": contrato.get('contratoStatusDisplay'),
                        "dados_completos": resultado
                    }
                else:
                    return {
                        "success": True,
                        "cliente_encontrado": False,
                        "mensagem": "Cliente não encontrado com este CPF/CNPJ"
                    }
                    
            elif function_name == "verificar_acesso_sgp":
                contrato = function_args.get('contrato')
                resultado = sgp.verifica_acesso(contrato)
                
                status_conexao = (
                    resultado.get('msg') or
                    resultado.get('status') or 
                    resultado.get('status_conexao') or
                    resultado.get('mensagem') or
                    "Status não disponível"
                )
                
                return {
                    "success": True,
                    "contrato": contrato,
                    "status_conexao": status_conexao,
                    "dados_completos": resultado
                }
                
            elif function_name == "gerar_fatura_completa":
                contrato = function_args.get('contrato')
                
                # Gerar fatura/boleto
                fatura_resultado = sgp.segunda_via_fatura(contrato)
                
                # Se a fatura foi gerada com sucesso, gerar PIX também
                pix_dados = None
                if fatura_resultado and 'fatura' in str(fatura_resultado).lower():
                    try:
                        # Extrair ID da fatura do resultado (assumindo que vem no resultado)
                        fatura_id = fatura_resultado.get('id') or fatura_resultado.get('fatura_id') or contrato
                        pix_resultado = sgp.gerar_pix(fatura_id)
                        pix_dados = pix_resultado
                    except Exception as e:
                        logger.warning(f"Erro ao gerar PIX: {str(e)}")
                
                return {
                    "success": True,
                    "contrato": contrato,
                    "fatura_gerada": True,
                    "dados_fatura": fatura_resultado,
                    "pix_disponivel": pix_dados is not None,
                    "dados_pix": pix_dados,
                    "valor_fatura": fatura_resultado.get('valor') if fatura_resultado else None,
                    "vencimento": fatura_resultado.get('vencimento') if fatura_resultado else None,
                    "codigo_barras": fatura_resultado.get('codigo_barras') if fatura_resultado else None,
                    "link_pdf": fatura_resultado.get('link_pdf') if fatura_resultado else None
                }
                
            elif function_name == "gerar_pix_qrcode":
                fatura_id = function_args.get('fatura_id')
                resultado = sgp.gerar_pix(fatura_id)
                
                return {
                    "success": True,
                    "fatura_id": fatura_id,
                    "pix_gerado": True,
                    "codigo_pix": resultado.get('codigo_pix') if resultado else None,
                    "qr_code": resultado.get('qr_code') if resultado else None,
                    "valor": resultado.get('valor') if resultado else None,
                    "dados_completos": resultado
                }
                
            else:
                return {
                    "erro": f"Função {function_name} não implementada",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Erro ao executar função SGP {function_name}: {str(e)}")
            return {
                "erro": f"Erro ao executar {function_name}: {str(e)}",
                "success": False
            }

    def _build_user_prompt(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        user_prompt = f"Mensagem do cliente: {mensagem}"
        if contexto is not None:
            if contexto.get('dados_cliente'):
                user_prompt += f"\n\nDados do cliente: {contexto['dados_cliente']}"
            if contexto.get('historico'):
                user_prompt += f"\n\nHistórico da conversa: {contexto['historico']}"
            if contexto.get('produtos_disponiveis'):
                user_prompt += f"\n\nProdutos disponíveis: {contexto['produtos_disponiveis']}"
        return user_prompt

    async def generate_response(
        self,
        mensagem: str,
        provedor: Provedor,
        contexto: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        try:
            # Atualizar a chave da API de forma assíncrona
            await self.update_api_key_async()
            
            # Verificar se a chave foi configurada
            if not self.api_key:
                logger.error("Chave da API OpenAI não configurada - configure no painel do superadmin")
                return {
                    "success": False,
                    "erro": "Chave da API OpenAI não configurada. Configure no painel do superadmin.",
                    "provedor": provedor.nome
                }
            
            system_prompt = self._build_system_prompt(provedor)
            user_prompt = self._build_user_prompt(mensagem, contexto or {})
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response = await openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            resposta = response.choices[0].message.content.strip()
            logger.info(f"Resposta gerada para provedor {provedor.nome}: {resposta[:100]}...")
            return {
                "success": True,
                "resposta": resposta,
                "model": self.model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "provedor": provedor.nome,
                "agente": provedor.nome_agente_ia
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com OpenAI: {str(e)}")
            return {
                "success": False,
                "erro": f"Erro ao processar mensagem: {str(e)}",
                "provedor": provedor.nome
            }

    def generate_response_sync(
        self,
        mensagem: str,
        provedor: Provedor,
        contexto: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        try:
            # Atualizar a chave da API antes de usar
            self.update_api_key()
            
            # Verificar se a chave foi configurada
            if not self.api_key:
                logger.error("Chave da API OpenAI não configurada - configure no painel do superadmin")
                return {
                    "success": False,
                    "erro": "Chave da API OpenAI não configurada. Configure no painel do superadmin.",
                    "provedor": provedor.nome
                }
            
            # Verificar se já perguntou se é cliente nesta conversa
            conversation = contexto.get('conversation') if contexto else None
            already_asked_if_client = False
            
            if conversation:
                # Verificar se já perguntou se é cliente
                already_asked_if_client = conversation.additional_attributes.get('asked_if_client', False)
                logger.info(f"Conversa {conversation.id}: already_asked_if_client = {already_asked_if_client}")
            else:
                logger.warning("Nenhuma conversa fornecida no contexto")
            
            system_prompt = self._build_system_prompt(provedor)
            
            # Verificar se a mensagem indica necessidade de perguntar se é cliente
            mensagem_lower = mensagem.lower()
            needs_client_check = any(keyword in mensagem_lower for keyword in [
                'boleto', 'fatura', 'conta', 'pagamento', 'débito', 'vencimento',
                'sem internet', 'internet parou', 'não funciona', 'problema', 'chamado', 'reclamação',
                'técnico', 'instalação', 'cancelar', 'mudar plano', 'alterar', 'consulta'
            ])
            
            # Adicionar instrução específica para perguntar se é cliente apenas quando necessário
            if not already_asked_if_client and needs_client_check:
                logger.info("Detectada necessidade de verificar se é cliente - adicionando instrução")
                system_prompt += "\n\nIMPORTANTE: O cliente mencionou algo que requer verificação se ele é cliente (boleto, problemas técnicos, etc). Pergunte educadamente se ele já é cliente antes de prosseguir. Use uma frase como:\n"
                system_prompt += "- 'Para te ajudar melhor, você já é nosso cliente?'\n"
                system_prompt += "- 'Posso confirmar se você já é cliente da [NOME_DA_EMPRESA]?'\n"
                system_prompt += "Seja natural e educado na pergunta."
            elif not already_asked_if_client:
                logger.info("Conversa inicial - respondendo naturalmente sem forçar pergunta sobre ser cliente")
                system_prompt += "\n\nIMPORTANTE: Responda de forma natural e amigável. Se for apenas um cumprimento ou pergunta geral, não pergunte imediatamente se é cliente. Seja acolhedor e pergunte como pode ajudar. Só verifique se é cliente quando ele solicitar algo específico como boletos, suporte técnico, etc."
            else:
                logger.info("Já perguntou se é cliente, prosseguindo normalmente")
            
            user_prompt = self._build_user_prompt(mensagem, contexto or {})
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            # Definir ferramentas SGP que a IA pode chamar (formato atualizado para OpenAI)
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "consultar_cliente_sgp",
                        "description": "Consulta dados reais do cliente no SGP usando CPF/CNPJ",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente (apenas números)"
                                }
                            },
                            "required": ["cpf_cnpj"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "verificar_acesso_sgp",
                        "description": "Verifica status de acesso/conexão de um contrato no SGP",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato"
                                }
                            },
                            "required": ["contrato"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "gerar_fatura_completa",
                        "description": "Gera fatura completa com boleto, PIX, QR code e todos os dados de pagamento",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato"
                                }
                            },
                            "required": ["contrato"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "gerar_pix_qrcode",
                        "description": "Gera PIX e QR code para pagamento de uma fatura específica",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "fatura_id": {
                                    "type": "string",
                                    "description": "ID da fatura para gerar PIX"
                                }
                            },
                            "required": ["fatura_id"]
                        }
                    }
                }
            ]

            # Fazer chamada inicial com ferramentas disponíveis
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                tools=tools,
                tool_choice="auto"
            )
            
            # Processar se a IA chamou alguma ferramenta
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"IA chamou função: {function_name} com argumentos: {function_args}")
                
                # Executar a função chamada pela IA
                function_result = self._execute_sgp_function(provedor, function_name, function_args)
                
                # Adicionar resultado da função à conversa
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": response.choices[0].message.tool_calls
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(function_result, ensure_ascii=False)
                })
                
                # Gerar resposta final com os dados da função
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            resposta = response.choices[0].message.content.strip()
            logger.info(f"Resposta gerada para provedor {provedor.nome}: {resposta[:100]}...")
            
            # Verificar se precisa marcar que perguntou sobre ser cliente
            if not already_asked_if_client and conversation and needs_client_check:
                logger.info("Verificando se a resposta contém pergunta sobre ser cliente")
                # Verificar se a resposta já contém uma pergunta sobre ser cliente
                client_questions = [
                    "já é nosso cliente",
                    "já é cliente",
                    "é nosso cliente",
                    "é cliente da",
                    "você já é cliente",
                    "para te ajudar melhor, você já é",
                    "posso confirmar se você já é"
                ]
                
                resposta_contem_pergunta = any(question in resposta.lower() for question in client_questions)
                logger.info(f"Resposta contém pergunta sobre ser cliente: {resposta_contem_pergunta}")
                
                # Só marcar que perguntou se realmente perguntou
                if resposta_contem_pergunta:
                    conversation.additional_attributes['asked_if_client'] = True
                    conversation.save(update_fields=['additional_attributes'])
                    logger.info(f"Marcado que já perguntou se é cliente para conversa {conversation.id}")
                else:
                    logger.info("Resposta não contém pergunta sobre ser cliente - não marcando como perguntado")
            else:
                if already_asked_if_client:
                    logger.info("Já perguntou se é cliente anteriormente")
                elif not needs_client_check:
                    logger.info("Não foi necessário perguntar se é cliente nesta mensagem")
                if not conversation:
                    logger.warning("Nenhuma conversa fornecida para marcar asked_if_client")
            
            return {
                "success": True,
                "resposta": resposta,
                "model": self.model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "provedor": provedor.nome,
                "agente": provedor.nome_agente_ia
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com OpenAI: {str(e)}")
            return {
                "success": False,
                "erro": f"Erro ao processar mensagem: {str(e)}",
                "provedor": provedor.nome
            }

openai_service = OpenAIService() 
