import flet as ft
import pandas as pd
from flet import FilePickerResultEvent, TextField, ElevatedButton, Row, Column

def main(page: ft.Page):
    page.title = "Gestión de Datos"
    
    # Campos y controles comunes
    file_path = TextField(label="Archivo seleccionado", read_only=True)
    column_count = ft.Text(value="", size=16, color="blue")
    column_names = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)
    checkboxes = []
    # Inicialización con una columna de ejemplo
    manual_table = ft.DataTable(columns=[ft.DataColumn(ft.Text("Placeholder"))], rows=[])
    
    # Función para manejar la selección del archivo en carga automática
    def on_file_picked(e: FilePickerResultEvent):
        if e.files:
            file_path.value = e.files[0].path
            page.update()
            
            # Leer el archivo Excel
            try:
                df = pd.read_excel(file_path.value)
                
                # Validar el número de columnas
                if 2 <= len(df.columns) <= 8:
                    column_count.value = f"Cantidad de items: {len(df.columns)}"
                    
                    checkboxes.clear()
                    for col in df.columns:
                        checkbox = ft.Checkbox(label=col, value=False, on_change=on_checkbox_change)
                        checkboxes.append(checkbox)

                    if len(df.columns) == 2:
                        checkboxes[0].value = True
                        checkboxes[1].value = True

                    column_names.controls = checkboxes

                else:
                    column_count.value = "Error: El archivo debe contener entre 2 y 8 columnas."
                    column_names.controls = []
                
            except Exception as ex:
                column_count.value = "Error al leer el archivo"
                column_names.controls = [ft.Text(str(ex))]
            
            page.update()
    
    # Función para cambiar entre secciones
    def switch_section(section):
        if section == "automatica":
            automatic_section.visible = True
            manual_section.visible = False
        else:
            automatic_section.visible = False
            manual_section.visible = True
        page.update()

    # Función para manejar el cambio de estado de los checkboxes
    def on_checkbox_change(e):
        selected = [cb for cb in checkboxes if cb.value]
        if len(selected) > 2:
            e.control.value = False
            page.update()
    
    # Función para generar la tabla en carga manual
    def generate_table(e):
        item_count = int(item_count_field.value)
        record_count = int(record_count_field.value)
        
        if not (2 <= item_count <= 8):
            page.add(ft.Text("Error: La cantidad de ítems debe estar entre 2 y 8.", color="red"))
            return
        
        # Crear encabezados de la tabla
        headers = [ft.DataColumn(ft.Text(f"Item {i+1}")) for i in range(item_count)]
        rows = []

        for _ in range(record_count):
            cells = [ft.DataCell(ft.TextField()) for _ in range(item_count)]
            rows.append(ft.DataRow(cells))
        
        manual_table.columns = headers
        manual_table.rows = rows
        page.update()

    # Sección de carga automática
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    pick_file_button = ft.ElevatedButton("Seleccionar archivo", on_click=lambda _: file_picker.pick_files())
    automatic_section = Column([
        ft.Text("Carga de Datos Automática", size=24),
        file_path,
        pick_file_button,
        column_count,
        column_names,
    ])
    
    # Sección de carga manual
    item_count_field = TextField(label="Cantidad de ítems (2-8)", width=200)
    record_count_field = TextField(label="Cantidad de registros", width=200)
    generate_table_button = ElevatedButton("Generar Tabla", on_click=generate_table)
    manual_section = Column([
        ft.Text("Carga de Datos Manual", size=24),
        Row([item_count_field, record_count_field, generate_table_button]),
        manual_table,
    ])
    
    # Navegación
    navigation = Row([
        ElevatedButton("Carga Automática", on_click=lambda _: switch_section("automatica")),
        ElevatedButton("Carga Manual", on_click=lambda _: switch_section("manual")),
    ])
    
    # Inicialmente ambas secciones deben estar visibles
    automatic_section.visible = True
    manual_section.visible = False
    
    page.add(navigation)
    page.add(automatic_section)
    page.add(manual_section)
    
    # Mostrar la sección automática por defecto
    switch_section("automatica")

# Ejecutar la aplicación Flet
ft.app(target=main)
