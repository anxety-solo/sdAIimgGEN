# ~ widgets.py | by ANXETY ~

from widget_factory import WidgetFactory        # WIDGETS
from webui_utils import update_current_webui    # WEBUI
import json_utils as js                         # JSON

import ipywidgets as widgets
from pathlib import Path
import os


# Constants
HOME = Path.home()
SCR_PATH = Path(HOME / 'ANXETY')
SETTINGS_PATH = SCR_PATH / 'settings.json'
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

SCRIPTS = SCR_PATH / 'scripts'

CSS = SCR_PATH / 'CSS'
JS = SCR_PATH / 'JS'
widgets_css = CSS / 'main-widgets.css'
widgets_js = JS / 'main-widgets.js'


## ======================= WIDGETS =======================

def read_model_data(file_path, data_type):
    """Reads model, VAE, or ControlNet data from the specified file."""
    local_vars = {}
    
    with open(file_path) as f:
        exec(f.read(), {}, local_vars)
    
    if data_type == "model":
        model_names = list(local_vars['model_list'].keys())   # Return model names
        return ['none'] + model_names
    elif data_type == "vae":
        vae_names = list(local_vars['vae_list'].keys())    # Return the VAE names
        return ['none', 'ALL'] + vae_names
    elif data_type == "cnet":
        cnet_names = list(local_vars['controlnet_list'].keys())   # Return ControlNet names
        return ['none', 'ALL'] + cnet_names

webui_selection = {
    'A1111': "--xformers --no-half-vae",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'ComfyUI': "--dont-print-server --preview-method auto --use-pytorch-cross-attention",
    'Forge': "--opt-sdp-attention --cuda-stream --cuda-malloc --pin-shared-memory"  # Remove: --disable-xformers 
}

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets."""
model_header = factory.create_header('Выбор Модели')
model_options = read_model_data(f'{SCRIPTS}/_models-data.py', 'model')
model_widget = factory.create_dropdown(model_options, 'Модель:', '4. Counterfeit [Anime] [V3] + INP')
model_num_widget = factory.create_text('Номер Модели:', '', 'Введите номера моделей для скачивания.')
inpainting_model_widget = factory.create_checkbox('Inpainting Модели', False, class_names=['inpaint'])
XL_models_widget = factory.create_checkbox('SDXL', False, class_names=['sdxl'])

switch_model_widget = factory.create_hbox([inpainting_model_widget, XL_models_widget])

# --- VAE ---
"""Create VAE selection widgets."""
vae_header = factory.create_header('Выбор VAE')
vae_options = read_model_data(f'{SCRIPTS}/_models-data.py', 'vae')
vae_widget = factory.create_dropdown(vae_options, 'Vae:', '3. Blessed2.vae')
vae_num_widget = factory.create_text('Номер Vae:', '', 'Введите номера vae для скачивания.')

# --- ADDITIONAL ---
"""Create additional configuration widgets."""
additional_header = factory.create_header('Дополнительно')
latest_webui_widget = factory.create_checkbox('Обновить WebUI', True)
latest_extensions_widget = factory.create_checkbox('Обновить Расширения', True)
check_custom_nodes_deps_widget = factory.create_checkbox('Чекать зависимости Custom-Nodes', True)
change_webui_widget = factory.create_dropdown(list(webui_selection.keys()), 'WebUI:', 'A1111', layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], 'Подробная Загрузка:', 'off', layout={'width': 'auto'})
choose_changes_widget = factory.create_hbox(
    [
        latest_webui_widget,
        latest_extensions_widget,
        check_custom_nodes_deps_widget,   # Only ComfyUI
        change_webui_widget,
        detailed_download_widget
    ],
    layout={'justify_content': 'space-between'}
)

controlnet_options = read_model_data(f'{SCRIPTS}/_models-data.py', 'cnet')
controlnet_widget = factory.create_dropdown(controlnet_options, 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text('Номер ControlNet:', '', 'Введите номера моделей ControlNet для скачивания.')
commit_hash_widget = factory.create_text('Commit Hash:', '', 'Переключение между ветвями или коммитами.')
civitai_token_widget = factory.create_text('Токен CivitAI:', '', 'Введите свой API-токен CivitAi.')
huggingface_token_widget = factory.create_text('Токен HuggingFace:')

ngrok_token_widget = factory.create_text('Токен Ngrok:')
ngrok_button = factory.create_html('<a href="https://dashboard.ngrok.com/get-started/your-authtoken" target="_blank">Получить Ngrok Токен</a>', class_names=["button", "button_zrok"])
ngrok_widget = factory.create_hbox([ngrok_token_widget, ngrok_button])

zrok_token_widget = factory.create_text('Токен Zrok:')
zrok_button = factory.create_html('<a href="https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU" target="_blank">Зарегать Zrok Токен</a>', class_names=["button", "button_zrok"])
zrok_widget = factory.create_hbox([zrok_token_widget, zrok_button])

commandline_arguments_widget = factory.create_text('Аргументы:', webui_selection['A1111'])

additional_widget_list = [
    additional_header,
    choose_changes_widget,
    HR,
    controlnet_widget, controlnet_num_widget,
    commit_hash_widget,
    civitai_token_widget, huggingface_token_widget, zrok_widget, ngrok_widget,
    HR,
    commandline_arguments_widget
]

# --- CUSTOM DOWNLOAD ---
"""Create Custom-Download Selection widgets."""
custom_download_header_popup = factory.create_html('''
<div class="header" style="cursor: pointer;" onclick="toggleContainer()">Кастомная Загрузка</div>
<div class="info" id="info_dl">INFO</div>
<div class="popup">
    Разделите несколько URL-адресов запятой/пробелом.
    Для <span class="file_name">пользовательского имени</span> файла/расширения укажите его через <span class="braces">[]</span> после URL без пробелов.
    <span class="required">Для файлов обязательно укажите</span> - <span class="extension">Расширение Файла.</span>
    <div class="sample">
        <span class="sample_label">Пример для Файла:</span>
        https://civitai.com/api/download/models/229782<span class="braces">[</span><span class="file_name">Detailer</span><span class="extension">.safetensors</span><span class="braces">]</span>
        <br>
        <span class="sample_label">Пример для Расширения:</span>
        https://github.com/hako-mikan/sd-webui-regional-prompter<span class="braces">[</span><span class="file_name">Regional-Prompter</span><span class="braces">]</span>
    </div>
</div>
''')

empowerment_widget = factory.create_checkbox('Расширение возможностей', False, class_names=['empowerment'])
empowerment_output_widget = factory.create_textarea(
'', '', """Используйте специальные теги. Портативный аналог "Файл (txt)"
Доступные теги: model, vae, lora, embed, extension, adetailer, control, upscale, clip, config
---
Например:

# Lora
https://civitai.com/api/download/models/229782

# Extension
https://github.com/hako-mikan/sd-webui-cd-tuner[CD-Tuner]
""",
layout={'width': '100%'}
)

Model_url_widget = factory.create_text('Model:')
Vae_url_widget = factory.create_text('Vae:')
LoRA_url_widget = factory.create_text('LoRa:')
Embedding_url_widget = factory.create_text('Embedding:')
Extensions_url_widget = factory.create_text('Extensions:')
ADetailer_url_widget = factory.create_text('ADetailer:')
custom_file_urls_widget = factory.create_text('Файл (txt):')

# --- Save Button ---
"""Create button widgets."""
save_button = factory.create_button('Сохранить', class_names=["button", "button_save"])

## ================== DISPLAY / SETTINGS =================

factory.load_css(widgets_css)   # load CSS (widgets)
factory.load_js(widgets_js)     # load JS (widgets)

# Display sections
model_widgets = [model_header, model_widget, model_num_widget, switch_model_widget]
vae_widgets = [vae_header, vae_widget, vae_num_widget]
additional_widgets = additional_widget_list
custom_download_widgets = [
    custom_download_header_popup,
    empowerment_widget,
    empowerment_output_widget,
    Model_url_widget,
    Vae_url_widget,
    LoRA_url_widget,
    Embedding_url_widget,
    Extensions_url_widget,
    ADetailer_url_widget,
    custom_file_urls_widget
]

# Create Boxes
model_box = factory.create_vbox(model_widgets, class_names=["container"])
vae_box = factory.create_vbox(vae_widgets, class_names=["container"])
additional_box = factory.create_vbox(additional_widgets, class_names=["container"])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=["container", "container_cdl"])

WIDGET_LIST = factory.create_vbox([model_box, vae_box, additional_box, custom_download_box, save_button],
                                  layouts=[{'width': '1080px'}]*4)    # style for the first four elements
factory.display(WIDGET_LIST)

## ================== CALLBACK FUNCTION ==================

# Initialize visibility
check_custom_nodes_deps_widget.layout.display = 'none'  # Initially hidden
empowerment_output_widget.layout.display = 'none'       # Initially hidden

# Callback functions for XL options
def update_XL_options(change, widget):
    selected = change['new']

    default_model_values = {
        True: ('3. WAI-illustrious [Anime] [V9] [XL]', 'none', 'none'),            # For XL models
        False: ('4. Counterfeit [Anime] [V3] + INP', '3. Blessed2.vae', 'none')    # For 1.5 models
    }

    # GET DATA MODELs | VAES| CNETs
    data_file = '_xl-models-data.py' if selected else '_models-data.py'
    model_widget.options = read_model_data(f'{SCRIPTS}/{data_file}', 'model')
    vae_widget.options = read_model_data(f'{SCRIPTS}/{data_file}', 'vae')
    controlnet_widget.options = read_model_data(f'{SCRIPTS}/{data_file}', 'cnet')

    # Set default values from the dictionary
    model_widget.value, vae_widget.value, controlnet_widget.value = default_model_values[selected]

# Callback functions for updating widgets
def update_change_webui(change, widget):
    selected_webui = change['new']
    commandline_arguments = webui_selection.get(selected_webui, "")
    commandline_arguments_widget.value = commandline_arguments
    
    if selected_webui == 'ComfyUI':
        latest_extensions_widget.layout.display = 'none'
        latest_extensions_widget.value = False
        check_custom_nodes_deps_widget.layout.display = 'inline-block'
        Extensions_url_widget.description = 'Custom Nodes:'
    else:
        latest_extensions_widget.layout.display = 'inline-block'
        latest_extensions_widget.value = True
        check_custom_nodes_deps_widget.layout.display = 'none'
        Extensions_url_widget.description = 'Extensions:'

# Callback functions for Empowerment
def update_empowerment(change, widget):
    selected_emp = change['new']

    customDL_widgets = [
        Model_url_widget,
        Vae_url_widget, 
        LoRA_url_widget,
        Embedding_url_widget,
        Extensions_url_widget,
        ADetailer_url_widget
    ]

    if selected_emp:
        for wg in customDL_widgets:
            wg.layout.display = 'none'
        empowerment_output_widget.layout.display = 'inline-block'
    else:
        for wg in customDL_widgets:
            wg.layout.display = ''    # idk why, but that's the way it's supposed to be >_<'
        empowerment_output_widget.layout.display = 'none'

# Connecting widgets
factory.connect_widgets([(change_webui_widget, 'value')], update_change_webui)
factory.connect_widgets([(XL_models_widget, 'value')], update_XL_options)
factory.connect_widgets([(empowerment_widget, 'value')], update_empowerment)

## ============== Load / Save - Settings V3 ==============

SETTINGS_KEYS = [
      'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
      'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash',
      'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments',
      # CustomDL
      'empowerment', 'empowerment_output',
      'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
      'custom_file_urls'
]

def save_settings():
    """Save widget values to settings."""
    widgets_values = {key: globals()[f"{key}_widget"].value for key in SETTINGS_KEYS}
    js.save(SETTINGS_PATH, "WIDGETS", widgets_values)

    update_current_webui(change_webui_widget.value)  # Upadte Selected WebUI in setting.json

def load_settings():
    """Load widget values from settings."""
    if js.key_exists(SETTINGS_PATH, 'WIDGETS'):
        widget_data = js.read(SETTINGS_PATH, 'WIDGETS')
        for key in SETTINGS_KEYS:
            if key in widget_data:
                globals()[f"{key}_widget"].value = widget_data.get(key, "")

def save_data(button):
    """Handle save button click."""
    save_settings()
    factory.close(list(WIDGET_LIST.children), class_names=['hide'], delay=0.8)

load_settings()
save_button.on_click(save_data)