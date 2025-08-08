"""
Serviço para integração com OpenAI ChatGPT
"""

import os
import openai
import logging
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
        
        # Personalidade (lista)
        personalidade = provedor.personalidade or []
        if not personalidade:
            personalidade = ["Atencioso", "Carismatico", "Educado", "Objetivo", "Persuasivo"]
        
        # Planos de internet
        planos_internet = provedor.planos_internet or ''
        # Modo de falar/sotaque
        modo_falar = provedor.modo_falar or ''
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
            }
        ]
        
        # Usar ferramentas personalizadas se disponíveis, senão usar padrão
        ferramentas = provedor.ferramentas_ia if provedor.ferramentas_ia else ferramentas_padrao
        
        # Regras gerais - usar personalizadas se disponíveis, senão usar padrão
        regras_padrao = [
            f"Responder apenas sobre assuntos relacionados à {nome_provedor}.",
            "Nunca inventar informações. Sempre use 'buscar_documentos' para confirmar dados técnicos ou planos.",
            "Se não souber ou for fora do escopo, diga exatamente: 'Desculpe, não posso te ajudar com isso. Encaminhando para um atendente humano.'",
            "*SEMPRE* Consulte a tool 'GetCpfContato' no contato inicial do cliente para verificar se o CPF já está salvo no contato do ChatWoot antes de solicitar ao cliente.",
            "Sempre que coletar o CPF do cliente, use a ferramenta 'SalvarCpfContato' para salvar o CPF no contato do ChatWoot.",
            "*NUNCA* pergunte 'Você já é cliente?' antes de executar 'GetCpfContato'. A ferramenta DEVE ser a primeira ação do atendimento."
        ]
        
        regras_gerais = provedor.regras_gerais if provedor.regras_gerais else regras_padrao
        
        # Fluxo de atendimento - usar personalizado se disponível, senão usar padrão
        fluxo_padrao = {
            "boas_vindas": {
                "instructions": f"Cumprimente de forma simpática e *IMEDIATAMENTE* após a saudação, execute a tool 'GetCpfContato'. > Se encontrar CPF/CNPJ válido: confirme 'Vejo que você já é cliente!' e siga direto para 'cliente'. > Se não encontrar: pergunte 'Você já é nosso cliente?' > Se sim: peça CPF/CNPJ, salve com 'SalvarCpfContato' e vá para 'cliente'. > Se não: siga para 'nao_cliente'.",
                "example_message": f"👋 Olá! Seja bem-vindo à {nome_provedor}! Eu sou o {nome_agente}. *Verificando seu cadastro...*"
            },
            "cliente": {
                "descricao_geral": f"Fluxo para quem já é cliente da {nome_provedor}.",
                "etapas": [
                    {
                        "etapa": 1,
                        "titulo": "Identificar demanda",
                        "acao_ia": "Perguntar de forma natural o que o cliente deseja resolver ou saber.",
                        "observacao": "Se o cliente ja tiver falado qual a demanda, não pergunte novamente.",
                        "example_message": "😁 Maravilha! Em que posso te ajudar hoje?"
                    },
                    {
                        "etapa": 2,
                        "titulo": "CPF/CNPJ Pré-validado",
                        "acao_ia": "Se o CPF/CNPJ foi obtido via 'GetCpfContato', confirme: 'Seu cadastro já está aqui!'. *Pule a coleta*. Se não tem CPF: peça e salve com 'SalvarCpfContato'."
                    },
                    {
                        "etapa": 3,
                        "titulo": "Validar CPF/CNPJ",
                        "acao_ia": "Utilizar a tool 'validar_cpf' para confirmar os dados e retornar com os contratos do cliente, caso válido."
                    },
                    {
                        "etapa": 4,
                        "titulo": "Confirmar dados",
                        "acao_ia": "Após validar o CPF/CNPJ, confirma os dados para o cliente.",
                        "example_message": "Ótimo! Encontrei seu cadastro. Tudo bem com você *{nome_cliente}* e o número de contrato é *{numero_de_contrato}*. Está tudo certo?",
                        "observacao_1": "Se o cliente tiver mais de um contrato, pergunte qual deles ele deseja tratar.",
                        "observacao_2": "Se o contrato selecionado pelo cliente estiver *ATIVO*, prossiga com o atendimento. Se estiver *SUSPENSO*, informe a ele da situação e ofereça o boleto/pix para pagamento, se estiver cancelado, pergunte se ele deseja reativar o contrato e se ele disser que sim repasse para o atendimento humano usando a tool 'encaminha_financeiro'."
                    },
                    {
                        "etapa": 5,
                        "titulo": "Entender demanda",
                        "acao_ia": "Depois dos dados validados. entenda o que ele deseja. Se o cliente ja estiver falado, não pergunte novamente.",
                        "example_message": "Perfeito! {nome_do_cliente} . Qual é a sua dúvida ou problema? Fatura, suporte técnico ou outro assunto? ",
                        "observacao": "Se o cliente ja estiver falado qual a demanda, não pergunte novamente."
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
                "modo_falar": modo_falar,
                "planos_internet": planos_internet,
                "informacoes_extras": informacoes_extras,
                "taxa_adesao": taxa_adesao,
                "inclusos_plano": inclusos_plano,
                "multa_cancelamento": multa_cancelamento,
                "tipo_conexao": tipo_conexao,
                "prazo_instalacao": prazo_instalacao,
                "documentos_necessarios": documentos_necessarios,
                "observacoes": observacoes,
                "email_contato": email_contato
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
        
        if uso_emojis:
            prompt_dict["emoji_config"] = uso_emojis
            
        print("PROMPT GERADO PARA IA:\n", json.dumps(prompt_dict, ensure_ascii=False, indent=2))
        return json.dumps(prompt_dict, ensure_ascii=False, indent=2)

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
            
            # Adicionar instrução específica para perguntar se é cliente
            if not already_asked_if_client:
                logger.info("Adicionando instrução para perguntar se já é cliente")
                system_prompt += "\n\nIMPORTANTE: Sempre que um cliente enviar uma mensagem pela primeira vez, você DEVE perguntar se ele já é cliente. Use uma das seguintes frases:\n"
                system_prompt += "- 'Você já é nosso cliente?'\n"
                system_prompt += "- 'Antes de continuar, você já é cliente da [NOME_DA_EMPRESA]?'\n"
                system_prompt += "- 'Gostaria de saber se você já é nosso cliente?'\n"
                system_prompt += "SEMPRE faça essa pergunta antes de responder qualquer outra coisa."
            else:
                logger.info("Já perguntou se é cliente, não adicionando instrução")
            
            user_prompt = self._build_user_prompt(mensagem, contexto or {})
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            resposta = response.choices[0].message.content.strip()
            logger.info(f"Resposta gerada para provedor {provedor.nome}: {resposta[:100]}...")
            
            # Se não perguntou ainda e a resposta não contém a pergunta sobre ser cliente, adicionar
            if not already_asked_if_client and conversation:
                logger.info("Verificando se a resposta contém pergunta sobre ser cliente")
                # Verificar se a resposta já contém uma pergunta sobre ser cliente
                client_questions = [
                    "já é nosso cliente",
                    "já é cliente",
                    "é nosso cliente",
                    "é cliente da",
                    "gostaria de saber se você já é"
                ]
                
                resposta_contem_pergunta = any(question in resposta.lower() for question in client_questions)
                logger.info(f"Resposta contém pergunta sobre ser cliente: {resposta_contem_pergunta}")
                
                if not resposta_contem_pergunta:
                    # Adicionar a pergunta no início da resposta
                    nome_empresa = provedor.nome or "nossa empresa"
                    pergunta_cliente = f"Antes de continuar, você já é cliente da {nome_empresa}?\n\n"
                    resposta = pergunta_cliente + resposta
                    logger.info(f"Adicionada pergunta sobre ser cliente: {pergunta_cliente.strip()}")
                
                # Marcar que já perguntou
                conversation.additional_attributes['asked_if_client'] = True
                conversation.save(update_fields=['additional_attributes'])
                logger.info(f"Marcado que já perguntou se é cliente para conversa {conversation.id}")
            else:
                if already_asked_if_client:
                    logger.info("Já perguntou se é cliente anteriormente")
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
