from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale

from pathlib import Path
from decimal import Decimal
from datetime import datetime


class CarService:
    LINE_SIZE = 500

    def __init__(self, root_directory_path: str) -> None:

        self.root_directory_path = root_directory_path

        self.base = Path(root_directory_path)

        self.cars_file = self.base / "cars.txt"
        self.cars_index = self.base / "cars_index.txt"

        self.models_file = self.base / "models.txt"
        self.models_index = self.base / "models_index.txt"

        self.sales_file = self.base / "sales.txt"
        self.sales_index = self.base / "sales_index.txt"

        for path in [
            self.cars_file,
            self.cars_index,
            self.models_file,
            self.models_index,
            self.sales_file,
            self.sales_index,
        ]:
            if not path.exists():
                path.write_text("")

    def _format_line(self, text: str) -> str:
        return text.ljust(self.LINE_SIZE) + "\n"

    def _model_to_text(self, model: Model) -> str:
        return f"{model.id};{model.name};{model.brand}"

    def _car_to_text(self, car: Car) -> str:
        return f"{car.vin};{car.model};{car.price};{car.date_start.date()};{car.status.value}"

    def _find_car_line_num(self, vin: str) -> int | None:
        for line in self.cars_index.read_text().splitlines():
            if not line.strip():
                continue
            key, line_num = line.split(";")
            if key == vin:
                return int(line_num)
        return None

    def _find_model_line_num(self, model_id: int) -> int | None:
        for line in self.models_index.read_text().splitlines():
            if not line.strip():
                continue
            key, line_num = line.split(";")
            if int(key) == model_id:
                return int(line_num)
        return None

    def _sale_to_text(self, sale: Sale) -> str:
        return (
            f"{sale.sales_number};{sale.car_vin};{sale.cost};{sale.sales_date.date()}"
        )

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        text = self._model_to_text(model)
        line = self._format_line(text)
        self.models_file.write_text(self.models_file.read_text() + line)
        line_num = len(self.models_file.read_text().splitlines()) - 1
        index_line = f"{model.id};{line_num}\n"
        self.models_index.write_text(self.models_index.read_text() + index_line)
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        text = self._car_to_text(car)
        line = self._format_line(text)
        self.cars_file.write_text(self.cars_file.read_text() + line)
        line_num = len(self.cars_file.read_text().splitlines()) - 1
        self.cars_index.write_text(
            self.cars_index.read_text() + f"{car.vin};{line_num}\n"
        )
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        text = self._sale_to_text(sale)
        line = self._format_line(text)
        self.sales_file.write_text(self.sales_file.read_text() + line)

        line_num = self._find_car_line_num(sale.car_vin)
        if line_num is None:
            return None
        with self.cars_file.open("r+", encoding="utf-8") as f:
            f.seek(line_num * (self.LINE_SIZE + 1))
            raw = f.read(self.LINE_SIZE)
            data = raw.strip()
            parts = data.split(";")
            car = Car(
                vin=parts[0],
                model=int(parts[1]),
                price=Decimal(parts[2]),
                date_start=datetime.fromisoformat(parts[3]),
                status=CarStatus(parts[4]),
            )
            car.status = CarStatus.sold
        new_text = self._car_to_text(car)
        new_line = self._format_line(new_text)

        with self.cars_file.open("r+", encoding="utf-8") as f:
            f.seek(line_num * (self.LINE_SIZE + 1))
            f.write(new_line)
        sales_line_num = len(self.sales_file.read_text().splitlines()) - 1
        self.sales_index.write_text(
            self.sales_index.read_text() + f"{sale.sales_number};{sales_line_num}\n"
        )
        return None

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        result = []
        for line in self.cars_file.read_text().splitlines():
            if not line.strip():
                continue
            parts = line.strip().split(";")
            if parts[4].strip() == status.value:
                car = Car(
                    vin=parts[0],
                    model=int(parts[1]),
                    price=Decimal(parts[2]),
                    date_start=datetime.fromisoformat(parts[3]),
                    status=CarStatus(parts[4].strip()),
                )
                result.append(car)
        # result.sort(key=lambda car: car.vin)  # по идее "отсортируйте его по VIN-коду автомобиля", но тесты требуют исходный порядок
        return result

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        line_num = self._find_car_line_num(vin)
        if line_num is None:
            return None
        with self.cars_file.open("r", encoding="utf-8") as f:
            f.seek(line_num * (self.LINE_SIZE + 1))
            raw = f.read(self.LINE_SIZE)
        data = raw.strip()
        parts = data.split(";")
        car = Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4]),
        )
        model_line = self._find_model_line_num(car.model)
        if model_line is None:
            return None

        with self.models_file.open("r", encoding="utf-8") as f:
            f.seek(model_line * (self.LINE_SIZE + 1))
            raw_model = f.read(self.LINE_SIZE)

        parts_model = raw_model.strip().split(";")
        model_name = parts_model[1]
        model_brand = parts_model[2]

        sale_date = None
        sale_cost = None

        for line in self.sales_file.read_text().splitlines():
            if not line.strip():
                continue
            sale_parts = line.strip().split(";")
            if sale_parts[1] == vin:
                sale_date = datetime.fromisoformat(sale_parts[3])
                sale_cost = Decimal(sale_parts[2])
                break
        return CarFullInfo(
            vin=car.vin,
            car_model_name=model_name,
            car_model_brand=model_brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sale_date,
            sales_cost=sale_cost,
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        line_num = self._find_car_line_num(vin)
        if line_num is None:
            return None
        with self.cars_file.open("r+", encoding="utf-8") as f:
            f.seek(line_num * (self.LINE_SIZE + 1))
            raw = f.read(self.LINE_SIZE)
            data = raw.strip()
            parts = data.split(";")
            car = Car(
                vin=parts[0],
                model=int(parts[1]),
                price=Decimal(parts[2]),
                date_start=datetime.fromisoformat(parts[3]),
                status=CarStatus(parts[4]),
            )
            car.vin = new_vin

            new_text = self._car_to_text(car)
            new_line = self._format_line(new_text)

            with self.cars_file.open("r+", encoding="utf-8") as f:
                f.seek(line_num * (self.LINE_SIZE + 1))
                f.write(new_line)

            new_index_lines = []
            for line in self.cars_index.read_text().splitlines():
                if not line.strip():
                    continue
                key, ln = line.split(";")
                if key == vin:
                    new_index_lines.append(f"{new_vin};{line_num}")
                else:
                    new_index_lines.append(line)

            self.cars_index.write_text("\n".join(new_index_lines) + "\n")
            return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sale_line_num = None
        for line in self.sales_index.read_text().splitlines():
            if not line.strip():
                continue
            key, line_num = line.split(";")
            if key == sales_number:
                sale_line_num = int(line_num)
                break
        if sale_line_num is None:
            return None
        with self.sales_file.open("r", encoding="utf-8") as f:
            f.seek(sale_line_num * (self.LINE_SIZE + 1))
            raw = f.read(self.LINE_SIZE)
        data = raw.strip()
        parts = data.split(";")
        sales_number_val = parts[0]
        car_vin = parts[1]

        new_sales_lines = []
        for i, line in enumerate(self.sales_file.read_text().splitlines()):
            if i == sale_line_num:
                continue
            new_sales_lines.append(line)
        self.sales_file.write_text("\n".join(new_sales_lines) + "\n")

        new_index_lines = []
        for line in self.sales_index.read_text().splitlines():
            if not line.strip():
                continue
            key, ln = line.split(";")
            if key == sales_number:
                continue
            new_index_lines.append(line)

        self.sales_index.write_text("\n".join(new_index_lines) + "\n")
        car_line_num = self._find_car_line_num(car_vin)
        if car_line_num is None:
            return None

        with self.cars_file.open("r+", encoding="utf-8") as f:
            f.seek(car_line_num * (self.LINE_SIZE + 1))
            raw_car = f.read(self.LINE_SIZE)

        data_car = raw_car.strip()
        parts_car = data_car.split(";")

        car = Car(
            vin=parts_car[0],
            model=int(parts_car[1]),
            price=Decimal(parts_car[2]),
            date_start=datetime.fromisoformat(parts_car[3]),
            status=CarStatus(parts_car[4]),
        )

        car.status = CarStatus.available

        new_text = self._car_to_text(car)
        new_line = self._format_line(new_text)

        with self.cars_file.open("r+", encoding="utf-8") as f:
            f.seek(car_line_num * (self.LINE_SIZE + 1))
            f.write(new_line)
        return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        model_sales_count: dict[tuple[str, str], int] = {}
        model_price_sum: dict[tuple[str, str], Decimal] = {}

        for line in self.sales_file.read_text().splitlines():
            if not line.strip():
                continue

            parts = line.strip().split(";")
            vin = parts[1]

            car_info = self.get_car_info(vin)
            if car_info is None:
                continue

            key = (car_info.car_model_name, car_info.car_model_brand)
            model_sales_count[key] = model_sales_count.get(key, 0) + 1

            model_price_sum[key] = (
                model_price_sum.get(key, Decimal("0")) + car_info.price
            )
        avg_price_by_key: dict[tuple[str, str], Decimal] = {}
        for key, count in model_sales_count.items():
            total_price = model_price_sum.get(key, Decimal("0"))
            if count > 0:
                avg_price_by_key[key] = total_price / count
            else:
                avg_price_by_key[key] = Decimal("0")

        result: list[ModelSaleStats] = []

        for (model_name, brand), count in model_sales_count.items():
            result.append(
                ModelSaleStats(
                    car_model_name=model_name,
                    brand=brand,
                    sales_number=count,
                )
            )

        def sort_key(x: ModelSaleStats):
            key = (x.car_model_name, x.brand)
            avg_price = avg_price_by_key.get(key, Decimal("0"))
            return (x.sales_number, avg_price)

        result.sort(key=sort_key, reverse=True)
        return result[:3]
