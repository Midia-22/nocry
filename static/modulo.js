/* -------------------------------
   CARREGAMENTO DO MÓDULO
--------------------------------*/
async function carregarModulo() {
    const moduloID = location.hash.replace("#", "").trim();
    if (!moduloID) return console.error("Nenhum ID encontrado na URL.");

    try {
        const response = await fetch("modules");
        const modules = await response.json();

        const modulo = modules.find(m => m.id === moduloID);
        if (!modulo) return console.error("Módulo não encontrado:", moduloID);

        preencherCabecalho(modulo);
        criarCamposFormulario(modulo);
        validarCampos();
    } catch (e) {
        console.error("Erro ao carregar módulo:", e);
    }
}

/* -------------------------------
   FUNÇÃO: PREENCHER CABEÇALHO
--------------------------------*/
function preencherCabecalho(modulo) {
    document.querySelector(".module-header h1").textContent = modulo.title;
    document.querySelector(".module-header .info").textContent = modulo.desc;
}

/* -------------------------------
   FUNÇÃO: CRIAR CAMPOS DO FORMULÁRIO
--------------------------------*/
function criarCamposFormulario(modulo) {
    const searchBox = document.querySelector(".search-box");

    searchBox.querySelectorAll(".input-row").forEach(r => r.remove());
    if (!modulo.forms || modulo.forms.length === 0) return;

    const placeholders = {
        cpf: "000.000.000-00",
        nome: "João da Silva",
        cnpj: "00.000.000/0000-00",
        telefone: "(00) 00000-0000",
        email: "email@exemplo.com",
        placa: "ABC-1234",
        chassi: "9BWZZZ377VT004251",
        renavam: "12345678901",
        motor: "Número do motor",
        caixaCambio: "Código da caixa de câmbio",
        cnh: "12345678900",
        cns: "000000000000000",
        data_de_nascimento: "01/01/2000",
        nome_mãe: "Maria Bonita",
        chave_aleatoria:"7f1c2b39-5e7d-4f0c-a9b3-62e4c1ae89d2"
    };

    for (let i = 0; i < modulo.forms.length; i += 2) {
        const row = document.createElement("div");
        row.className = "input-row";

        for (let j = 0; j < 2; j++) {
            const rawField = modulo.forms[i + j];
            if (!rawField) break;

            const group = document.createElement("div");
            group.className = "input-group";

            const labelText = rawField.replace(/_/g, ' ');

            group.innerHTML = `
                <label>${labelText.toUpperCase()}</label>
                <input type="text" data-field="${rawField}"
                       placeholder="${placeholders[rawField] || labelText}" />
            `;
            row.appendChild(group);
        }

        searchBox.insertBefore(row, document.querySelector(".btn-area"));
    }

    document.querySelectorAll(".input-group input").forEach(input => {
        const tipo = input.dataset.field;
        if (["cpf", "cnpj", "telefone", "data_de_nascimento", "placa",].includes(tipo)) {
            aplicarMascara(input, tipo);
        }
    });
}

/* -------------------------------
   FUNÇÃO: APLICAR MÁSCARAS
--------------------------------*/
function aplicarMascara(input, tipo) {
    input.addEventListener("input", () => {

        // Tratamento de placa permite letras e números
        let v;
        if (tipo === "placa") {
            v = input.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
        } else {
            v = input.value.replace(/\D/g, "");
        }

        switch (tipo) {

            /* ---- MÁSCARA DE PLACA (BRASIL) ---- */
            case "placa":
                // Antigo: AAA9999
                if (/^[A-Z]{3}[0-9]{4}$/.test(v)) {
                    v = v.replace(/^([A-Z]{3})([0-9]{4})$/, "$1-$2");
                }
                // Mercosul: AAA9A99
                else if (/^[A-Z]{3}[0-9][A-Z][0-9]{2}$/.test(v)) {
                    v = v.replace(/^([A-Z]{3})([0-9][A-Z][0-9]{2})$/, "$1-$2");
                }
                // Montagem dinâmica ao digitar
                else {
                    if (v.length > 3) {
                        v = v.slice(0, 3) + "-" + v.slice(3);
                    }
                    if (v.length > 8) {
                        v = v.slice(0, 8);
                    }
                }
                break;

            case "cpf":
                v = v.replace(/(\d{3})(\d)/, "$1.$2")
                     .replace(/(\d{3})(\d)/, "$1.$2")
                     .replace(/(\d{3})(\d{2})$/, "$1-$2");
                break;

            case "cnpj":
                v = v.replace(/(\d{2})(\d)/, "$1.$2")
                     .replace(/(\d{3})(\d)/, "$1.$2")
                     .replace(/(\d{3})(\d)/, "$1/$2")
                     .replace(/(\d{4})(\d{2})$/, "$1-$2");
                break;

            case "telefone":
                v = v.replace(/(\d{2})(\d)/, "($1) $2")
                     .replace(/(\d{5})(\d)/, "$1-$2");
                break;

            case "data_de_nascimento":
                if (v.length > 2) v = v.slice(0, 2) + '/' + v.slice(2);
                if (v.length > 5) v = v.slice(0, 5) + '/' + v.slice(5, 9);
                if (v.length > 10) v = v.slice(0, 10);
                break;
            case "chave_aleatoria":
                // Monta dinamicamente 8-4-4-4-12
                if (v.length > 8)  v = v.slice(0, 8)  + "-" + v.slice(8);
                if (v.length > 13) v = v.slice(0, 13) + "-" + v.slice(13);
                if (v.length > 18) v = v.slice(0, 18) + "-" + v.slice(18);
                if (v.length > 23) v = v.slice(0, 23) + "-" + v.slice(23);
                if (v.length > 36) v = v.slice(0, 36);
                break;
        }

        input.value = v;
    });
}

/* -------------------------------
   FUNÇÃO: VALIDAR CAMPOS
--------------------------------*/
function validarCampos() {
    const validators = {
        cpf: /^\d{3}\.\d{3}\.\d{3}-\d{2}$/,
        cnpj: /^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/,
        nome: /^[A-Za-zÀ-ÿ ]{3,}$/,
        telefone: /^\(\d{2}\) \d{5}-\d{4}$/,
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        chassi: /^[A-HJ-NPR-Z0-9]{17}$/,
        renavam: /^\d{11}$/,
        placa: /^[A-Z]{3}-[0-9]{4}$|^[A-Z]{3}-[0-9][A-Z][0-9]{2}$/,
        motor: /^[A-Za-z0-9]{5,20}$/,
        caixaCambio: /^[A-Za-z0-9]{3,20}$/,
        cnh: /^\d{11}$/,
        cns: /^\d{15}$/,
        data_de_nascimento: /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/,
        chave_aleatoria: /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/
    };

    document.querySelectorAll(".input-group input").forEach(input => {
        const tipo = input.dataset.field;
        const regex = validators[tipo];
        if (!regex) return;

        input.addEventListener("input", () => {
            const valor = input.value.trim();
            if (valor === "") {
                input.style.borderColor = "#1d2230";
                input.style.boxShadow = "none";
            } else if (regex.test(valor)) {
                input.style.borderColor = "#00ff88";
                input.style.boxShadow = "0 0 8px #00ff8855";
            } else {
                input.style.borderColor = "#ff4444";
                input.style.boxShadow = "0 0 8px #ff444455";
            }
        });
    });
}

/* -------------------------------
   FUNÇÃO: ENVIAR BUSCA
--------------------------------*/
function setFormEnabled(enabled) {
    document.querySelectorAll(".input-group input, .btn-search").forEach(el => {
        el.disabled = !enabled;
        el.style.opacity = enabled ? "1" : "0.6"; // feedback visual
        el.style.cursor = enabled ? "pointer" : "not-allowed";
    });
}

/* -------------------------------
   FUNÇÃO: ENVIAR BUSCA
--------------------------------*/
async function enviarBusca() {
    const moduloID = location.hash.replace("#", "").trim();
    if (!moduloID) return alert("Módulo inválido.");

    const dados = {};
    document.querySelectorAll(".input-group input").forEach(input => {
        dados[input.dataset.field] = input.value.trim();
    });

    const token = localStorage.getItem("token");
    if (!token) {
        alert("Token não encontrado. Faça login novamente.");
        window.location.href = "/login";
        return;
    }

    dados.token = token;

    // DESABILITA FORMULÁRIO ENQUANTO A REQUISIÇÃO ESTÁ EM ANDAMENTO
    setFormEnabled(false);

    try {
        const resposta = await fetch(`/api/${moduloID}/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });

        const json = await resposta.json();
        exibirResultado(json);
    } catch (e) {
        console.error("Erro ao enviar busca:", e);
        alert("Erro na requisição.");
    } finally {
        // REABILITA FORMULÁRIO APÓS A RESPOSTA OU ERRO
        setFormEnabled(true);
    }
}
/* -------------------------------
   FUNÇÃO: EXIBIR RESULTADO
--------------------------------*/
function exibirResultado(json) {
    const out = document.getElementById("resultado-busca");
    out.innerHTML = "";

    if (!json.ok) {
        out.innerHTML = `<div style="color:#ff4444; font-weight:bold;">Erro: ${json.msg || 'Não foi possível obter os dados'}</div>`;
        return;
    }

    let data = json.data;

    if (!data) {
        out.innerHTML = `<div style="color:#ffbb00;">Nenhum dado retornado.</div>`;
        return;
    }

    if (Array.isArray(data)) {
        if (data.length === 0) {
            out.innerHTML = `<div style="color:#ffbb00;">Nenhum registro encontrado.</div>`;
            return;
        }
        data.forEach(obj => criarCard(obj, "Resultado"));
        return;
    }

    if (typeof data === "object") {

    // Caso 1: objeto simples (seu caso)
    const allSimple = Object.values(data).every(v => typeof v !== "object" || v === null);

    if (allSimple) {
        criarCard(data, "Resultado");
        return;
    }

    // Caso 2: objeto contendo outros objetos
    for (const [secao, valores] of Object.entries(data)) {
        if (typeof valores === "object") {
            criarCard(valores, secao);
        }
    }

    return;
    }

    out.innerHTML = `<div style="color:#ffbb00;">Formato de dados desconhecido.</div>`;
}

/* -------------------------------------------------
   FUNÇÃO AUXILIAR: CRIA UM CARD DE RESULTADO
---------------------------------------------------*/
function criarCard(obj, tituloSecao) {
    const out = document.getElementById("resultado-busca");

    const card = document.createElement("div");
    Object.assign(card.style, {
        background: "#11141d",
        border: "1px solid #1d2230",
        padding: "20px",
        borderRadius: "12px",
        boxShadow: "0 0 15px rgba(0,0,0,0.3)",
        marginBottom: "20px"
    });

    const titulo = document.createElement("h3");
    titulo.textContent = tituloSecao;
    titulo.style.color = "#00bfff";
    titulo.style.marginBottom = "15px";
    titulo.style.fontSize = "20px";
    card.appendChild(titulo);

    const grid = document.createElement("div");
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "1fr 1fr";
    grid.style.gap = "15px";

    for (const [key, value] of Object.entries(obj)) {
        const fieldDiv = document.createElement("div");
        fieldDiv.style.display = "flex";
        fieldDiv.style.flexDirection = "column";

        const label = document.createElement("span");
        label.textContent = key.replace(/_/g, " ").toUpperCase();
        label.style.opacity = "0.7";
        label.style.fontSize = "14px";

    /* -------------------------------------------------------
    SE A KEY FOR "foto" → trata como imagem Base64 OU array
    --------------------------------------------------------*/
    if (key.toLowerCase() === "foto") {

        // Aceita string OU array
        let base64 = null;

        if (Array.isArray(value) && value.length > 0) {
            base64 = value[0];
        } else if (typeof value === "string") {
            base64 = value;
        }

        // Se foto existir
        if (base64 && base64.length > 20) {
            const img = document.createElement("img");
            img.src = "data:image/jpeg;base64," + base64;
            img.style.width = "150px";
            img.style.height = "150px";
            img.style.objectFit = "cover";
            img.style.borderRadius = "10px";
            img.style.border = "2px solid #00bfff";
            img.style.marginTop = "8px";
            img.style.boxShadow = "0 0 10px #00bfff55";

            // BOTÃO AZUL PARA BAIXAR A FOTO ORIGINAL
            const btn = document.createElement("button");
            btn.textContent = "Baixar Foto";
            btn.style.marginTop = "10px";
            btn.style.padding = "8px 12px";
            btn.style.background = "#007bff";
            btn.style.color = "white";
            btn.style.border = "none";
            btn.style.borderRadius = "6px";
            btn.style.cursor = "pointer";
            btn.style.fontSize = "14px";
            btn.style.width = "150px";
            btn.style.fontWeight = "bold";

            btn.addEventListener("click", () => {
                const cpf = obj.cpf || "foto"; // se não tiver CPF, usa "foto"
                const a = document.createElement("a");
                a.href = "data:image/jpeg;base64," + base64;
                a.download = cpf + ".jpg"; // aqui o nome do arquivo é o CPF
                a.click();
            });

            fieldDiv.appendChild(label);
            fieldDiv.appendChild(img);
            fieldDiv.appendChild(btn);
            grid.appendChild(fieldDiv);
            continue;
        }
    }
        /* -------------------------------------------------------
           CAMPOS PADRÃO (texto comum)
        --------------------------------------------------------*/
        const val = document.createElement("span");
        val.textContent = value || "-";
        val.style.fontWeight = "bold";
        val.style.fontSize = "16px";

        fieldDiv.appendChild(label);
        fieldDiv.appendChild(val);
        grid.appendChild(fieldDiv);
    }

    card.appendChild(grid);
    out.appendChild(card);
}

/* -------------------------------
   INICIALIZAÇÃO
--------------------------------*/
document.addEventListener("DOMContentLoaded", () => {
    // Clique no botão
    document.querySelector(".btn-search").addEventListener("click", enviarBusca);

    // Delegação de eventos para Enter
    const searchBox = document.querySelector(".search-box");
    searchBox.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault(); // evita o submit padrão
            enviarBusca();
        }
    });

    carregarModulo();
});