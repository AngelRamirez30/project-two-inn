import flet as ft
import pandas as pd
import os
import random
from scipy.stats import chi2
from flet import FilePickerResultEvent, TextField, ElevatedButton, Row, Column, Checkbox, DataTable, DataColumn, DataRow, DataCell, IconButton, icons

def main(page: ft.Page):
    page.title = "Reglas de Asociación"
    page.background_color = ft.colors.WHITE
    page.window.maximized = True  # Maximizar la ventana al iniciar

    # Campos y controles comunes
    file_path = TextField(label="Archivo seleccionado", value="Ninguno", read_only=True)
    checkboxes = []
    manual_table = DataTable(columns=[DataColumn(ft.Text("Eliminar")), DataColumn(ft.Text("Tabla vacía"))], rows=[])
    item_names = []
    filled_checkboxes = Column([])
    contingency_table = DataTable(columns=[DataColumn(ft.Text("Contingencia")), DataColumn(ft.Text("PS")), DataColumn(ft.Text("~PS")), DataColumn(ft.Text("Total"))], rows=[])
    dependency_table = DataTable(columns=[DataColumn(ft.Text("Condición")), DataColumn(ft.Text("Valor"))], rows=[])
    results_table = DataTable(columns=[DataColumn(ft.Text("Regla")), DataColumn(ft.Text("Cobertura")), DataColumn(ft.Text("Confianza"))], rows=[])
    chi_square_text = ft.Text(value="Chi-Cuadrado: N/A", size=16)
    significance_text = ft.Text(value="Significancia: N/A", size=16)

    def on_file_picked(e: FilePickerResultEvent):
        if e.files:
            selected_file = e.files[0].path
            file_name = os.path.basename(selected_file)
            file_path.value = file_name
            page.update()

            try:
                df = pd.read_excel(selected_file)

                if 2 <= len(df.columns) <= 8:
                    manual_table.columns = [DataColumn(ft.Text("Eliminar"))] + [DataColumn(ft.Row([ft.Text(col), IconButton(icon=icons.DELETE, on_click=lambda e, name=col: remove_item(name), icon_color="red")])) for col in df.columns]
                    manual_table.rows = []

                    for i in range(len(df)):
                        new_row = [DataCell(IconButton(icon=icons.DELETE, on_click=lambda e, row_index=i: remove_record(row_index), icon_color="red"))]
                        for col in df.columns:
                            cell_value = str(df.at[i, col])
                            if cell_value not in ["0", "1"]:
                                cell_value = ""
                            new_row.append(DataCell(ft.Container(content=TextField(value=cell_value, on_change=on_textfield_change), bgcolor="#181c21")))
                        manual_table.rows.append(DataRow(new_row))

                    item_names.clear()
                    item_names.extend(df.columns)

                    checkboxes.clear()
                    for col in df.columns:
                        checkbox = Checkbox(label=col, value=False, on_change=on_checkbox_change)
                        checkboxes.append(checkbox)

                    filled_checkboxes.controls = checkboxes

                    # Deshabilitar botones de cálculo al cargar nuevo archivo
                    calculate_button.disabled = True

                    # Habilitar los botones si hay al menos 2 ítems
                    add_record_button.disabled = len(manual_table.columns) - 1 < 2
                    fill_random_button.disabled = len(manual_table.rows) == 0

                else:
                    manual_table.columns = [DataColumn(ft.Text("Eliminar")), DataColumn(ft.Text("Tabla vacía"))]
                    manual_table.rows = []
                    filled_checkboxes.controls = []

            except Exception as ex:
                manual_table.columns = [DataColumn(ft.Text("Eliminar")), DataColumn(ft.Text("Tabla vacía"))]
                manual_table.rows = []
                filled_checkboxes.controls = []

            page.update()

    def on_checkbox_change(e):
        selected = [cb for cb in checkboxes if cb.value]
        calculate_button.disabled = len(selected) != 2
        page.update()

    def check_table_filled():
        for row in manual_table.rows:
            for cell in row.cells[1:]:  # Ignorar el primer cell que es el botón de eliminar
                if isinstance(cell.content.content, TextField) and cell.content.content.value == "":
                    return False
        return True

    def on_textfield_change(e):
        # Validar que los valores sean solo 0 o 1
        if e.control.value not in ["0", "1"]:
            e.control.value = ""
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
                filled_checkboxes.controls.append(Checkbox(label=item, value=False, on_change=on_checkbox_change, disabled=not item_filled or len(manual_table.rows) == 0))
        page.update()

    def calculate_metrics(e):
        # Lógica para calcular Cobertura y Confianza
        selected_items = [cb.label for cb in checkboxes if cb.value]
        if len(selected_items) == 2:
            item1, item2 = selected_items
            # Calcular Cobertura y Confianza
            coverage, confidence = calculate_coverage_confidence(item1, item2)
            coverage_text.value = f"Cobertura: {coverage * 100:.2f}%"
            confidence_text.value = f"Confianza: {confidence * 100:.2f}%"
            generate_contingency_table(item1, item2)
            generate_dependency_table(item1, item2)
            chi_square_value, significance = calculate_chi_square(item1, item2)
            chi_square_text.value = f"Chi-Cuadrado: {chi_square_value:.2f}"
            significance_text.value = f"Significancia de la dependencia: {significance}"
            show_results_popup()
            page.update()

    def calculate_coverage_confidence(item1, item2):
        item1_index = item_names.index(item1) + 1
        item2_index = item_names.index(item2) + 1
        total_records = len(manual_table.rows)
        item1_count = sum(1 for row in manual_table.rows if row.cells[item1_index].content.content.value == "1")
        item2_count = sum(1 for row in manual_table.rows if row.cells[item2_index].content.content.value == "1")
        both_count = sum(1 for row in manual_table.rows if
                         row.cells[item1_index].content.content.value == "1" and row.cells[
                             item2_index].content.content.value == "1")

        coverage = both_count / total_records if total_records > 0 else 0
        confidence = both_count / item1_count if item1_count > 0 else 0

        return coverage, confidence

    def generate_contingency_table(item1, item2):
        item1_index = item_names.index(item1) + 1
        item2_index = item_names.index(item2) + 1

        # Calcular la tabla de contingencia
        contingency_data = [[0, 0], [0, 0]]
        for row in manual_table.rows:
            item1_val = row.cells[item1_index].content.content.value
            item2_val = row.cells[item2_index].content.content.value
            if item1_val == "1" and item2_val == "1":
                contingency_data[0][0] += 1
            elif item1_val == "1" and item2_val == "0":
                contingency_data[0][1] += 1
            elif item1_val == "0" and item2_val == "1":
                contingency_data[1][0] += 1
            elif item1_val == "0" and item2_val == "0":
                contingency_data[1][1] += 1

        total_records = len(manual_table.rows)
        total_item1_1 = sum(contingency_data[0])
        total_item1_0 = sum(contingency_data[1])
        total_item2_1 = contingency_data[0][0] + contingency_data[1][0]
        total_item2_0 = contingency_data[0][1] + contingency_data[1][1]

        contingency_table.columns = [
            DataColumn(ft.Text("Contingencia")),
            DataColumn(ft.Text(item2)),
            DataColumn(ft.Text(f"No {item2}")),
            DataColumn(ft.Text("Total"))
        ]
        contingency_table.rows = [
            DataRow([DataCell(ft.Text(item1)), DataCell(ft.Text(str(contingency_data[0][0]))),
                     DataCell(ft.Text(str(contingency_data[0][1]))), DataCell(ft.Text(str(total_item1_1)))]),
            DataRow([DataCell(ft.Text(f"No {item1}")), DataCell(ft.Text(str(contingency_data[1][0]))),
                     DataCell(ft.Text(str(contingency_data[1][1]))), DataCell(ft.Text(str(total_item1_0)))]),
            DataRow([DataCell(ft.Text("Total")), DataCell(ft.Text(str(total_item2_1))),
                     DataCell(ft.Text(str(total_item2_0))), DataCell(ft.Text(str(total_records)))])
        ]

        # Calcular las reglas de asociación con sus coberturas y confianzas
        rules = [
            (f"Si {item1} = 1 entonces {item2} = 1", contingency_data[0][0], contingency_data[0][0] / total_records,
             contingency_data[0][0] / total_item1_1 if total_item1_1 != 0 else 0),
            (f"Si {item1} = 1 entonces {item2} = 0", contingency_data[0][1], contingency_data[0][1] / total_records,
             contingency_data[0][1] / total_item1_1 if total_item1_1 != 0 else 0),
            (f"Si {item1} = 0 entonces {item2} = 1", contingency_data[1][0], contingency_data[1][0] / total_records,
             contingency_data[1][0] / total_item1_0 if total_item1_0 != 0 else 0),
            (f"Si {item1} = 0 entonces {item2} = 0", contingency_data[1][1], contingency_data[1][1] / total_records,
             contingency_data[1][1] / total_item1_0 if total_item1_0 != 0 else 0),
            (f"Si {item2} = 1 entonces {item1} = 1", contingency_data[0][0], contingency_data[0][0] / total_records,
             contingency_data[0][0] / total_item2_1 if total_item2_1 != 0 else 0),
            (f"Si {item2} = 1 entonces {item1} = 0", contingency_data[1][0], contingency_data[1][0] / total_records,
             contingency_data[1][0] / total_item2_1 if total_item2_1 != 0 else 0),
            (f"Si {item2} = 0 entonces {item1} = 1", contingency_data[0][1], contingency_data[0][1] / total_records,
             contingency_data[0][1] / total_item2_0 if total_item2_0 != 0 else 0),
            (f"Si {item2} = 0 entonces {item1} = 0", contingency_data[1][1], contingency_data[1][1] / total_records,
             contingency_data[1][1] / total_item2_0 if total_item2_0 != 0 else 0)
        ]

        # Generar la tabla de resultados con las reglas ajustadas
        results_table.rows = [
            DataRow([DataCell(ft.Text(rule[0])), DataCell(ft.Text(f"{rule[2] * 100:.2f}%")),
                     DataCell(ft.Text(f"{rule[3] * 100:.2f}%"))])
            for rule in rules
        ]

        page.update()

    def generate_dependency_table(item1, item2):
        item1_index = item_names.index(item1) + 1
        item2_index = item_names.index(item2) + 1

        dependency_data = [[0, 0], [0, 0]]
        for row in manual_table.rows:
            item1_val = row.cells[item1_index].content.content.value
            item2_val = row.cells[item2_index].content.content.value
            if item1_val == "1" and item2_val == "1":
                dependency_data[0][0] += 1
            elif item1_val == "1" and item2_val == "0":
                dependency_data[0][1] += 1
            elif item1_val == "0" and item2_val == "1":
                dependency_data[1][0] += 1
            elif item1_val == "0" and item2_val == "0":
                dependency_data[1][1] += 1

        total_records = len(manual_table.rows)
        item1_count = sum(1 for row in manual_table.rows if row.cells[item1_index].content.content.value == "1")
        item2_count = sum(1 for row in manual_table.rows if row.cells[item2_index].content.content.value == "1")

        factor_dep_11 = calculate_factor_dependency(item1_count, item2_count, dependency_data[0][0], total_records)
        factor_dep_10 = calculate_factor_dependency(item1_count, total_records - item2_count, dependency_data[0][1],
                                                    total_records)
        factor_dep_01 = calculate_factor_dependency(total_records - item1_count, item2_count, dependency_data[1][0],
                                                    total_records)
        factor_dep_00 = calculate_factor_dependency(total_records - item1_count, total_records - item2_count,
                                                    dependency_data[1][1], total_records)

        dependency_table.columns = [
            DataColumn(ft.Text("Dependencia")),
            DataColumn(ft.Text(item2)),
            DataColumn(ft.Text(f"No {item2}"))
        ]
        dependency_table.rows = [
            DataRow([DataCell(ft.Text(f"{item1}")), DataCell(ft.Text(f"{factor_dep_11:.3f}")),
                     DataCell(ft.Text(f"{factor_dep_10:.3f}"))]),
            DataRow([DataCell(ft.Text(f"No {item1}")), DataCell(ft.Text(f"{factor_dep_01:.3f}")),
                     DataCell(ft.Text(f"{factor_dep_00:.3f}"))])
        ]

        page.update()

    def calculate_factor_dependency(item1_count, item2_count, both_count, total_records):
        if total_records > 0 and item1_count > 0 and item2_count > 0:
            factor_dependency = (both_count / total_records) / (
                    (item1_count / total_records) * (item2_count / total_records))
        else:
            factor_dependency = 0
        return factor_dependency

    def calculate_chi_square(item1, item2):
        item1_index = item_names.index(item1) + 1
        item2_index = item_names.index(item2) + 1

        observed = [[0, 0], [0, 0]]
        for row in manual_table.rows:
            item1_val = row.cells[item1_index].content.content.value
            item2_val = row.cells[item2_index].content.content.value
            if item1_val == "1" and item2_val == "1":
                observed[0][0] += 1
            elif item1_val == "1" and item2_val == "0":
                observed[0][1] += 1
            elif item1_val == "0" and item2_val == "1":
                observed[1][0] += 1
            elif item1_val == "0" and item2_val == "0":
                observed[1][1] += 1

        total_records = len(manual_table.rows)
        expected = [[0, 0], [0, 0]]
        row_totals = [sum(row) for row in observed]
        col_totals = [sum(col) for col in zip(*observed)]
        for i in range(2):
            for j in range(2):
                expected[i][j] = (row_totals[i] * col_totals[j]) / total_records if total_records > 0 else 0

        chi_square = sum(
            ((observed[i][j] - expected[i][j]) ** 2) / expected[i][j] for i in range(2) for j in range(2) if
            expected[i][j] != 0)

        significance_levels = {0.95: chi2.ppf(0.95, 1), 0.99: chi2.ppf(0.99, 1), 0.9999: chi2.ppf(0.9999, 1)}
        significance = "No significativo"
        for level, critical_value in significance_levels.items():
            if chi_square > critical_value:
                significance = f"Significativo al nivel {int(level * 100)}%"

        return chi_square, significance

    def show_results_popup():
        results_popup.open = True
        page.update()

    add_record_button = ElevatedButton("Agregar Cesta", on_click=add_record, disabled=True)
    fill_random_button = ElevatedButton("Llenado Aleatorio", on_click=fill_random, disabled=True)
    calculate_button = ElevatedButton("Realizar cálculos", on_click=calculate_metrics, disabled=True)
    coverage_text = ft.Text(value="Cobertura: N/A", size=16)
    confidence_text = ft.Text(value="Confianza: N/A", size=16)
    chi_square_text = ft.Text(value="Chi-Cuadrado: N/A", size=16)
    significance_text = ft.Text(value="Significancia: N/A", size=16)

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    pick_file_button = ElevatedButton("Seleccionar archivo", on_click=lambda _: file_picker.pick_files())

    item_name_field = TextField(label="Ingrese el item", width=200)
    add_item_button = ElevatedButton("Agregar Item", on_click=add_item)

    main_section = Column([
        ft.Text("Reglas de Asociación", size=24),
        Row([file_path, pick_file_button]),
        Row([item_name_field, add_item_button]),
        Row([add_record_button, fill_random_button]),
        Row([
            Column([filled_checkboxes], expand=False),
            Column([manual_table], expand=True, scroll="always"),
        ], expand=True, vertical_alignment="start"),
        Row([calculate_button])
    ], expand=True)

    results_popup = ft.AlertDialog(
        title=ft.Text("Resultados"),
        content=Column([
            coverage_text,
            confidence_text,
            chi_square_text,
            significance_text,
            ft.Text("Tabla de Contingencia", size=20),
            contingency_table,
            ft.Text("Factores de Dependencia", size=20),
            dependency_table,
            ft.Text("Cobertura y Confianza de las Reglas", size=20),
            results_table
        ], scroll="always"),
        on_dismiss=lambda e: print("Dialog dismissed!")
    )

    page.overlay.append(results_popup)
    page.add(main_section)

ft.app(target=main)
