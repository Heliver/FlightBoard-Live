# ✈️ FlightBoard-Live

Painel de voos ao vivo com destaque para chegadas e partidas, ideal para uso em displays ou dashboards personalizados. A interface foi construída com **Streamlit** e realiza a coleta automática dos dados através de um script Python, simulando um painel como o de aeroportos reais.

---

## 📌 Funcionalidades

- ✅ Destaque visual para o próximo voo de chegada e partida
- ✅ Piscar de alerta nos cards de destaque a cada atualização
- ✅ Histórico com os últimos 5 voos exibidos
- ✅ Tabela com as próximas chegadas e partidas
- ✅ Modo Simplificado (ideal para ESP32 com LVGL)
- ✅ Exibição de vídeo ao vivo do aeroporto
- ✅ Atualização automática a cada 20 segundos

---

## ▶️ Como rodar localmente

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/FlightBoard-Live.git](https://github.com/seu-usuario/FlightBoard-Live.git)
    cd FlightBoard-Live
    ```

2.  **Crie e ative um ambiente virtual** (opcional, mas recomendado):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o dashboard:**
    ```bash
    streamlit run dashboard.py
    ```

---

## ☁️ Deploy gratuito

Você pode publicar esse painel facilmente em serviços como:

-   [Render.com](https://render.com/)
-   [Railway.app](https://railway.app/)
-   [Streamlit Community Cloud](https://streamlit.io/cloud)

---

## 📁 Estrutura do Projeto
FLIGHTBOARD-LIVE/
├── dashboard.py         # Interface principal com Streamlit
├── flight_collector.py  # Script que coleta os dados de voo
├── requirements.txt     # Dependências do projeto
└── README.md            # Este arquivo

---

## 🧪 Requisitos

-   Python 3.8 ou superior
-   Streamlit
-   Pandas
-   Requests
-   Pytz

---

## 📷 Exemplo de uso

A tela pode ser utilizada em modo simplificado para displays pequenos como ESP32 com navegador, exibindo apenas os cards e vídeo.