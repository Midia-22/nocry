import requests
import pyotp
from bs4 import BeautifulSoup
import re

'danieltrisuzzi@pcivil.rj.gov.br'
'Daniel@1213',
class Siel:
    def Login(self):
        codigo = pyotp.TOTP(self.chave).now()
        codigo = f'{codigo[:3]}.{codigo[3:]}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
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

        response = self.session.get('https://siel.tse.jus.br/session/new', headers=headers)
        r = response.text
        csrf = r.split('csrf-token" content="')[1].split('"')[0]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://siel.tse.jus.br/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://siel.tse.jus.br',
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
            'authenticity_token': csrf,
            'session[email]': self.user,
            'session[password]': self.psw,
            'session[otp]': codigo,
            'commit': 'Entrar',
        }

        response = self.session.post('https://siel.tse.jus.br/session',  headers=headers, data=data)
        if not 'Informe nome ou parte do nome' in response.text:
            return(False)

        csrf = r.split('csrf-token" content="')[1].split('"')[0]
        self.token = csrf
        return self.token


    def Consulta(self,form:dict):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://siel.tse.jus.br/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://siel.tse.jus.br',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
        }

        for key, value in form.items():
            if value:
                break
        
        if not value:
            return False

        data = {
            'authenticity_token': csrf,
            'pesquisa[num_processo]': '1',
            'pesquisa[identificador]': value,  # CPF / TITULO DE ELEITOR
            'pesquisa[nome]': '',
            'pesquisa[base]': [
                '',
                '2',
            ],
            'pesquisa[data_nasc]': '',
            'pesquisa[nome_mae]': '',
            'pesquisa[natural_uf]': '',
            'pesquisa[natural_municipio]': '',
            'pesquisa[domicilio_uf]': '',
            'pesquisa[domicilio_municipio]': '',
            'button': 'Pesquisar',
        }

        response = self.session.post('https://siel.tse.jus.br/pesquisas',  headers=headers, data=data)
        r = response.text
        if 'Nenhum Resultado encontrado' in r:
            return(None)
        elif not 'Resultado da Pesquisa' in r:
            return False
        
        soup = BeautifulSoup(r, 'html.parser')
        table = soup.find('table',class_="table table-card my-4")

        pesquisaId = None
        if table:
            for line in table.find_all('tr'):
                pesquisaId = line.find('input', attrs={'name': 'pesquisa_origem_id'})

                if pesquisaId: 
                    pesquisaId = pesquisaId['value']
                    eleitor = line.find('td', class_='center').text.strip()
                    cpf = line.find('td', class_='center font-monospace').text.strip()
                    cpf = re.sub(r'\D', '', cpf)
                
                    break


        csrf = r.split('csrf-token" content="')[1].split('"')[0]


        data = {
            'authenticity_token': csrf,
            'base': '2',
            'cpf': cpf,
            'pesquisa_origem_id': pesquisaId,
            'titulo': eleitor,
        }

        response = self.session.post('https://siel.tse.jus.br/detalhes', headers=headers, data=data)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('div',class_="card-horizontal label-w-12 parametros")
        if table:
            resultado = {}
            for line in table.find_all('div'):
                key = line.find('label').get_text(strip=True)
                if key == 'cd_status':
                    continue

                value = line.find('p',)
                if value:
                    value = value.get_text(strip=True)
                else:
                    value = ''

                resultado[key] = value

        return resultado
