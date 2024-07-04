import flet as ft
import pandas as pd
import os
import random
from flet import FilePickerResultEvent, TextField, ElevatedButton, Row, Column, Checkbox, DataTable, DataColumn, DataRow, DataCell, IconButton, icons

def main(page: ft.Page):
    page.title = "Gestión de Datos"
    page.background_color = ft.colors.WHITE

    # Campos y controles comunes
    file_path = TextField(label="Archivo seleccionado", value="Ninguno", read_only=True)
    column_count = ft.Text(value="", size=16, color="blue")
    checkboxes = []
    manual_table = DataTable(columns=[DataColumn(ft.Text("Eliminar")), DataColumn(ft.Text("Tabla vacía"))], rows=[])
    item_names = []
    filled_checkboxes = Column([])

    def on_file_picked(e: FilePickerResultEvent):
        if e.files:
            selected_file = e.files[0].path
            file_name = os.path.basename(selected_file)
            file_path.value = file_name
            page.update()

            try:
                df = pd.read_excel(selected_file)

                if 2 <= len(df.columns) <= 8:
                    column_count.value = f"Cantidad de columnas: {len(df.columns)}"

                    manual_table.columns = [DataColumn(ft.Text("Eliminar"))] + [DataColumn(ft.Row([ft.Text(col), IconButton(icon=icons.DELETE, on_click=lambda e, name=col: remove_item(name), icon_color="red")])) for col in df.columns]
                    manual_table.rows = []

                    for i in range(len(df)):
                        new_row = [DataCell(IconButton(icon=icons.DELETE, on_click=lambda e, row_index=i: remove_record(row_index), icon_color="red"))]
                        for col in df.columns:
                            new_row.append(DataCell(ft.Container(content=TextField(value=str(df.at[i, col]), on_change=on_textfield_change), bgcolor="#181c21")))
                        manual_table.rows.append(DataRow(new_row))

                    item_names.clear()
                    item_names.extend(df.columns)

                    checkboxes.clear()
                    for col in df.columns:
                        checkbox = Checkbox(label=col, value=False, on_change=on_checkbox_change)
                        checkboxes.append(checkbox)

                    filled_checkboxes.controls = checkboxes

                    # Habilitar los botones si hay al menos 2 ítems
                    add_record_button.disabled = len(manual_table.columns) - 1 < 2
                    fill_random_button.disabled = len(manual_table.rows) == 0

                else:
                    column_count.value = "Error: El archivo debe contener entre 2 y 8 columnas."
                    manual_table.columns = [DataColumn(ft.Text("Eliminar")), DataColumn(ft.Text("Tabla vacía"))]
                    manual_table.rows = []
                    filled_checkboxes.controls = []

            except Exception as ex:
                column_count.value = f"Error al leer el archivo: {str(ex)}"
                manual_table.columns = [DataColumn(ft.Text("Eliminar")), DataColumn(ft.Text("Tabla vacía"))]
                manual_table.rows = []
                filled_checkboxes.controls = []

            page.update()

    def on_checkbox_change(e):
        selected = [cb for cb in checkboxes if cb.value]
        if len(selected) > 2:
            e.control.value = False
            page.update()

    def check_table_filled():
        for row in manual_table.rows:
            for cell in row.cells[1:]:  # Ignorar el primer cell que es el botón de eliminar
                if isinstance(cell.content.content, TextField) and cell.content.content.value == "":
                    return False
        return True

    def on_textfield_change(e):
        check_table_and_generate_checkboxes()

    def add_item(e):
        item_name = item_name_field.value.strip()
        if item_name:
            # Verificar si el nombre del ítem ya existe, ignorando mayúsculas y minúsculas
            if any(item.lower() == item_name.lower() for item in item_names):
                snack_bar = ft.SnackBar(ft.Text("El nombre del ítem ya existe."))
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
                return

            if len(manual_table.columns) - 1 < 8:
                if len(manual_table.columns) == 2 and isinstance(manual_table.columns[1].label, ft.Text) and manual_table.columns[1].label.value == "Tabla vacía":
                    manual_table.columns.pop()
                    for row in manual_table.rows:
                        row.cells.pop()
                manual_table.columns.append(DataColumn(ft.Row([ft.Text(item_name), IconButton(icon=icons.DELETE, on_click=lambda e, name=item_name: remove_item(name), icon_color="red")])))

                for row in manual_table.rows:
                    row.cells.append(DataCell(ft.Container(content=TextField(on_change=on_textfield_change), bgcolor="#181c21")))
                item_names.append(item_name)
                item_name_field.value = ""
                page.update()

                # Habilitar el botón de agregar cesta si hay al menos 2 ítems
                add_record_button.disabled = len(manual_table.columns) - 1 < 2
                page.update()
                check_table_and_generate_checkboxes()

    def add_record(e):
        new_row_cells = [DataCell(ft.Container(content=TextField(on_change=on_textfield_change), bgcolor="#181c21")) for _ in range(len(manual_table.columns) - 1)]
        new_row = DataRow([DataCell(IconButton(icon=icons.DELETE, on_click=lambda e, row=None: remove_record(new_row), icon_color="red"))] + new_row_cells)
        manual_table.rows.append(new_row)
        page.update()

        # Habilitar el botón de llenado aleatorio si hay registros
        fill_random_button.disabled = len(manual_table.rows) == 0
        page.update()
        check_table_and_generate_checkboxes()

    def remove_item(item_name):
        index = next((i for i, col in enumerate(manual_table.columns[1:]) if isinstance(col.label, ft.Row) and col.label.controls[0].value == item_name), None)
        if index is not None:
            index += 1  # Ajustar el índice porque la primera columna es la de eliminación
            manual_table.columns.pop(index)
            for row in manual_table.rows:
                row.cells.pop(index)
            item_names.remove(item_name)

            # Si se elimina hasta dejar 1 ítem, eliminar los registros
            if len(manual_table.columns) - 1 <= 1:
                manual_table.rows.clear()

            # Si no quedan ítems, añadir columna "Tabla vacía"
            if len(manual_table.columns) == 1:
                manual_table.columns.append(DataColumn(ft.Text("Tabla vacía")))
                for row in manual_table.rows:
                    row.cells.append(DataCell(ft.Text("")))

            # Actualizar estado del botón de agregar cesta
            add_record_button.disabled = len(manual_table.columns) - 1 < 2

            # Deshabilitar el botón de llenado aleatorio si no hay registros
            fill_random_button.disabled = len(manual_table.rows) == 0

            page.update()
            check_table_and_generate_checkboxes()

            # Restablecer el campo de archivo seleccionado a "Ninguno" si se eliminan todos los registros
            if not manual_table.rows:
                file_path.value = "Ninguno"
                page.update()

    def remove_record(row):
        manual_table.rows.remove(row)
        page.update()
        check_table_and_generate_checkboxes()

        # Restablecer el campo de archivo seleccionado a "Ninguno" si se eliminan todos los registros
        if not manual_table.rows:
            file_path.value = "Ninguno"
            page.update()

    def fill_random(e):
        for row in manual_table.rows:
            for cell in row.cells[1:]:  # Ignorar el primer cell que es el botón de eliminar
                if isinstance(cell.content.content, TextField):
                    cell.content.content.value = str(random.choice([0, 1]))
        page.update()
        check_table_and_generate_checkboxes()

    def check_table_and_generate_checkboxes():
        filled_checkboxes.controls.clear()
        if len(manual_table.columns) - 1 >= 2:
            for i, item in enumerate(item_names):
                item_filled = all(isinstance(row.cells[i + 1].content.content, TextField) and row.cells[i + 1].content.content.value != "" for row in manual_table.rows)
                filled_checkboxes.controls.append(Checkbox(label=item, value=False, disabled=not item_filled or len(manual_table.rows) == 0))
        page.update()

    add_record_button = ElevatedButton("Agregar Cesta", on_click=add_record, disabled=True)
    fill_random_button = ElevatedButton("Llenado Aleatorio", on_click=fill_random, disabled=True)

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    pick_file_button = ElevatedButton("Seleccionar archivo", on_click=lambda _: file_picker.pick_files())

    item_name_field = TextField(label="Ingrese el item", width=200)
    add_item_button = ElevatedButton("Agregar Item", on_click=add_item)
    
    main_section = Column([
        ft.Text("Gestión de Datos", size=24),
        Row([file_path, pick_file_button]),
        column_count,
        Row([item_name_field, add_item_button]),
        Row([add_record_button, fill_random_button]),
        Row([
            Column([filled_checkboxes], expand=False),
            Column([manual_table], expand=True, scroll="always"),
        ], expand=True, vertical_alignment="start"),
    ], expand=True)

    page.add(main_section)

ft.app(target=main)
