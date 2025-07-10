#!/bin/python
# 2025 (C) Alfa Development Group
# Developed by SistemaRayoXP
import sys
import argparse

try:
    from PySide6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLineEdit,
        QLabel,
        QPushButton,
        QListWidget,
        QListWidgetItem,
        QAbstractItemView,
        QMessageBox,
    )
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt
except ImportError:
    Qt = None

from PIL import Image, ImageDraw, ImageFont

DEFAULT_HEIGHT = 1080
DEFAULT_OUTPUT_FILENAME = "Screenshot.png"
DEFAULT_BULLET = "•"
DEFAULT_DESCRIPTION = "Estos son los cambios para esta versión:"
DEFAULT_TITLE = "Cambios de la versión"
DEFAULT_TITLE_WITH_VERSION = "Cambios de la versión %s"
DEFAULT_TOP_COLOR = (158, 130, 10)
DEFAULT_BOTTOM_COLOR = (43, 43, 34)
DEFAULT_TEXT_COLOR = (255, 255, 255)


class ImageMaker:
    topbox_height = 70
    margin_left = 40
    bottombox_margin_x = round(margin_left * 1.5)
    bottombox_margin_y = topbox_height

    def __init__(self, resolucion_y: int = 720):
        self.resolucion_y = resolucion_y
        self.factor = self.resolucion_y / 720
        self.topbox_height = round(70 * self.factor)
        self.margin_left = round(40 * self.factor)
        self.bottombox_margin_x = round(self.margin_left * 1.5)
        self.bottombox_margin_y = self.topbox_height

    def create_tag_image(
        self,
        tags: list,
        tag_bullet: str = "•",
        title: str = "Cambios de la versión",
        description: str = "Estos son los cambios para esta versión:",
        top_color: tuple[int, int, int] = (158, 130, 10),
        bottom_color: tuple[int, int, int] = (43, 43, 34),
        text_color: tuple[int, int, int] = (255, 255, 255),
        output_filename: str = "Screenshot.png",
    ):
        """
        Crea una imagen 16:9 con dos cajas:
        - La superior (fondo dorado) para el título
        - La inferior (fondo gris) para los tags
        Coloca los tags en una cuadrícula y guarda la imagen.
        """
        tags.sort()
        # Dimensiones de la imagen (16:9)
        image_width, image_height = (
            round(self.resolucion_y * (16 / 9)),
            self.resolucion_y,
        )

        # Crea la imagen con fondo blanco
        img = Image.new("RGB", (image_width, image_height), "white")
        draw = ImageDraw.Draw(img)

        # Dibuja la caja superior (fondo dorado)
        draw.rectangle([(0, 0), (image_width, self.topbox_height)], fill=top_color)

        # Dibuja la caja inferior (fondo gris)
        draw.rectangle(
            [(0, self.topbox_height), (image_width, image_height)], fill=bottom_color
        )

        # Fuentes para el texto
        try:
            title_font = ImageFont.truetype(
                "NotoSans-SemiBold.ttf", round(35 * self.factor)
            )
        except IOError:
            try:
                title_font = ImageFont.truetype("arial.ttf", round(35 * self.factor))
            except IOError:
                title_font = ImageFont.load_default()

        try:
            body_font = ImageFont.truetype("arial.ttf", round(35 * self.factor))
        except IOError:
            body_font = ImageFont.load_default()

        try:
            body_font_bold = ImageFont.truetype("arialbd.ttf", round(35 * self.factor))
        except IOError:
            body_font_bold = ImageFont.load_default()

        # Dibuja el título en la caja superior
        bbox_title = draw.textbbox((0, 0), title, font=title_font)
        title_h = bbox_title[3] - bbox_title[1]
        title_x = self.margin_left
        title_y = (self.topbox_height // 2) - (title_h)
        draw.text((title_x, title_y), title, fill=text_color, font=title_font)

        # Dibuja la descripción en la caja inferior
        bbox_desc = draw.textbbox((0, 0), description, font=body_font_bold)
        desc_h = bbox_desc[3] - bbox_desc[1]
        desc_x = self.bottombox_margin_x
        desc_y = self.topbox_height + self.bottombox_margin_y
        draw.text((desc_x, desc_y), description, fill=text_color, font=body_font_bold)

        # Calcula la cantidad de columnas según el largo máximo de los tags
        max_len = max(len(tag) for tag in tags) if tags else 0
        columns = 3 if max_len > 15 else 2

        # Configuración para posicionar los tags en la caja gris
        row_spacing = round(40 * self.factor)  # separación vertical entre filas
        col_spacing = (image_width - self.bottombox_margin_x) // (
            3 if columns == 3 else 2
        )
        margin_top = (
            self.topbox_height
            + self.bottombox_margin_y
            + desc_h
            + round(5 * self.factor)
        )

        # Dibuja cada tag
        for i, tag in enumerate(tags):
            text = f"{tag_bullet} {tag}"
            row = i // columns
            col = i % columns

            # bbox_tag = draw.textbbox((0, 0), text, font=body_font)
            x_pos = self.bottombox_margin_x + col * col_spacing
            y_pos = margin_top + row * row_spacing

            draw.text((x_pos, y_pos), text, fill=text_color, font=body_font)

        # Guarda la imagen
        img.save(output_filename)
        return True

    def create_changelog(
        self,
        tags: list,
        tag_bullet: str,
        description: str,
        output_filename: str = "changelog.txt",
    ):
        output = f"""
        [B]{description}[/B]
        
        {"\n        ".join(f"{tag_bullet} {x}" for x in tags)}
        """

        with open(output_filename, "w") as f:
            f.write(output)


if Qt:

    class QListWidgetWithDelete(QListWidget):
        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Delete:
                # Action to perform when Delete is pressed
                selected_items = self.selectedItems()
                if not selected_items:
                    return
                for item in selected_items:
                    self.takeItem(self.row(item))
            else:
                # Call the base class implementation for other keys.
                super().keyPressEvent(event)

    class MyApp(QWidget):
        def __init__(self):
            super().__init__()
            self.image_maker = ImageMaker()
            self.init_ui()

        @staticmethod
        def create_dark_palette():
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            return palette

        def init_ui(self):
            # Layout principal
            main_layout = QVBoxLayout()

            # Sección para agregar tags
            self.help_input_label = QLabel("Nombre del canal con cambio:", self)
            main_layout.addWidget(self.help_input_label)

            # Sección para agregar tags
            self.tag_input = QLineEdit(self)
            self.tag_input.setPlaceholderText("Ingresa una etiqueta")
            self.tag_input.returnPressed.connect(self.add_tag)
            main_layout.addWidget(self.tag_input)

            # Lista editable de tags
            self.tag_list_widget = QListWidgetWithDelete(self)
            self.tag_list_widget.setEditTriggers(
                QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
            )
            main_layout.addWidget(self.tag_list_widget)

            # Botón para eliminar tag(s) seleccionados
            self.remove_tag_button = QPushButton("Eliminar etiqueta seleccionada", self)
            self.remove_tag_button.clicked.connect(self.remove_tag)
            main_layout.addWidget(self.remove_tag_button)

            # QLineEdit para editar el título
            main_layout.addWidget(QLabel("Título:", self))
            self.title_line = QLineEdit(self)
            self.title_line.setText("Cambios de la versión 3.10.")
            self.title_line.setPlaceholderText(f"{DEFAULT_TITLE}")
            main_layout.addWidget(self.title_line)

            # QLineEdit para editar la descripción
            main_layout.addWidget(QLabel("Descripción:", self))
            self.description_line = QLineEdit(self)
            self.description_line.setText(f"{DEFAULT_DESCRIPTION}")
            main_layout.addWidget(self.description_line)

            # QLineEdit para editar la viñeta y la resolución
            self.options_layout = QHBoxLayout()
            self.bullet_layout = QVBoxLayout()
            self.resolution_layout = QVBoxLayout()

            self.bullet_label = QLabel("Viñeta")
            self.bullet_line = QLineEdit(self)
            self.bullet_line.setText(f"{DEFAULT_BULLET}")
            self.bullet_line.setPlaceholderText(f"{DEFAULT_BULLET}")
            self.bullet_layout.addWidget(self.bullet_label)
            self.bullet_layout.addWidget(self.bullet_line)

            self.resolution_label = QLabel("Resolución de la imagen")
            self.resolution_line = QLineEdit(self)
            self.resolution_line.setText(f"{DEFAULT_HEIGHT}")
            self.resolution_line.setPlaceholderText(f"{DEFAULT_HEIGHT}")
            self.resolution_layout.addWidget(self.resolution_label)
            self.resolution_layout.addWidget(self.resolution_line)

            self.options_layout.addLayout(self.bullet_layout)
            self.options_layout.addLayout(self.resolution_layout)
            main_layout.addLayout(self.options_layout)

            # QLineEdit para editar el nombre del archivo de salida
            main_layout.addWidget(QLabel("Nombre de archivo de salida:", self))
            self.output_line = QLineEdit(self)
            self.output_line.setText(f"{DEFAULT_OUTPUT_FILENAME}")
            self.output_line.setPlaceholderText(f"{DEFAULT_OUTPUT_FILENAME}")
            main_layout.addWidget(self.output_line)

            # Botón para generar la imagen
            self.generate_button = QPushButton("Generar imagen", self)
            self.generate_button.clicked.connect(self.generate_image)
            main_layout.addWidget(self.generate_button)

            # Configuración de la ventana
            self.setLayout(main_layout)
            self.setWindowTitle("Generador de registros de cambios")
            self.resize(400, 600)

        def add_tag(self):
            """Agrega el texto del QLineEdit a la lista de tags."""
            text = self.tag_input.text().strip()
            if text:
                item = QListWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                # self.tag_list_widget.addItem(text)
                self.tag_list_widget.addItem(item)
                self.tag_input.clear()

        def remove_tag(self):
            """Elimina los elementos seleccionados en el QListWidget."""
            selected_items = self.tag_list_widget.selectedItems()
            if not selected_items:
                return
            for item in selected_items:
                self.tag_list_widget.takeItem(self.tag_list_widget.row(item))

        def generate_image(self):
            """Lee todos los parámetros, invoca la función para generar la imagen y muestra un mensaje de confirmación."""
            # Obtiene todos los tags de la lista
            tags = [
                self.tag_list_widget.item(i).text()
                for i in range(self.tag_list_widget.count())
            ]

            # Obtiene los parámetros de cada QLineEdit (o usa el valor por defecto si el campo está vacío)
            title = self.title_line.text().strip()
            description = self.description_line.text().strip()
            bullet = self.bullet_line.text().strip() or "•"
            output_filename = self.output_line.text().strip() or "output.png"
            resolution = self.resolution_line.text().strip()

            try:
                resolution = int(resolution)
            except ValueError:
                resolution = 720

            # Llama a la función para generar la imagen
            ImageMaker(resolution).create_tag_image(
                tags, bullet, title, description, output_filename=output_filename
            )
            QMessageBox.information(
                self,
                "Guardado correcto",
                f"Imagen generada y guardada como {output_filename}",
                QMessageBox.StandardButton.Ok,
            )


def parse_color(color_str):
    """Convert a comma-separated color string 'R,G,B' into a tuple of three ints."""
    try:
        parts = color_str.split(",")
        if len(parts) != 3:
            raise ValueError("Color must have exactly three components (R,G,B).")
        return tuple(int(x) for x in parts)
    except Exception as e:
        raise argparse.ArgumentTypeError(
            f"Invalid color format '{color_str}'. Expected format: R,G,B"
        ) from e


def get_arg_parser():
    parser = argparse.ArgumentParser(
        description="Create a tag image with specified parameters."
    )

    # Mandatory positional argument for tags (list)
    parser.add_argument(
        "tags", nargs="*", help="A list of tags to be used in the image."
    )

    # Optional arguments with defaults
    parser.add_argument(
        "-b",
        "--tag_bullet",
        default=DEFAULT_BULLET,
        help="Bullet character to prepend to each tag (default: '•').",
    )
    parser.add_argument(
        "-t",
        "--title",
        default=DEFAULT_TITLE,
        help="Title of the tag image (default: 'Cambios de la versión').",
    )
    parser.add_argument(
        "-v", "--version", help="Version for the title (default: None)."
    )
    parser.add_argument(
        "-d",
        "--description",
        default=DEFAULT_DESCRIPTION,
        help="Description for the tag image (default: 'Estos son los cambios para esta versión:').",
    )
    parser.add_argument(
        "--top_color",
        type=parse_color,
        default=DEFAULT_TOP_COLOR,
        help="Top color in R,G,B format (default: '158,130,10').",
    )
    parser.add_argument(
        "--bottom_color",
        type=parse_color,
        default=DEFAULT_BOTTOM_COLOR,
        help="Bottom color in R,G,B format (default: '43,43,34').",
    )
    parser.add_argument(
        "--text_color",
        type=parse_color,
        default=DEFAULT_TEXT_COLOR,
        help="Text color in R,G,B format (default: '255,255,255').",
    )
    parser.add_argument(
        "-o",
        "--output_filename",
        default="Screenshot.png",
        help="Output filename (default: 'Screenshot.png').",
    )
    parser.add_argument(
        "-l",
        "--generate_changelog",
        default="changelog.txt",
        help="Output changelog filename. Does not generate one if omitted.",
    )

    # Additional flag for CLI mode
    parser.add_argument(
        "-c",
        "--cli",
        action="store_true",
        default=True,
        help="Run the application in CLI mode.",
    )

    # New resolution argument: expects the desired height.
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        default=DEFAULT_HEIGHT,
        help="Desired height of the image. The width will be calculated with a fixed 16:9 ratio.",
    )

    return parser


def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    if args.cli:
        title = (
            DEFAULT_TITLE_WITH_VERSION % args.version if args.version else DEFAULT_TITLE
        )

        if not args.tags:
            parser.error("In CLI mode (-c/--cli), at least one tag is required.")

        maker = ImageMaker(args.resolution)

        maker.create_tag_image(
            tags=args.tags,
            tag_bullet=args.tag_bullet,
            title=title,
            description=args.description,
            top_color=args.top_color,
            bottom_color=args.bottom_color,
            text_color=args.text_color,
            output_filename=args.output_filename,
        )

        if args.generate_changelog:
            maker.create_changelog(
                tags=args.tags,
                tag_bullet=args.tag_bullet,
                description=args.description,
                output_filename=args.generate_changelog,
            )
    elif Qt:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")  # Ensures consistency across platforms
        app.setPalette(MyApp.create_dark_palette())
        window = MyApp()
        window.show()
        sys.exit(app.exec())
    else:
        parser.error(
            "The GUI (Qt/PySide6) couldn't be loaded. Use the --help command to use the --cli mode."
        )


if __name__ == "__main__":
    main()
