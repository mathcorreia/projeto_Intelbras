import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import datetime

# URL do nosso backend
BACKEND_URL = "http://backend:8000"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG], suppress_callback_exceptions=True)
app.title = "Dashboard de Monitoramento"

def create_camera_card(camera):
    return dbc.Card(
        dbc.CardBody([
            html.H5(camera['name'], className="card-title"),
            html.P(f"IP: {camera['ip_address']}"),
            html.P(f"Nível: {camera['level'].capitalize()}", className=f"text-{camera['level']}"),
        ]),
        id={'type': 'camera-card', 'index': camera['id']},
        n_clicks=0,
        className="mb-2 camera-card",
        style={'cursor': 'pointer'}
    )

def create_event_card(event):
    metadata = event.get('metadata', {})
    
    card_header = html.Div(f"{event['event_type'].replace('_', ' ').title()} - {event['id']}", className="card-header")
    card_body_content = [
        html.P(f"Timestamp: {datetime.datetime.fromisoformat(event['timestamp']).strftime('%d/%m/%Y %H:%M:%S')}", className="small"),
    ]

    # Lógica adaptativa para exibir dados
    if metadata:
        if 'name' in metadata:
            card_body_content.append(html.H5(metadata['name'], className="text-info"))
        if 'expression' in metadata:
            card_body_content.append(html.P(f"Temperamento: {metadata['expression']}"))
        if 'gender' in metadata:
            card_body_content.append(html.P(f"Gênero: {metadata['gender']}"))
        if 'age_range' in metadata:
            card_body_content.append(html.P(f"Idade Estimada: {metadata['age_range']}"))
            
    return dbc.Card([card_header, dbc.CardBody(card_body_content)], className="mb-2")


# --- Layout Principal da Aplicação ---
app.layout = dbc.Container(fluid=True, children=[
    dcc.Store(id='store-selected-camera-id'),
    dcc.Interval(id='interval-cameras', interval=30000, n_intervals=0), # Atualiza lista de cameras a cada 30s
    dcc.Interval(id='interval-events', interval=5000, n_intervals=0), # Atualiza eventos a cada 5s

    dbc.Row([
        # Coluna da Esquerda (Sidebar)
        dbc.Col(width=3, children=[
            html.H2("Câmeras", className="text-center my-3"),
            dbc.Input(id='new-cam-name', placeholder='Nome da Câmera', className='mb-2'),
            dbc.Input(id='new-cam-ip', placeholder='Endereço IP', className='mb-2'),
            dbc.Select(
                id='new-cam-level',
                options=[
                    {'label': 'Bronze', 'value': 'bronze'},
                    {'label': 'Prata', 'value': 'silver'},
                    {'label': 'Ouro', 'value': 'gold'},
                ],
                value='bronze',
                className='mb-2'
            ),
            dbc.Button('Adicionar Câmera', id='add-cam-button', color='primary', className='w-100'),
            html.Hr(),
            html.Div(id='camera-list', children=[html.P("Carregando câmeras...")]),
        ], className="bg-dark vh-100 p-3"),

        # Coluna da Direita (Conteúdo Principal)
        dbc.Col(width=9, children=[
            html.Div(id='main-content', className="p-3")
        ]),
    ])
])

# --- Callbacks ---

# Atualizar a lista de câmeras
@app.callback(
    Output('camera-list', 'children'),
    Input('interval-cameras', 'n_intervals')
)
def update_camera_list(n):
    try:
        response = requests.get(f"{BACKEND_URL}/cameras/")
        if response.status_code == 200:
            cameras = response.json()
            if not cameras:
                return html.P("Nenhuma câmera cadastrada.")
            return [create_camera_card(cam) for cam in cameras]
        return html.P("Erro ao carregar câmeras.")
    except requests.exceptions.RequestException:
        return html.P("Backend indisponível.")

# Adicionar nova câmera
@app.callback(
    Output('interval-cameras', 'n_intervals'), # Força a atualização da lista
    Input('add-cam-button', 'n_clicks'),
    State('new-cam-name', 'value'),
    State('new-cam-ip', 'value'),
    State('new-cam-level', 'value'),
    State('interval-cameras', 'n_intervals'),
    prevent_initial_call=True
)
def add_camera(n_clicks, name, ip, level, current_intervals):
    if name and ip and level:
        payload = {'name': name, 'ip_address': ip, 'level': level}
        try:
            requests.post(f"{BACKEND_URL}/cameras/", json=payload)
        except requests.exceptions.RequestException:
            pass # Lidar com erro se necessário
    return current_intervals + 1

# Armazenar ID da câmera selecionada
@app.callback(
    Output('store-selected-camera-id', 'data'),
    [Input({'type': 'camera-card', 'index': dash.ALL}, 'n_clicks')]
)
def store_selected_camera(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n > 0 for n in n_clicks if n is not None):
        return None
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    camera_id = eval(button_id)['index']
    return camera_id

# Atualizar o conteúdo principal com base na câmera selecionada
@app.callback(
    Output('main-content', 'children'),
    Input('store-selected-camera-id', 'data'),
    Input('interval-events', 'n_intervals')
)
def update_main_content(camera_id, n):
    if camera_id is None:
        return html.H4("Selecione uma câmera na lista à esquerda.", className="text-center mt-5")

    try:
        # Pega os eventos da câmera selecionada
        events_response = requests.get(f"{BACKEND_URL}/events/{camera_id}")
        events = events_response.json() if events_response.status_code == 200 else []
        
        return dbc.Row([
            # Coluna de Vídeo
            dbc.Col(md=8, children=[
                html.H4("Feed de Vídeo Ao Vivo"),
                html.Img(src=f"{BACKEND_URL}/video_feed/{camera_id}", style={'width': '100%'})
            ]),
            # Coluna de Eventos
            dbc.Col(md=4, children=[
                html.H4("Últimos Eventos"),
                html.Div(
                    id='event-list',
                    children=[create_event_card(e) for e in reversed(events)] if events else "Nenhum evento recente."
                )
            ])
        ])

    except requests.exceptions.RequestException:
        return html.H4("Erro de comunicação com o backend.", className="text-center mt-5 text-danger")

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)