import json, os, tempfile, base64, requests, pickle
from bs4 import BeautifulSoup
from uuid import uuid4
import time
import time
import json
import os
import threading
import re
import pyotp
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

db_lock = threading.Lock()

DB_PATH = os.path.join("dbs", "beta.json")

proxy_url = f"http://user-pias6568569313-region-br-st-minasgerais-city-juizdefora-sessid-brwkuojsop9ztw291-sesstime-90:iXgT3mu1g7o8b@va.proxy.piaproxy.com:5000"
proxies = {
    "http":  proxy_url,
    "https": proxy_url,
}
class TimeoutSession(requests.Session):
    def __init__(self, timeout=None):
        super().__init__()
        self.timeout = timeout

    def request(self, *args, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        return super().request(*args, **kwargs)

        
class Sisreg:
    def __init__(self,user,psw):
        self.user = user
        self.psw = psw
        self.token = None

        self.session = requests.Session()
    
    def Login(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://sisregiii.saude.gov.br',
            'Connection': 'keep-alive',
            'Referer': 'https://sisregiii.saude.gov.br/cgi-bin/index?logout=1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        data = {
            'usuario': self.user,
            'senha': '',
            'senha_256': self.psw,
            'etapa': 'ACESSO',
            'logout': '',
        }

        response = self.session.post('https://sisregiii.saude.gov.br/', headers=headers, data=data)

        if not '<a class="item" href="/cgi-bin/config_perfil" target="f_principal">' in response.text:
            return False
        else:
            self.token = True
            return self.token
    
    def Consulta(self,value):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://sisregiii.saude.gov.br',
            'Connection': 'keep-alive',
            'Referer': 'https://sisregiii.saude.gov.br/cgi-bin/cadweb50?standalone=1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'iframe',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=4',
        }

        params = {
            'standalone': '1',
        }

        data = {
            'nu_cns': value,
            'nome_paciente': '',
            'nome_mae': '',
            'dt_nascimento': '',
            'uf_nasc': '',
            'mun_nasc': '',
            'uf_res': '',
            'mun_res': '',
            'sexo': '',
            'etapa': 'DETALHAR',
            'url': '',
            'standalone': '1',
        }

        response = self.session.post(
            'https://sisregiii.saude.gov.br/cgi-bin/cadweb50',
            params=params,
            headers=headers,
            data=data,
        )
        r = response.text
        
        if 'Falha ao sincronizar dados do usuario.' in r:
            return None
        elif 'foi finalizada pelo servidor. Efetue o logon novamente' in r:
            return False
        elif 'Erro inesperado recuperando dados do banco local.' in r:
            return None
        try:
            soup = BeautifulSoup(response.text,"html.parser")

            soup = soup.find("table",class_='table_listagem')

            def clean(t):
                if t is None:
                    return ""
                return re.sub(r"\s+", " ", t).strip(" :-\n\t")
            dados = {}
            pending_keys = []  # chaves identificadas que aguardam valores

            for tr in soup.find_all("tr"):
                tds = tr.find_all("td")
                if not tds:
                    continue

                # --- Caso a linha contenha CHAVES (usa <b>) ---
                if any(td.find("b") for td in tds):
                    pending_keys = []  # limpa lista
                    for td in tds:
                        if td.find("b"):
                            chave = clean(td.get_text().replace(":", ""))
                            if chave:
                                pending_keys.append(chave)
                    continue  # vai para a próxima linha buscar os valores

                # --- Caso a linha contenha VALORES ---
                if pending_keys:
                    valores = [clean(td.get_text()) for td in tds]
                    for chave, valor in zip(pending_keys, valores):
                        if valor and chave:
                            if 'SEM INFORMA' in valor:
                                valor = None
                            dados[chave] = valor
                    pending_keys = []  # reseta após preencher

            # Remove campos duplicados como "Número"
            # (último prevalece — exatamente como SIPNI mostra)
            limpo = {}
            for chave, valor in dados.items():
                limpo[chave] = valor
            
            if limpo.get("Data de Nascimento"):
                limpo['Data de Nascimento'] = limpo['Data de Nascimento'].split(" ")[0]
            if limpo.get("Telefone(s)"):
                limpo['Telefone(s)'] = limpo['Telefone(s)'].replace("Tipo Telefone DDD Número ", "").strip()
                pass
            if limpo.get("E-mail(s)"):
                limpo['E-mail(s)'] = limpo['E-mail(s)'].replace("Tipo E-mail Validado ", "").strip()
            return limpo
        except:

            return False

class Cadsus:
    def __init__(self, usuario, senha_hash):
        self.usuario = usuario
        self.senha_hash = senha_hash
        self.session = TimeoutSession(timeout=20)
        self.session.proxies.update(proxies)
        self.token = None
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Origin': 'https://sipni.datasus.gov.br',
        }
        self.headers_html = {
            **self.base_headers,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }
        self.headers_ajax = {
            **self.base_headers,
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Faces-Request': 'partial/ajax',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
        }

    def Login(self):
        """ Realiza o login no SIPNI """
        response = self.session.get(
            'https://sipni.datasus.gov.br/si-pni-web/faces/paciente/manterPaciente.jsf',
            headers=self.headers_html,
            verify=False
        )
        r = response.text
        j_idt23, j_idt35 = r.split('<td><button id="')[1].split('"')[0].split(":")
        viewstate = r.split('javax.faces.ViewState" value="')[1].split('"')[0]

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': f'{j_idt23}:{j_idt35}',
            'javax.faces.partial.execute': f'{j_idt23}:{j_idt35}',
            'javax.faces.behavior.event': 'click',
            'javax.faces.partial.event': 'click',
            j_idt23: j_idt23,
            'javax.faces.ViewState': viewstate,
            f'{j_idt23}:usuario': self.usuario,
            f'{j_idt23}:senha': self.senha_hash,
        }
        response = self.session.post(
            'https://sipni.datasus.gov.br/si-pni-web/faces/inicio.jsf',
            headers=self.headers_ajax,
            data=data,
            verify=False
        )

        vs = response.text.split('"><![CDATA[')[1].split(']]><')[0]

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': f'{j_idt23}:{j_idt35}',
            'javax.faces.partial.execute': '@all',
            f'{j_idt23}:{j_idt35}': f'{j_idt23}:{j_idt35}',
            j_idt23: j_idt23,
            'javax.faces.ViewState': vs,
            f'{j_idt23}:usuario': self.usuario,
            f'{j_idt23}:senha': self.senha_hash,
        }
        self.session.post(
            'https://sipni.datasus.gov.br/si-pni-web/faces/inicio.jsf',
            headers=self.headers_ajax,
            data=data,
            verify=False
        )
        if 'summary:"Usuário ou senha incorreto!",detail:"' in response.text:
            return False
        else: 
            self.token = True
            return self.token

    def Consulta(self, form):
        info = {
            'dialogPesquisarPacienteWSCadsusForm:numeroCartao': '',
            'dialogPesquisarPacienteWSCadsusForm:nomePaciente': '',
            'dialogPesquisarPacienteWSCadsusForm:nomeSocial': '',
            'dialogPesquisarPacienteWSCadsusForm:nomeMaePaciente': '',
            'dialogPesquisarPacienteWSCadsusForm:nomePaiPaciente': '',
            'dialogPesquisarPacienteWSCadsusForm:dataNascimento_input': '',
            'dialogPesquisarPacienteWSCadsusForm:uf_input': '',
            'dialogPesquisarPacienteWSCadsusForm:uf_focus': '',
            'dialogPesquisarPacienteWSCadsusForm:tipoDocumento_input': '',
            'dialogPesquisarPacienteWSCadsusForm:tipoDocumento_focus': '',
            'dialogPesquisarPacienteWSCadsusForm:documento': '',
        }
        
        mapa = {
            "nome": "nomePaciente",
            "nome_mãe": "nomeMaePaciente",
            "data_de_nascimento": "dataNascimento_input",
        }
        
        if form.get("cpf"):
            info['dialogPesquisarPacienteWSCadsusForm:tipoDocumento_input'] = '1'
            info['dialogPesquisarPacienteWSCadsusForm:documento'] = form['cpf']
        elif form.get("cns"):
            info['dialogPesquisarPacienteWSCadsusForm:numeroCartao'] = form['cns']
        else:
            for campo, valor in form.items():
                if valor: 
                    nome_campo_info = mapa[campo]
                    chave_info = f"dialogPesquisarPacienteWSCadsusForm:{nome_campo_info}"
                    info[chave_info] = valor
        
        response = self.session.get(
            'https://sipni.datasus.gov.br/si-pni-web/faces/paciente/manterPaciente.jsf',
            headers=self.headers_html,
            verify=False
        )
        viewstate = response.text.split('javax.faces.ViewState" value="')[1].split('"')[0]


        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'selectPaciente',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'idDialogPesquisarPacienteWSCadsus',
            'selectPaciente': 'selectPaciente',
            'manterPacienteForm': 'manterPacienteForm',
            'javax.faces.ViewState': viewstate,
            'zona': 'U',
            'tipoSaidaPaciente_input': '',
            'tipoSaidaPaciente_focus': '',
        }
        response = self.session.post(
            'https://sipni.datasus.gov.br/si-pni-web/faces/paciente/manterPaciente.jsf',
            headers=self.headers_ajax,
            data=data,
            verify=False
        )
        try:
            vs = response.text.split('"><![CDATA[')[2].split(']]><')[0]
            j_idt235 = response.text.split(
                '<td class="colunaLabel200px"><button id="dialogPesquisarPacienteWSCadsusForm:'
            )[1].split('"')[0]
        except: return False

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable',
            'javax.faces.partial.execute': 'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable',
            'javax.faces.partial.render': 'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable': 'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable_pagination': 'true',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable_first': '0',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable_rows': '1000',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable_encodeFeature': 'true',
            'dialogPesquisarPacienteWSCadsusForm': 'dialogPesquisarPacienteWSCadsusForm',
            'dialogPesquisarPacienteWSCadsusForm:numeroCartao': '',
            'dialogPesquisarPacienteWSCadsusForm:nomePaciente': '',
            'dialogPesquisarPacienteWSCadsusForm:nomeSocial': '',
            'dialogPesquisarPacienteWSCadsusForm:nomeMaePaciente': '',
            'dialogPesquisarPacienteWSCadsusForm:nomePaiPaciente': '',
            'dialogPesquisarPacienteWSCadsusForm:dataNascimento_input': '',
            'dialogPesquisarPacienteWSCadsusForm:uf_input': '',
            'dialogPesquisarPacienteWSCadsusForm:uf_focus': '',
            'dialogPesquisarPacienteWSCadsusForm:tipoDocumento_input': '',
            'dialogPesquisarPacienteWSCadsusForm:tipoDocumento_focus': '',
            'dialogPesquisarPacienteWSCadsusForm:documento': '',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable_selection': '',
            'javax.faces.ViewState': vs,
        }

        response = self.session.post(
            'https://sipni.datasus.gov.br/si-pni-web/faces/paciente/manterPaciente.jsf',
            headers=self.headers_ajax,
            data=data,
            verify=False
        )

        vs = response.text.split('"><![CDATA[')[2].split(']]><')[0]


        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': f'dialogPesquisarPacienteWSCadsusForm:{j_idt235}',
            'javax.faces.partial.execute': 'dialogPesquisarPacienteWSCadsusForm',
            'javax.faces.partial.render': 'dialogPesquisarPacienteWSCadsusForm errorMessage',
            f'dialogPesquisarPacienteWSCadsusForm:{j_idt235}': f'dialogPesquisarPacienteWSCadsusForm:{j_idt235}',
            'dialogPesquisarPacienteWSCadsusForm': 'dialogPesquisarPacienteWSCadsusForm',
            'dialogPesquisarPacienteWSCadsusForm:dialogPesquisarPacienteWSCadsusListTable_selection': '',
            'javax.faces.ViewState': vs,
        }
        data.update(info)
        response = self.session.post(
            'https://sipni.datasus.gov.br/si-pni-web/faces/paciente/manterPaciente.jsf',
            headers=self.headers_ajax,
            data=data,
            verify=False
        )
        if 'Nenhum Paciente Encontrado !' in response.text:
            return None
        html = response.text.split('</span></span></th></tr></thead><tfoot></tfoot>')[1].split('</table></div><div id=')[0]

        soup = BeautifulSoup(html, 'html.parser')

        data = []

        rows = soup.select('tbody#dialogPesquisarPacienteWSCadsusForm\\:dialogPesquisarPacienteWSCadsusListTable_data tr')

        for row in rows:
            cols = row.find_all('td')
            cols_text = [col.text.strip() for col in cols]
            _,cns, nome_completo, nome_social, nome_mae, nome_pai, municipio,data_nascimento, sexo = cols_text
            if municipio == "":
                cidade,uf = None,None
            else:
                cidade, uf = municipio.split(" / ")

            dados = {
                "cns": cns,
                "nome_completo": nome_completo,
                "nome_social": nome_social,
                "nome_mae": nome_mae,
                "nome_pai": nome_pai,
                "municipio": cidade,
                "uf": uf,
                "data_nascimento": data_nascimento,
                "sexo": sexo
            }
            for key in dados.keys():
                if (dados[key]) in ['SEM INFORMAÇÃO','',' ']:
                    dados[key] = None
            data.append(dados)
        
        if not len(data) == 1:
            return data 

        data = data[0]
        cns = data['cns']
        extra = consult_generic(Sisreg,'sisreg',cns)
        if extra:
            data.update(extra)
        else:
            return data

        # NORMALIZAR CHAVES
        def normalize_key(key):
            return (
                key.lower()
                .replace(" ", "_")
                .replace("ã", "a")
                .replace("á", "a")
                .replace("â", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ô", "o")
                .replace("ú", "u")
                .replace("ç", "c")
                .replace("(", "")
                .replace(")", "")
            )

        data = { normalize_key(k): v for k, v in data.items() }

        # MAPA DE CAMPOS
        pessoa_map = {
            "Identificação": [
                "nome_completo",
                "nome_social",
                "sexo",
                "raca",
                "nacionalidade",
                "data_nascimento",
                "cns",
                "cpf",
            ],

            "Filiação": [
                "nome_mae",
                "nome_pai",
            ],

            "Endereço": [
                "tipo_logradouro",
                "logradouro",
                "bairro",
                "municipio",
                "uf",
                "cep",
                "pais_residencia",
            ],

            "Contato": [
                "telefones",
            ],
        }

        resultado = {}

        for secao, campos in pessoa_map.items():
            resultado[secao] = {}
            for campo in campos:
                if campo in data and data[campo] not in (None, "", "null"):
                    resultado[secao][campo] = data[campo]

        return resultado

class Checkonn:
    def __init__(self,user,psw):
        self.user = user
        self.psw = psw
        self.session = requests.Session()
        self.token = None

    def Login(self):

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        response = self.session.get('https://appbuscacheckonn.com/login.aspx?ReturnUrl=%2f', headers=headers)
        r = response.text
        
        vs = r.split('id="__VIEWSTATE" value="')[1].split('"')[0]
        vg = r.split('id="__VIEWSTATEGENERATOR" value="')[1].split('"')[0]
        event = r.split('id="__EVENTVALIDATION" value="')[1].split('"')[0]

        data = {
            '__EVENTTARGET': 'ctl00$body$sdIN',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': vs,
            '__VIEWSTATEGENERATOR': vg,
            '__EVENTVALIDATION': event,
            'ctl00$ipHidden': '',
            'ctl00$body$user': self.user,
            'ctl00$body$password': self.psw,
        }

        response = self.session.post('https://appbuscacheckonn.com/login.aspx?ReturnUrl=%2f', headers=headers, data=data)

        if not 'Trocar a senha' in response.text:
            return(False)
        else:
            
            return True

    def Consulta(self,cpf):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://appbuscacheckonn.com/login.aspx?ReturnUrl=%2f',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        response = self.session.get('https://appbuscacheckonn.com/consultas/consultacpf.aspx',  headers=headers)

        r = response.text
        vs = r.split('id="__VIEWSTATE" value="')[1].split('"')[0]
        vg = r.split('id="__VIEWSTATEGENERATOR" value="')[1].split('"')[0]
        event = r.split('id="__EVENTVALIDATION" value="')[1].split('"')[0]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://appbuscacheckonn.com',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://appbuscacheckonn.com/consultas/consultacpf.aspx',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': vs,
            '__VIEWSTATEGENERATOR': vg,
            '__EVENTVALIDATION': event,
            'ctl00$ctl00$subject': '',
            'ctl00$ctl00$comment': '',
            'ctl00$ctl00$TextBox1': '',
            'ctl00$ctl00$tbCurrPass': '',
            'ctl00$ctl00$tbNewPass': '',
            'ctl00$ctl00$tbNewPass2': '',
            'ctl00$ctl00$MainContent$hf_confirm': '',
            'ctl00$ctl00$MainContent$ddlTipoConsulta': 'Auto',
            'ctl00$ctl00$MainContent$tbParametro': '',
            'ctl00$ctl00$MainContent$tbCPF': cpf,
            'ctl00$ctl00$MainContent$tbCNPJ': '',
            'ctl00$ctl00$MainContent$tbNome': '',
            'ctl00$ctl00$MainContent$tbDataNasc': '',
            'ctl00$ctl00$MainContent$tbEndereco': '',
            'ctl00$ctl00$MainContent$tbBairro': '',
            'ctl00$ctl00$MainContent$tbCidade': '',
            'ctl00$ctl00$MainContent$tbUF': '',
            'ctl00$ctl00$MainContent$tbTelefone': '',
            'ctl00$ctl00$MainContent$tbPlaca': '',
            'ctl00$ctl00$MainContent$tbEmail': '',
            'ctl00$ctl00$MainContent$btnConsultar': 'Consultar',
            'ctl00$ctl00$MainContent$ConsultaContent$celular': '',
            'ctl00$ctl00$MainContent$ConsultaContent$taMensagemLivre': '',
        }

        response = self.session.post('https://appbuscacheckonn.com/consultas/consultacpf.aspx',  headers=headers, data=data)

        if '">Esqueci a senha</a>' in response:
            return False

        html = response.text
        if ' - não localizado' in html: return None

        soup = BeautifulSoup(html,'html.parser')

        retorno = {}

        soup = soup.find("div",class_='container-consulta-resultado border')


        # CADASTRO BASICO
        cad_box = soup.find("div",id='MainContent_ConsultaContent_pnlDadosCadastrais')
        cad_box = cad_box.find("div",class_='container')

        for line in cad_box.find_all("div",class_='row'):
            keys =   [k.get_text().lower().replace(":",'').replace(" ",'_') for k in line.find_all('label')]
            values = [k.get_text() for k in line.find_all('span')]

            retorno.update(dict(zip(keys,values)))

        # TELEFONE 
        tel_box = soup.find("div",id='MainContent_ConsultaContent_pnlTelefones')

        numeros = []
        for telefone in tel_box.find_all("a"):
            numero = telefone.get("href").split("tel:")[1]
            numeros.append(numero)
        retorno['telefones'] = numeros

        # EMAIL
        """
        email_box = soup.find("div",id='MainContent_ConsultaContent_pnlEmails')

        emails = []
        for email in email_box.find_all("span"):
            emails.append(email.get_text())

        retorno['emails'] = emails
        """

        # ENDERECO

        enderecos_box = soup.find("div",id='MainContent_ConsultaContent_pnlEnderecos')

        keys = enderecos_box.find_all("label",class_='label3')
        keys = [k.get_text().lower().replace(":",'').replace(" ",'_') for k in keys]


        enderecos = []
        for line in enderecos_box.find_all('tr'):
            values = [v.get_text() for v in line.find_all("span",class_='text3')]
            
            endereco = dict(zip(keys,values))
            if endereco:
                if "mapa" in endereco and not endereco["mapa"]:
                    endereco.pop("mapa")
                enderecos.append(endereco)

        retorno['enderecos'] = enderecos


        # RENDA
        renda_box = soup.find("div", id='MainContent_ConsultaContent_pnlRenda')
        if renda_box:
            for line in renda_box.find_all("div", class_='row'):
                keys = [k.get_text().strip().lower().replace(":", "").replace(" ", "_") 
                        for k in line.find_all('label')]
                values = [v.get_text().strip() for v in line.find_all('span')]
                retorno.update(dict(zip(keys, values)))
        return retorno

class Receita:
    def __init__(self,user,psw):
        self.user= user
        self.psw = psw
        
        self.session = requests.Session()

        self.token = None
        
    def Login(self):
        headers = {
            'Host': 'www.epge.go.gov.br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.epge.go.gov.br',
            'Referer': 'https://www.epge.go.gov.br/ppg/login.jsp',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
        }

        json_data = {
            'cpf': self.user,
            'senha': self.psw,
        }

        response = self.session.post('https://www.epge.go.gov.br/ppg/rest/auth/redirect', headers=headers, json=json_data)

        try:
            if response.text =='':
                return(False)

            r = response.json()

            if r.get("hostRedirectLoginSuccess"):
                token = r['hostRedirectLoginSuccess'].split("token=")[1]
            else:
                return(False)
        except:
            return False

        headers = {
            'Host': 'www.epge.go.gov.br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Authorization': f'Bearer {token}',
            'codg-divisao': '3',
            'Referer': 'https://www.epge.go.gov.br/ppg/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        response = self.session.get(
            'https://www.epge.go.gov.br/ppg/rest/sistemas/buscar-arvore-sistema-ativo-por-usuario-divisao/8/709/3',
            headers=headers,
        )
        try:
            r = response.json()
            if r.get("token"):
                token = r['token']
                self.token = token
                return token
            else:
                return(False)
        except:
            return False

    def Consulta(self,valor):
        if not self.token:
            return False
        
        valor = re.sub(r'\D', '', valor)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'auditoria': valor,
            'Authorization': f'Bearer {self.token}',
            'codg-divisao': '3',
            'Connection': 'keep-alive',
            'Referer': 'https://www.epge.go.gov.br/gcp/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
        }

        response = self.session.get(f'https://www.epge.go.gov.br/gcp/rest/consulta-receita/{valor}',  headers=headers)
        try:
            r = response.json()
            if len(r) > 0:
                dados = r[0]
            else:
                return None
        except:
            return False
        cpf = {
            "Dados Pessoa Física": [
                "nome", "nomeMae", "cpf", "dataNascimento", "sexo",
                "estrangeiro", "residenteExterior", "situacaoCadastral",
                "ocupacaoPrincipal", "exercicioOcupacao", "naturezaOcupacao",
                "anoObito"
            ],
            "Endereço": [
                "tipoLogradouro", "logradouro", "numeroLogradouro", "complemento",
                "bairro", "municipio", "cep", "uf", "codigoMunicipio", "codigoPaisExterior"
            ]
        }

        cnpj = {
            "Dados da Empresa": [
                "cnpj", "nomeEmpresarial", "nomeFantasia", "naturezaJuridica",
                "dataAbertura", "cnaePrincipal", "cnaeSecundario", "capitalSocial",
                "porte", "estabelecimento"
            ],
            "Endereço": [
                "tipoLogradouro", "logradouro", "numeroLogradouro", "complemento",
                "bairro", "nomeMunicipio", "codigoMunicipio", "cep", "uf"
            ],
            "Cadastro": [
                "situacaoCadastral", "dataSituacaoCadastral", "opcaoSimples",
                "telefone1", "telefone2", "email", "cpfResponsavel", "nomeResponsavel"
            ],
            "Socios": [
                "socios"
            ]
        }
        
        if len(valor) > 11:
            secoes = cnpj
        else:
            secoes = cpf

        resultado = {}
        for secao, campos in secoes.items():
            resultado[secao] = {}
            for campo in campos:
                if campo in dados:
                    # converte camelCase para snake_case
                    chave_snake = re.sub(r'([a-z])([A-Z])', r'\1_\2', campo)
                    resultado[secao][chave_snake] = dados[campo]

        if resultado.get("Socios"):
            socios = [f"{socio['nome']} | {socio['numero']}"for socio in resultado['Socios']['socios']]
            resultado['Socios'] = socios
        return resultado

class Parana:  # FOTO PR / VEICULO NACIONAL (CHASSI SEM PLACA)
    def __init__(self, user, psw, session=None):
        if "|Midia|" in user:
            self.user, self.hard = user.split("|Midia|")
        else:
            self.user, self.hard = user, ""
        self.psw = psw
        self.token = None
        self.session = session or requests.Session()
        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'usuario': 'SESP-MOBILE',
            'senha': 'hYS&*f4!l0J',
            'idHardware': self.hard,
            'latitude': '0.0',
            'longitude': '0.0',
            'precisao': '0.0',
            'Host': 'redebio.pr.gov.br',
        }

    def Login(self):
        try:
            response = self.session.post(
                'https://redebio.pr.gov.br/sespintegracao/jws/login',
                headers=self.headers,
                json={'usuario': self.user, 'senha': self.psw},
                timeout=15
            )
            r = response.json()
            token = r.get("token")
            if token:
                hard = r.get('idHardware', '')
                self.token = f"{token}|Midia|{hard}"
                return self.token
            return False
        except Exception:
            return False

    def Consulta(self, form):
        veiculo = {
            "placa": "",
            "chassi": "",
            "renavam": "",
            "motor": "",
            "proprietario": "",
            "cpf": "",
            "cnpj": ""
        }

        condutor = {
            "nome": "",
            "rg": "",
            "cpf": "",
            "cnh": "",
            "tipoCondutor": 2
        }

        # Identifica se a consulta é pessoa ou veículo
        pessoa = True if form.get("cpf") or form.get("cnh") else False
        json_data = condutor.copy() if pessoa else veiculo.copy()

        # Preenche apenas os campos existentes no modelo escolhido
        for campo, valor in form.items():
            if valor and campo in json_data:
                json_data[campo] = valor

        # Precisa estar logado
        if not self.token:
            return False

        tk, id_hard = self.token.split("|Midia|")

        headers2 = {
            **self.headers,
            'token': tk,
            'idHardware': id_hard,
            'latitude': '0.0',
            'longitude': '0.0',
            'precisao': '0.0',
        }

        # Limpeza somente no modo pessoa
        if pessoa:
            campos_numericos = ["cpf", "cnh", "rg"]
            for campo in campos_numericos:
                if campo in json_data and json_data[campo]:
                    json_data[campo] = re.sub(r'\D', '', json_data[campo])

            url = 'https://redebio.pr.gov.br/sespintegracao/jws/Condutor/Listar'
        else:
            url = 'https://redebio.pr.gov.br/sespintegracao/jws/Veiculo/Listar'

        resp1 = self.session.post(
            url=url,headers=headers2, json=json_data, timeout=20
        )
        r1 = resp1.json()

        if r1.get('msgErro') == 'O USUARIO NAO ESTA LOGADO.':
            return False
        if r1.get('codRetorno') == 99:
            return None
        retorno = r1.get("retorno")
        if not retorno:
            return False

        exclude = ('codRetorno','descricao','totalRegistros','registros','tipoCondutor','cpf','tipoDocumento','documento')


        if pessoa == False:
            dados = retorno[0]
            for fld in exclude:
                dados.pop(fld, None)
            return dados

        dados = retorno[0]
        for fld in exclude:
            dados.pop(fld, None)

        resp2 = self.session.get(
            'https://redebio.pr.gov.br/sespintegracao/jws/Imagem/Listar',
            params={'rg': dados.get('rg', '')},
            headers=headers2,
            timeout=15
        )
        r2 = resp2.json()
        if isinstance(r2, list) and len(r2) > 0:
            foto = r2[-1]
            dados['foto'] = foto['imagem']

            """
            
            for fld in ('codigoIndividuo','sequencial'):
                foto.pop(fld, None)
            dados['foto'] = foto
            """
        else:
            dados['foto'] = None

        cnh = {
            "Dados Pessoais": [
                "nome", "nomeMae", "nomePai", "sexo",
                "dataNascimento", "nacionalidade", "naturalidade","foto"
            ],
            "Documento": [
                "rg", "ufDocumento", "numeroCedula", "cnh",
                "categoria", "situacaoCNH", "dataValidade", "cargasPerigosas",
                "listaObservacaoCNH"
            ],
            "Localidade": [
                "municipio", "residencia", "ciretran"
            ],


        }

        resultado = {}

        for secao, campos in cnh.items():
            resultado[secao] = {}
            for campo in campos:
                if campo in dados:
                    resultado[secao][campo] = dados[campo]

        return resultado

class Pernanbuco:
    def __init__(self, user, psw, session=None):
        # espera user no formato "usuario|Midia|chave"
        if "|Midia|" in user:
            self.user, self.chave,self.base = user.split("|Midia|")
        else:
            self.user, self.chave = user, ""
        self.psw = psw
        self.token = None
        self.session = session or requests.Session()

        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://policiaagil.sds.pe.gov.br',
            'Referer': 'https://policiaagil.sds.pe.gov.br/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        }

    def Login(self):
        try:
            codigo = pyotp.TOTP(self.chave).now()
            json_data = {
                'USUARIO': self.user,
                'SENHA': self.psw,
                'BASE': self.base,
                'SISTEMA': 'policiaagil-web',
                'IP': '',
                'OTP': codigo,
            }
            resp = self.session.post(
                'https://auth-bids.apps.ocp-server.ati.pe.gov.br/login',
                headers=self.headers,
                json=json_data
            )
            
            text = resp.text
            if "Usuário ou Senha inválidos!" in text:
                return False
            token = resp.json().get('token')
            if not token:
                return False
            self.token = token
            return self.token
        except Exception:
            return False

    def Consulta(self, form):
        if not self.token:
            return False
        
        
        map = {
            "cpf":"https://abis-gti.apps.ocp-server.ati.pe.gov.br/wsCivil/BuscarCidadaoPorCPF/{}",
            "placa":"https://api-detran-gti.apps.ocp-server.ati.pe.gov.br/buscarPlaca/{}",
            "chassi":"https://api-detran-gti.apps.ocp-server.ati.pe.gov.br/buscarChassi/{}"
        }

        pessoa = False
        for key,valor in form.items():
            valor = form[key]
            if valor:
                if key == 'cpf':
                    pessoa = True
                valor = re.sub(r'[^a-zA-Z0-9]', '', valor)
                url = map[key].format(valor)

        headers = {**self.headers, 'Authorization': f'Bearer {self.token}'}
        resp1 = self.session.get(
            url,
            headers=headers
        )
        if '"message"' in resp1.text:
            return False
        if resp1.text.strip() == '"A Busca não encontrou resultados"':
            return None
        elif 'DUPLICIDADE DE CHASSI NA BIN' in resp1.text:
            return None

        info = resp1.json()
        if pessoa is False:

            # mover debitos para o root
            if "debitos" in info:
                for k, v in info["debitos"].items():
                    info[k] = v

            veiculo_map = {
                "Veículo": [
                    "Situacao", "Placa", "Chassi", "Renavam", "CRV",
                    "TipoVeic", "Categoria", "Combustivel",
                    "Marca", "Cor",
                    "AnoFabricacao", "AnoModelo",
                    "UFPlaca", "Municipio", "Bairro", "Logradouro",
                    "NumCaixa", "CEP"
                ],

                "Proprietário": [
                    "Nome", "CPFCGC"
                ],

                "Impostos": [
                    "valorLicenciamento", "valorIpva",
                    "ipvaUnica", "parcelaIpva",
                    "valorMulta", "valorBombeiros"
                ],
            }

            # Mapeamento de nomes bonitos
            nome_campos = {
                "Situacao": "Situação",
                "Placa": "Placa",
                "Chassi": "Chassi",
                "Renavam": "Renavam",
                "CRV": "CRV",
                "TipoVeic": "Tipo",
                "Categoria": "Categoria",
                "Combustivel": "Combustível",
                "Marca": "Marca / Modelo",
                "Cor": "Cor",
                "AnoFabricacao": "Ano de fabricação",
                "AnoModelo": "Ano modelo",
                "UFPlaca": "UF",
                "Municipio": "Município",
                "Bairro": "Bairro",
                "Logradouro": "Logradouro",
                "NumCaixa": "Complemento",
                "CEP": "CEP",
                "Nome": "Nome do proprietário",
                "CPFCGC": "CPF do proprietário",

                "valorLicenciamento": "Licenciamento (R$)",
                "valorIpva": "Valor IPVA SEFAZ (R$)",
                "ipvaUnica": "Valor IPVA único (R$)",
                "parcelaIpva": "Valor IPVA parcelas (R$)",
                "valorMulta": "Valor multas (R$)",
                "valorBombeiros": "Bombeiro (R$)"
            }

            resultado = {}

            for secao, campos in veiculo_map.items():
                resultado[secao] = {}
                for campo in campos:
                    if campo in info:

                        # valor convertido
                        valor_original = info[campo]
                        if valor_original in (None, "", "null"):
                            valor_original = "Não informado"

                        # usa nome bonitinho
                        nome_bonito = nome_campos.get(campo, campo)

                        resultado[secao][nome_bonito] = valor_original

            return resultado
        info = info[0]
        pessoa = info.pop("NumeroPessoa", None)
        info.pop("NumeroPedido", None)

        # obter foto
        headers2 = {**headers,
            'key': 'Pamela.intranet.sds.pe.gov.br',
            'senha': '11TB#idnet%2020',
            'usuario': 'GTIWSUSER'
        }
        resp2 = self.session.get(
            f'https://abis-gti.apps.ocp-server.ati.pe.gov.br/wsCivil/ObterFoto3x4/{pessoa}',
            headers=headers2
        )
        foto = resp2.text.replace('"','')
        if foto == 'A busca não retornou Resultados':
            foto = None
        info['foto'] = foto
        return info

class DetranRO:
    def __init__(self,user,psw):
        self.session = requests.Session()
        self.token = None
        self.user = user
        self.psw = psw

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Connection': 'keep-alive',
        }

    def Login(self):
        
        response = self.session.get('https://servicosadm.detran.ro.gov.br/', headers=self.headers)
        token = response.text.split('__RequestVerificationToken" type="hidden" value="')[1].split('"')[0]


        data = {
            'Latitude': '',
            'Longitude': '',
            'ReturnUrl': '',
            'login': self.user,
            'senha':self.psw,
            '__RequestVerificationToken': token,
        }

        response = self.session.post('https://servicosadm.detran.ro.gov.br/Login/Post', headers=self.headers, data=data)

        if not '<i class="material-icons">keyboard_tab</i> Logout' in response.text:
            return(False)
        else:
            self.token = True
            return self.token

    def Consulta(self,form):

        entrys = {
            "cpf":"1",
            "renach":"2",
            "registro":"3"
        }
        for key,valor in form.items():
            valor = form[key]
            if valor:
                tipo = entrys[key]


        params = {
            'tipo': tipo,
            'termo': valor,
        }
        response = self.session.get(
            'https://servicosadm.detran.ro.gov.br/Policia/ConsultarCNH',
            params=params,
            headers=self.headers,
        )
        html = response.text
        if 'o foi possivel detalhar a CNH tente novamente mais tarde!' in html:
            return(None)

        retorno = {}

        soup = BeautifulSoup(html,"html.parser")

        box = soup.find("div",class_='card-content black-text')

        img = box.find("img",class_='responsive-img center-align').get("src")
        retorno['img'] = img
        dados = box.find("div",class_='row')


        for line in dados.find_all("input",class_='uppercase negrito'):
            key = line.get("id")
            value = line.get("value")

            retorno[key] = value

        return(retorno)

class CNH1:
    def __init__(self,user,psw):
        self.user = user
        self.psw = psw
        self.session = requests.Session()
        self.token = None

    def Login(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        response = self.session.get('https://www.habilitacao.detran.pr.gov.br/detran-habilitacao/', headers=headers,allow_redirects=False)
        url = (response.headers['Location'])
        state = url.split("&state=")[1]
        client = url.split('client_id=')[1].split("&")[0]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        response = self.session.get(
            url,
            headers=headers,
        )


        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://auth-cs.identidadedigital.pr.gov.br/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://auth-cs.identidadedigital.pr.gov.br',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        data = {
            'paginaLogin': '',
            'provedorselecionado': 'tabCentral',
            'origemRequisicao': '',
            'valorCPF': '',
            'urlLogo': 'https://web.celepar.pr.gov.br/drupal/images/detran/logo_detran_250x71.png',
            'loginPadrao': 'btnCentral',
            'modulosDeAutenticacao': 'btnGovbr,btnCertificado,btnCpf,btnEmail,btnCentral',
            'labelCentral': 'CPF,E-Mail',
            'moduloAtual': '',
            'dataAcesso': '2090',
            'exibirLinkAutoCadastro': 'true',
            'exibirLinkAutoCadastroCertificado': 'true',
            'exibirLinkRecuperarSenha': 'true',
            'formaAutenticacao': 'btnCpf',
            'response_type': 'code',
            'client_id': client,
            'redirect_uri': 'https%3A%2F%2Fwww.habilitacao.detran.pr.gov.br%2Fdetran-habilitacao',
            'scope': '',
            'state': state,
            'mensagem': '',
            'dnsCidadao': 'https://cidadao-cs.identidadedigital.pr.gov.br/centralcidadao',
            'provedores': '',
            'provedor': 'tabCentral',
            'tokenFormat': 'jwt',
            'code_challenge': '',
            'code_challenge_method': '',
            'captcha': 'false',
            'codCaptcha': '',
            'attribute': self.user,
            'attribute_central': self.user,
            'password': self.psw,
            'captchaCentral': '',
            'attribute_Sms': '',
            'celular': '',
            'captchaSms': '',
            'codigoSeguranca': '',
            'attribute_token': '',
            'codigoOTP': '',
            'attribute_expresso': '',
            'password_expresso': '',
            'captchaExpresso': '',
            'attribute_emailToken': '',
            'email': '',
            'captchaEmailToken': '',
            'codigoSegurancaEmail': '',
        }

        response = self.session.post(
            'https://auth-cs.identidadedigital.pr.gov.br/centralautenticacao/api/v1/authorize/jwt',
            headers=headers,
            data=data,
        )
        if not '<td valign="top">Tipo de Operador:' in response.text: 
            return(False)
        else:
            self.token = True
            return True

    def Consulta(self,form):
        if not self.token: return False
        for key,valor in form.items():
            valor = form[key]
            if valor:
                valor = re.sub(r'\D', '', valor)
                if key == "cpf":
                    data = {
                    'opcaoConsulta': '7',
                    'numCpf': valor,
                    }
                elif key == 'cnh':
                    data = {
                    'dataAgora': '',
                    'opcaoBusca': '2',
                    'numRegistroCNH': valor,
                    }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.habilitacao.detran.pr.gov.br',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.habilitacao.detran.pr.gov.br/detran-habilitacao/consultaTr555.do?action=iniciarProcesso',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        params = {
            'action': 'consultaBINCO',
        }

        response = self.session.post(
            'https://www.habilitacao.detran.pr.gov.br/detran-habilitacao/consultaTr555.do',
            params=params,
            headers=headers,
            data=data,
        )
        html = response.text

        if 'Nenhum registro localizado na BINCO nem no impedimento' in html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            j = soup.find("form", attrs={"name": "consultaTr555Form"})

            tabelas = j.find_all("table",class_='form_tabela')


            info = {}
            for tabela in tabelas[:4]:
                tds = tabela.find_all("td")
                dados = {}

                i = 0
                while i < len(tds):
                    if tds[i].find("b"):
                        key = tds[i].get_text(strip=True).replace(" ", "_")
                        if i + 1 < len(tds):
                            value = tds[i + 1].get_text(strip=True)
                            dados[key] = value
                    i += 1

                info.update(dados)


            cnh_map = {
                "Identificação": [
                    "Nome",
                    "Nome_Social",
                    "Nome_Mãe",
                    "Sexo",
                    "Data_Nascimento",
                    "Município_Nascimento",
                ],

                "Documento": [
                    "Tipo_Documento",
                    "Cédula",
                    "Num._Documento",
                    "Órgão_Expedidor",
                    "UF_Órgão",
                ],

                "CNH": [
                    "CPF",
                    "Categoria",
                    "Situação_CNH",
                    "Primeira_Hab.",
                    "Validade",
                    "Registro_CNH",
                    "PGU_Antigo",
                    "Número_Processo",
                    "Motivos",
                    "Observações_CNH",
                    "Outras_Adaptações",
                    "Cód._Última_Transação",
                    "Data_Última_Atualização",
                ],

                "UFs": [
                    "UF_Hab._Atual",
                    "UF_Solicitante",
                    "UF_Domínio",
                ]
            }
            resultado = {}

            for secao, campos in cnh_map.items():
                resultado[secao] = {}
                for campo in campos:
                    if campo in info:
                        resultado[secao][campo] = info[campo]

            return resultado

        except:
            return False

class ChavePix:
    def __init__(self,user,psw):
        try:
            user1,self.user = user.split(":")
            psw1,self.psw = psw.split(":")
        except:
            self.token = False
            return
        self.token = False
        self.session = requests.Session()

        self.session.proxies.update(proxies)
        payload = base64.b64encode(f"{user1}:{psw1}".encode()).decode()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://extranet.policiacivil.mg.gov.br',
            'Sec-GPC': '1',
            'Authorization': f'Basic {payload}',
            'Connection': 'keep-alive',
            'Referer': 'https://extranet.policiacivil.mg.gov.br/consulta-pix/login/auth',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

    def Login(self):
        data = {
            'j_username': self.user,
            'j_password': self.psw,
            'log': 'in',
        }
        response = self.session.post(
            'https://extranet.policiacivil.mg.gov.br/consulta-pix/j_spring_security_check',
            headers=self.headers,
            data=data,
        )
        if not "CONSULTA PIX - Inicio" in response.text:
            return(False)
        else:
            token = True
            self.token = True
            return(token)
        
    def Consulta(self,form:dict):
        if not self.token:
            return False
        map = {
            "chave_aleatoria":"rand",
            "telefone":"tel",
            "cpf":"cpf",
            "cnpj":"cnpj",
            "email":"mail"
        }
        for key,value in form.items():
            if value:
                key = map[key]
                chave = value
                break
        if key == 'tel':
            chave = "+55 " + chave
 

        data = {
            'tipoCh': key,
            'chave': chave,
            'autoridade': 'PC',
            'motivo': 'A pedido do comando.',
            '_action_pesquisa': 'PESQUISAR',
        }
        response = self.session.post(
            'https://extranet.policiacivil.mg.gov.br/consulta-pix/apixRequest/pesquisa',
            headers=self.headers,
            data=data,
        )
        html = response.text
        if not 'CONSULTA PIX - Pesquisa API - Swagger / Bacen' in html:
            return False
        soup = BeautifulSoup(html,'html.parser')

        soup = soup.find("table",id='resultados')
        if not soup:
            return(None)
        vinculos = soup.find_all('tbody')

        chaves = {}
        # TO DO: ADD CHAVES EXCLUIDAS
        for vinculo in vinculos:
            bank_info = {}
            for key in vinculo.find_all("td"):
                value = key.find("span")

                if value:
                    value = value.get_text().strip()

                key = key.find("strong").get_text().strip().replace(":",'')
                
                if "EVENTO" in key:
                    continue
                bank_info[key] = value

            if not bank_info.get("Status"):
                continue

            chave = bank_info.get("Chave")
            chaves[f'Chave: {chave}'] = bank_info
        if chaves == {}:
            return None
        return(chaves)

class DetranMG:
    def __init__(self, user, psw):
        self.user = user
        self.psw = psw
        self.token = False

        self.session = requests.Session()
        self.session.verify = False
                
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://empresas.detran.mg.gov.br',
                'Connection': 'keep-alive',
                'Referer': 'https://empresas.detran.mg.gov.br/RIJUD/login.asp',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Priority': 'u=0, i',
            }

    def Login(self):
        data = {
            'usuario': self.user,
            'senha': self.psw,
            'sistema': 'rijud',
            'url_inicial': 'frame.asp',
        }

        response = self.session.post(
            'https://empresas.detran.mg.gov.br/valida_certificado/verifica-login-usuario-senha.asp',
            headers=self.headers,
            data=data,
        )
        if not '<frame src="principal.asp" name="principal">' in response.text:
            return(False)
        else:
            self.token = True
            return(True)

    def Consulta(self,value):
        value = re.sub(r'[^A-Za-z0-9]', '', value)
        data = {
                'cnpj': '',
                'cpf': '',
                'renavam': '',
                'placa': value,
                'chassi': '',
            }

    
        response = self.session.post('https://empresas.detran.mg.gov.br/RIJUD/consultaVeic02.asp',  headers=self.headers, data=data)
        html = response.text

        if 'color="#FFFFFF">Mensagem !<' in html:
            return(None)
        elif not 'Aguarde carregando ...' in html:
            return(False)

        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table")
        linhas = table.find_all("tr")

        resultado = {}

        for tr in linhas:
            tds = tr.find_all("td")
            
            if not tds:
                continue

            # --- Função util para limpar textos ---
            def limpa(txt):
                txt = txt.replace("\n", " ").replace("\t", " ")
                txt = re.sub(r"\s+", " ", txt).strip()
                return txt

            if len(tds) == 4:
                k1 = limpa(tds[0].get_text())
                v1 = limpa(tds[1].get_text())
                k2 = limpa(tds[2].get_text())
                v2 = limpa(tds[3].get_text())

                if k1:
                    resultado[k1] = v1
                if k2:
                    resultado[k2] = v2

            elif len(tds) == 2:
                k = limpa(tds[0].get_text())
                v = limpa(tds[1].get_text())

                # --- Correção especial do proprietário ---
                if k.lower().startswith("propriet"):
                    # remove espaços extras e o "-" solto
                    v = v.replace(" - ", " - ").strip()

                if k:
                    resultado[k] = v
        return (resultado)
    



class FotoBa:
    def __init__(self, user, psw, session=None):
        self.user, self.psw = user, psw
        self.token = None
        self.session = session or requests.Session()
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Host': 'mop.ssp.ba.gov.br',
            'User-Agent': 'okhttp/4.9.2',
        }

    def encrypt(self, payload):
        def encode_string(text):
            if not text:
                return ""
            code = ""
            for c in text.strip():
                code += str(ord(c) + 166).zfill(3)
            return code

        payload = {k: encode_string(str(v)) for k, v in payload.items()}
        js = json.dumps(payload, separators=(',', ':'))
        return base64.b64encode(js.encode()).decode()

    def Login(self):
        data = {
            "matricula": self.user, "senha": self.psw,
            "versao": "", "imei": "", "ambiente": "p", "sistema": "android"
        }
        try:
            enc = self.encrypt(data)
            resp = self.session.post(
                "https://mop.ssp.ba.gov.br/ServiceMopConsultas/api/Geral/ConsultaUsuarioMopIos",
                headers=self.headers,
                json={"JsonParam": enc},
                timeout=10
            )
            j = resp.json()
            if isinstance(j, list) and j and j[0].get("retorno") == "ok":
                self.token = str(j[0].get("codigo"))
                return self.token
            return False
        except Exception:
            return False

    def Consulta(self, cpf):
        if not self.token:
            return False
        data = {"usuario": self.token, "rg": "", "cpf": cpf, "nome": ""}
        try:
            enc = self.encrypt(data)
            resp = self.session.post(
                "https://mop.ssp.ba.gov.br/ServiceMopConsultas/api/Geral/ConsultaAntecedentesIos",
                headers=self.headers,
                json={"JsonParam": enc},
                timeout=10
            )
            j = resp.json()

            if isinstance(j, list) and not j:
                return None
            if isinstance(j, list):
                j = j[0]
            for k in [
                "paginas", "origem", "tipodoc", "registro", "situacao", "sequencia",
                "obito", "viva", "avaliacao", "delegacia", "data_inquerito",
                "incidencias", "inqueritos", "envolvimentos", "documentos",
                "naturezas", "retorno", "codigo"
            ]:
                j.pop(k, None)
            for k, v in list(j.items()):
                if v == "NÃO": j[k] = False
                elif v == "SIM": j[k] = True
                elif v == "": j[k] = None
            return j
        except Exception:
            return False

class FotoEs:
    def __init__(self, user, psw, session=None):
        self.user = user
        self.psw = psw
        self.token = None
        self.session = session or requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://portal.sisp.es.gov.br',
            'Connection': 'keep-alive',
            'Referer': 'https://portal.sisp.es.gov.br/sispes-frontend/xhtml/pesquisa.jsf',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

    def Login(self):
        data = {
            'j_username': self.user,
            'j_password': self.psw,
            'submit.x': '193',
            'submit.y': '24'
        }
        try:
            resp = self.session.post(
                'https://portal.sisp.es.gov.br/sispes-frontend/xhtml/j_security_check',
                headers=self.headers,
                data=data,
                verify=False
            )
            text = resp.text
            if "Documentos Relacionados" not in text:
                return False
            # extrair ViewState
            self.token = text.split('id="j_id1:javax.faces.ViewState:0" value="')[1].split('"')[0]
            return self.token
        except Exception:
            return False

    def Consulta(self, cpf):
            cpf = re.sub(r'[^a-zA-Z0-9]', '', cpf)

            # primeiro post
            data1 = {
                'pesquisaform': 'pesquisaform',
                'pesquisaform:paramPesquisa': cpf,
                'pesquisaform:btnPesquisar': '',
                'javax.faces.ViewState': self.token
            }
            resp1 = self.session.post(
                'https://portal.sisp.es.gov.br/sispes-frontend/xhtml/pesquisa.jsf',
                headers=self.headers,
                data=data1,
                verify=False
            )
            r1 = resp1.text
            if '<td colspan="5">Nenhum resultado encontrado para os parâmetros informados.</td>' in r1:
                return None
            if '<input id="j_password" name="j_password" type="password"' in r1:
                return None

            html = r1.split('<div id="pesquisaform:tblPessoas" class="ui-datatable ui-widget" style="width: 100%">')[1].split('<div id="pesquisaform:tableParts" class="ui-datatable ui-widget" style="width: 100%">')[0]
            soup = BeautifulSoup(html, 'html.parser')
            
            box = soup.find("div", class_='ui-datatable-tablewrapper')
            _, nome, nascimento, mae, pai = [value.get_text() for value in box.find_all("td", role="gridcell")]

            # segundo post (mostrar fotos)
            data2 = {
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': 'pesquisaform:tblPessoas',
                'javax.faces.partial.execute': 'pesquisaform:tblPessoas',
                'javax.faces.partial.render': 'pesquisaform:growl+pesquisaform:tblPessoas',
                'javax.faces.behavior.event': 'rowToggle',
                'javax.faces.partial.event': 'rowToggle',
                'pesquisaform:tblPessoas_rowExpansion': 'true',
                'pesquisaform:tblPessoas_expandedRowIndex': '0',
                'pesquisaform:tblPessoas_encodeFeature': 'true',
                'pesquisaform:tblPessoas_skipChildren': 'true',
                'pesquisaform': 'pesquisaform',
                'pesquisaform:paramPesquisa': cpf,
                'pesquisaform:tblPessoas_selection': '',
                'javax.faces.ViewState': self.token
            }
            resp2 = self.session.post(
                'https://portal.sisp.es.gov.br/sispes-frontend/xhtml/pesquisa.jsf',
                headers=self.headers,
                data=data2,
                verify=False
            )
            vs = resp2.text.split('j_id1:javax.faces.ViewState:0"><![CDATA[')[1].split(']]></update>')[0]

            data3 = {
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': 'pesquisaform:tblPessoas:0:imgs',
                'javax.faces.partial.execute': '@all',
                'javax.faces.partial.render': 'pesquisaform:dlgImagens',
                'pesquisaform:tblPessoas:0:imgs': 'pesquisaform:tblPessoas:0:imgs',
                'pesquisaform': 'pesquisaform',
                'pesquisaform:paramPesquisa': cpf,
                'pesquisaform:tblPessoas_selection': '',
                'javax.faces.ViewState': vs
            }
            resp3 = self.session.post(
                'https://portal.sisp.es.gov.br/sispes-frontend/xhtml/pesquisa.jsf',
                headers=self.headers,
                data=data3,
                verify=False
            )
            soup_xml = BeautifulSoup(resp3.text, "xml")

            cdata_html = soup_xml.find("update").string
            soup_html = BeautifulSoup(cdata_html, "html.parser")

            imgs = []
            for figure in soup_html.find_all("figure"):
                img_tag = figure.find("img")
                figcaption = figure.find("figcaption")
                date = figcaption.get_text(strip=True) if figcaption else ""
                if img_tag and img_tag.get("src"):
                    src = img_tag['src']
                    img_resp = self.session.get(
                        f'https://portal.sisp.es.gov.br{src}',
                        headers=self.headers,
                        verify=False
                    )
                    img_b64 = base64.b64encode(img_resp.content).decode()
                    imgs.append(img_b64)
            if imgs == []:
                imgs = None
            else:
                imgs = imgs[-1]
            retorno = {
                "nome": nome,
                "cpf":cpf,
                "nascimento": nascimento,
                "mae": mae,
                "pai": pai,
                "foto": imgs
            }
            return retorno

if os.name == "nt":
    import msvcrt

    def file_lock(fp):
        msvcrt.locking(fp.fileno(), msvcrt.LK_LOCK, 1)

    def file_unlock(fp):
        msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)

# Linux / macOS
else:
    import fcntl

    def file_lock(fp):
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)

    def file_unlock(fp):
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)

def save_db(db):
    with db_lock:  # garante que apenas 1 thread passa aqui
        tmp = DB_PATH + ".tmp"

        # Escreve arquivo temporário
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        # Faz replace com retry (Windows-friendly)
        for tentativa in range(10):
            try:
                # tenta travar o arquivo destino
                if os.path.exists(DB_PATH):
                    with open(DB_PATH, "a") as f:
                        file_lock(f)

                os.replace(tmp, DB_PATH)
                return  # sucesso

            except PermissionError:
                time.sleep(0.05)  # espera 50ms e tenta de novo

            finally:
                # destrava o arquivo
                if os.path.exists(DB_PATH):
                    try:
                        with open(DB_PATH, "a") as f:
                            file_unlock(f)
                    except:
                        pass

        # Se falhar 10 vezes, levantar erro mais amigável
        raise PermissionError("Falhou ao substituir banco de dados após múltiplas tentativas. Outro processo está usando o arquivo.")

def save_session_pickle(obj, key):
    path = f"{key}.pkl"
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def load_session_pickle(cls, key):
    path = f"{key}.pkl"
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            os.remove(path)
    return cls("", "")

def load_db():
    if not os.path.exists(DB_PATH):
        base = {"tokens": [], "mop": {"token": None, "logs": []}}
        save_db(base)
        return base
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        base = {"tokens": [], "mop": {"token": None, "logs": []}}
        save_db(base)
        return base

def consult_generic(cls, db_key: str, data):
    db = load_db()
    mop = db.get(db_key, {})
    logs = mop.get("logs", [])

    def persist_session(client):
        db[db_key] = {"token": client.token, "logs": logs}
        save_db(db)
        save_session_pickle(client, db_key)

    client = load_session_pickle(cls, db_key)

    if client.token:
        try:
            r = client.Consulta(data)
            
            if r not in [False, None]:
                return r
            
            client.token = None
            persist_session(client)
        except Exception:
            client.token = None
            persist_session(client)

    for entry in logs:
        u, p = entry["user"], entry["psw"]
        client = cls(u, p)
        token = client.Login()

        if not token:
            continue
        client.token = token
        persist_session(client)
        try:
            r = client.Consulta(data)

            if r is False:
                # erro de login ou rede
                client.token = None
                persist_session(client)
            elif r is None:
                # consulta ok, mas sem registros
                return None
            else:
                # sucesso com dados
                return r

        except Exception:
            continue
    return False


dict_support = [
    "cadsus1",
    "bin",
    "senatran",
    "cnh",
    "chave-pix",

    "foto-pr",
    "foto-pe",
    "foto-ro",
]
entrys = {
    "cadsus1": (
        "sipni",
        Cadsus
    ),  # forms: cpf, nome, cns, data_de_nascimento, nome_mãe

    "receita": (
        "epge",
        Receita
    ),  # forms: cpf, cnpj

    "cnh": (
        "habilitacaoPR",
        CNH1
    ),  # forms: cpf, cnh

    "chave-pix": (
        "extranetMG",
        ChavePix
    ),  # forms: cpf, chave_aleatoria, telefone, email, cnpj

    "bin": (
        "redebio",
        Parana
    ),  # forms: placa, chassi, renavam, motor, caixaCambio

    "juds": (
        "detranmg",
        DetranMG
    ),  # forms: placa

    "senatran": (
        "policiaagil",
        Pernanbuco
    ),  # forms: placa, chassi

    "foto-pr": (
        "redebio",
        Parana
    ),  # forms: cpf, cnh

    "foto-pe": (
        "policiaagil",
        Pernanbuco
    ),  # forms: cpf

    "foto-ro": (
        "detranRo",
        DetranRO
    ),  # forms: cpf, cnh

    "foto-ba": (
        "mop",
        FotoBa
    ),  # forms: cpf

    "foto-es": (
        "sispes",
        FotoEs
    ),  # forms: cpf
}


def Main():
    from flask import Flask,request,jsonify
    
    APIS_TOKEN = ['curl1533']

    app = Flask(__name__)
    @app.route("/api/<id>/<token>", methods=["GET"])
    def consulta(id,token):
        
        if token not in APIS_TOKEN:
            return jsonify({"ok": False, "msg": "token invalido"}), 403

        form = request.args.to_dict() or {}
        if id in dict_support:
            valor = form
        else:
            values = 0
            for key in form:
                if form[key]:
                    values += 1
            
            if values > 1:
                valor = form
            elif values == 1:
                for key in form:
                    value = form[key]
                    if value:
                        valor = value
            else:
                return jsonify({"ok": False, "msg": f"parametros invalido"}), 404


        entry = entrys.get(id)
        if entry:
            db_key,cls = entry
        else:
            return jsonify({"ok": False, "msg": f"base {id} não encontrada"}), 404

        result = consult_generic(cls,db_key,valor)

        if result is False:
            return jsonify({"ok": False, "msg": "erro interno"}), 400
        elif result is None:
            return jsonify({"ok": True, "msg": "sem registros"}), 200
        else:
            return jsonify({"ok": True, "data": result}), 200
        
    
    return app
if __name__ == "__main__":
    app = Main()
    app.run(host="0.0.0.0", port=8081,debug=True)